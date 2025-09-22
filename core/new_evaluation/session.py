from __future__ import annotations
from typing import Callable, Dict, List, Optional
from .data_models import (
    ActionConfig, KeyframeSet, EvaluationState, StageResult, MetricValue,
    TrainingBundle, StageConfig, MetricConfig, FrameRef
)
from .pose_provider import PoseProvider

# Placeholder imports for existing engines (to be adapted)
try:
    from core.metrics_engine import MetricsEngine  # type: ignore
except Exception:  # pragma: no cover
    MetricsEngine = None  # type: ignore

try:
    from core.comparison_engine import ComparisonEngine  # type: ignore
except Exception:  # pragma: no cover
    ComparisonEngine = None  # type: ignore

class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Callable]] = {}

    def on(self, event: str, cb: Callable):
        self._subs.setdefault(event, []).append(cb)

    def emit(self, event: str, *args, **kwargs):
        for cb in self._subs.get(event, []):
            try:
                cb(*args, **kwargs)
            except Exception:
                pass

class EvaluationSession:
    """Facade orchestrating incremental evaluation lifecycle."""
    def __init__(self, config: ActionConfig, keyframes: KeyframeSet,
                 user_video: str, standard_video: Optional[str] = None):
        self.config = config
        self.keyframes = keyframes
        self.user_video = user_video
        self.standard_video = standard_video or ''
        self.state = EvaluationState(action=config.action, sport=config.sport)
        self.bus = EventBus()
        # mark all stages dirty initially
        for s in config.stages:
            self.state.mark_dirty(s.key)
        # Engines / services (lazy)
        self._metrics_engine = None  # type: ignore
        self._comparison_engine = None
        self._pose_provider = None
        self._engine_stage_config_map = {}  # map our stage_key -> engine StageConfig name

    # Subscription API --------------------------------------------------
    def on(self, event: str, cb: Callable):
        self.bus.on(event, cb)

    # Public control ----------------------------------------------------
    def evaluate(self, stage_key: Optional[str] = None):
        if stage_key:
            targets = [stage_key] if stage_key in self.state.dirty else []
        else:
            # preserve config order
            targets = [s.key for s in self.config.stages if s.key in self.state.dirty]
        for sk in targets:
            if sk not in self.state.dirty:
                continue
            cfg = self.config.stage_map.get(sk)
            if not cfg:
                continue
            result = self._evaluate_stage(cfg)
            self.state.stages[sk] = result
            self.state.clear_dirty(sk)
            self.bus.emit('stage_completed', result)
        if not self.state.dirty:
            self.state.overall_score = self._aggregate_overall()
            self.state.training = self._generate_training()
            self.bus.emit('action_completed', self.state)

    def update_user_keyframe(self, stage_key: str, frame_index: int):
        self.keyframes.update_user(stage_key, frame_index=frame_index)
        self.state.mark_dirty(stage_key)
        self.bus.emit('keyframe_updated', stage_key, frame_index)

    def update_standard_keyframe(self, stage_key: str, frame_index: int):
        self.keyframes.update_standard(stage_key, frame_index=frame_index)
        self.state.mark_dirty(stage_key)
        self.bus.emit('keyframe_updated', stage_key, frame_index)

    # Internal evaluation -----------------------------------------------
    def _evaluate_stage(self, cfg: StageConfig) -> StageResult:
        # If real metrics engine configuration not supplied, fallback to placeholder metric definitions
        if not self._metrics_engine:
            self._metrics_engine = MetricsEngine() if MetricsEngine else None
        if not self._pose_provider:
            self._pose_provider = PoseProvider()

        metrics: List[MetricValue] = []

        # Attempt to map to experimental engine config if available
        stage_engine_result_user = None
        stage_engine_result_std = None
        try:
            from core.experimental.config.sport_configs import SportConfigs  # type: ignore
            # Acquire pose for this stage (user keyframe only for now)
            user_fr: FrameRef | None = self.keyframes.user.get(cfg.key)
            std_fr: FrameRef | None = self.keyframes.standard.get(cfg.key)
            pose_user = pose_std = None
            if user_fr and self._pose_provider and self._metrics_engine:
                pose_user = self._pose_provider.extract(user_fr.video_path, user_fr.frame_index)
            if std_fr and self._pose_provider and self._metrics_engine:
                pose_std = self._pose_provider.extract(std_fr.video_path, std_fr.frame_index)
                # Build engine action config lazily once (cache stage name mapping)
                if not self._engine_stage_config_map:
                    act_cfg = SportConfigs.get_config(self.config.sport, self.config.action)
                    for st in act_cfg.stages:
                        # heuristic: map by prefix or contains
                        # our cfg.key expected like 'setup' vs engine 'setup_stage'
                        base = st.name.replace('_stage','')
                        self._engine_stage_config_map[base] = st
                        self._engine_stage_config_map[st.name] = st
                    self._engine_action_cfg = act_cfg
                eng_stage = None
                # direct key or suffixed
                if cfg.key in self._engine_stage_config_map:
                    eng_stage = self._engine_stage_config_map[cfg.key]
                elif f"{cfg.key}_stage" in self._engine_stage_config_map:
                    eng_stage = self._engine_stage_config_map[f"{cfg.key}_stage"]
                if eng_stage:
                    if pose_user is not None:
                        stage_engine_result_user = self._metrics_engine.compute_stage(eng_stage, pose_user, frame_index=(user_fr.frame_index if user_fr else 0))
                    if pose_std is not None:
                        stage_engine_result_std = self._metrics_engine.compute_stage(eng_stage, pose_std, frame_index=(std_fr.frame_index if std_fr else 0))
        except Exception:
            stage_engine_result_user = None
            stage_engine_result_std = None

        if stage_engine_result_user:
            user_map = stage_engine_result_user.measurements
            std_map = stage_engine_result_std.measurements if stage_engine_result_std else {}
            # simple unit mapping zh->en
            unit_mapping = {
                '度': '°',
                '像素': 'px',
                '秒': 's',
                '毫秒': 'ms'
            }
            for meas_name, mv_user in user_map.items():
                mv_std = std_map.get(meas_name)
                user_val = mv_user.value if mv_user.status == 'ok' else None
                std_val = mv_std.value if mv_std and mv_std.status == 'ok' else None
                deviation = None
                status = 'na'
                if user_val is not None and std_val is not None:
                    deviation = user_val - std_val
                    # Simple tolerance-driven status using std stage rule tolerance if available
                    tolerance = None
                    try:
                        # find rule via experimental config (already loaded) for thresholding
                        rule = None
                        for st in getattr(self, '_engine_action_cfg').stages:  # type: ignore
                            if st.name == eng_stage.name:  # type: ignore
                                for r in st.measurements:
                                    if r.name == meas_name:
                                        rule = r; break
                            if rule: break
                        if rule:
                            rng = rule.tolerance_range  # (min,max)
                            if rng:
                                min_v, max_v = rng
                                if min_v <= user_val <= max_v:
                                    status = 'ok'
                                else:
                                    # Distance from nearest boundary to classify warn/bad
                                    span = max_v - min_v if max_v > min_v else 1.0
                                    dist = 0.0
                                    if user_val < min_v:
                                        dist = min_v - user_val
                                    else:
                                        dist = user_val - max_v
                                    ratio = dist / span
                                    if ratio <= 0.1:
                                        status = 'warn'
                                    else:
                                        status = 'bad'
                            else:
                                status = 'ok'
                        else:
                            status = 'ok'
                    except Exception:
                        status = 'ok'
                else:
                    # fallback to user measurement status mapping
                    if mv_user.status == 'ok':
                        status = 'ok'
                    elif mv_user.status == 'missing':
                        status = 'na'
                    else:
                        status = 'bad'
                # Determine display (English) name if available on underlying rule
                display_name = meas_name
                try:
                    if 'rule' in locals() and rule:  # type: ignore
                        disp = getattr(rule, 'display_en', None)  # type: ignore
                        if disp:
                            display_name = disp
                except Exception:
                    pass
                # map unit
                unit_disp = unit_mapping.get(mv_user.unit, mv_user.unit)
                metrics.append(MetricValue(
                    key=meas_name,
                    name=display_name,
                    unit=unit_disp,
                    user_value=user_val,
                    std_value=std_val,
                    deviation=deviation,
                    status=status
                ))
        else:
            # fallback placeholder
            for mc in cfg.metrics:
                metrics.append(self._placeholder_metric(mc))

        stage_score = self._score_stage(metrics, cfg)
        suggestion = self._build_stage_suggestion(metrics, cfg)
        return StageResult(stage_key=cfg.key, score=stage_score, metrics=metrics, suggestion=suggestion)

    def _placeholder_metric(self, mc: MetricConfig) -> MetricValue:
        user_val = None
        std_val = None
        deviation = None
        status = 'na'
        if mc.target is not None:
            user_val = mc.target * 0.95
            std_val = mc.target
            deviation = user_val - std_val
            status = 'ok'
        return MetricValue(key=mc.key, name=mc.name, unit=mc.unit,
                            user_value=user_val, std_value=std_val, deviation=deviation, status=status)

    def _score_stage(self, metrics: List[MetricValue], cfg: StageConfig) -> int:
        if not metrics:
            return 0
        ok = sum(1 for m in metrics if m.status == 'ok')
        warn = sum(1 for m in metrics if m.status == 'warn')
        base = (ok * 1.0 + warn * 0.6) / len(metrics)
        return int(base * 100)

    def _aggregate_overall(self) -> int:
        if not self.state.stages:
            return 0
        total_w = 0.0
        acc = 0.0
        for s in self.config.stages:
            r = self.state.stages.get(s.key)
            if not r:
                continue
            w = self.config.scoring.stage_weights.get(s.key, s.weight)
            total_w += w
            acc += r.score * w
        if total_w == 0:
            return 0
        return int(acc / total_w)

    def _build_stage_suggestion(self, metrics: List[MetricValue], cfg: StageConfig) -> str:
        bad_keys = [m.name for m in metrics if m.status == 'bad']
        warn_keys = [m.name for m in metrics if m.status == 'warn']
        parts = []
        if bad_keys:
            parts.append('Needs Major Improvement: ' + ', '.join(bad_keys))
        if warn_keys:
            parts.append('Can Be Optimized: ' + ', '.join(warn_keys))
        return '; '.join(parts) or ''

    def _generate_training(self) -> Optional[TrainingBundle]:
        key_issues = []
        drills = []
        next_steps = []
        for s in self.state.stages.values():
            for m in s.metrics:
                if m.status == 'bad':
                    key_issues.append(m.name)
                if m.status in ('bad','warn'):
                    drills.append(f"Repetition drill focusing on {m.name}")
        if not key_issues and not drills:
            return None
        next_steps.append('Record a new video after practice for comparison')
        return TrainingBundle(key_issues=key_issues[:5], improvement_drills=drills[:5], next_steps=next_steps)

    # Accessors ----------------------------------------------------------
    def get_state(self) -> EvaluationState:
        return self.state

__all__ = ['EvaluationSession']

from __future__ import annotations
"""Converter: experimental sport_configs.ActionConfig -> new_evaluation ActionConfig.

Allows the new EvaluationSession to use real measurement rules
defined in `core.experimental.config.sport_configs` without manual
placeholder MetricConfig objects.
"""
from typing import List, Optional

from .data_models import ActionConfig as NewActionConfig, StageConfig as NewStageConfig, MetricConfig, ScoringPolicy

try:  # runtime import; keep failures silent for environments lacking experimental config
    from core.experimental.config.sport_configs import ActionConfig as OldActionConfig, StageConfig as OldStageConfig, MeasurementRule
except Exception:  # pragma: no cover
    OldActionConfig = None  # type: ignore
    OldStageConfig = None  # type: ignore
    MeasurementRule = None  # type: ignore


def _rule_to_metric(rule: MeasurementRule) -> MetricConfig:  # type: ignore
    # Use rule.name as key (assumed unique per stage). Convert tolerance_range into
    # center target + warn/bad thresholds based on proportional deviation.
    warn_threshold = None
    bad_threshold = None
    target = None
    if getattr(rule, 'tolerance_range', None):
        min_v, max_v = rule.tolerance_range
        span = max(max_v - min_v, 1e-6)
        target = (min_v + max_v) / 2.0
        allowed_dev = span / 2.0
        warn_threshold = allowed_dev * 1.15  # >15% beyond allowed
        bad_threshold = allowed_dev * 1.30   # >30% beyond allowed
        display_en = getattr(rule, 'display_en', None)
        metric_name = display_en or rule.name
    return MetricConfig(
        key=rule.name,
        name=metric_name,
        unit=rule.unit,
        formula=rule.measurement_type,
        weight=rule.weight,
        direction='closer-better' if target is not None else 'closer-better',
        target=target,
        warn_threshold=warn_threshold,
        bad_threshold=bad_threshold,
    )


def convert(old_action: OldActionConfig) -> NewActionConfig:  # type: ignore
    new_stages: List[NewStageConfig] = []
    for old_stage in old_action.stages:
        metrics = [_rule_to_metric(r) for r in old_stage.measurements]
        skey = old_stage.name[:-6] if old_stage.name.endswith('_stage') else old_stage.name
        stage_display = getattr(old_stage, 'display_en', None) or (old_stage.description or old_stage.name)
        new_stages.append(NewStageConfig(key=skey, name=stage_display, metrics=metrics, weight=old_stage.weight))
    # 安全检查：阶段数量是否一致
    try:
        if hasattr(old_action, 'stages') and len(new_stages) != len(old_action.stages):
            print(f"[convert warning] Stage count mismatch: {len(new_stages)} vs {len(old_action.stages)}")
    except Exception:
        pass
    scoring = ScoringPolicy(stage_weights={s.key: s.weight for s in new_stages})
    action_name_display = getattr(old_action, 'display_en', None) or old_action.name
    return NewActionConfig(
        sport='羽毛球',
        action=action_name_display,
        stages=new_stages,
        scoring=scoring
    )

__all__ = ['convert']

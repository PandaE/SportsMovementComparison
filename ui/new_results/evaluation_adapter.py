"""Adapter layer for simplified view models (no refined feedback retained)."""
from __future__ import annotations
from typing import Optional
from .view_models import (
    ActionEvaluationVM, StageVM, MetricVM, TrainingVM, FrameRef, VideoInfo
)
from core.new_evaluation.utils import normalize_stage_key

def _score_to_int(raw: Optional[float]) -> int:
    if raw is None:
        return 0
    try:
        return int(round(raw * 100))
    except Exception:
        return 0

def _derive_status(value, std) -> str:
    if value is None or std is None:
        return 'na'
    try:
        if std == 0:
            return 'na'
        diff_ratio = abs(value - std) / abs(std)
        if diff_ratio <= 0.10:
            return 'ok'
        if diff_ratio <= 0.20:
            return 'warn'
        return 'bad'
    except Exception:
        return 'na'

def adapt_action_evaluation(core_eval, *, sport: Optional[str] = None, action_name: Optional[str] = None,
                            user_video_path: Optional[str] = None, standard_video_path: Optional[str] = None,
                            training_data: Optional[dict] = None) -> ActionEvaluationVM:
    sport_val = sport or getattr(core_eval, 'sport', 'Unknown')
    action_val = action_name or getattr(core_eval, 'action_name', getattr(core_eval, 'name', 'Action'))
    stage_objs = getattr(core_eval, 'stages', [])
    adapted = []
    seen = set()
    for s in stage_objs:
        vm = _adapt_stage(s)
        if vm.key in seen:
            continue
        seen.add(vm.key)
        adapted.append(vm)
    return ActionEvaluationVM(
        sport=sport_val,
        action_name=action_val,
        score=_score_to_int(getattr(core_eval, 'score', None)),
        summary_raw=getattr(core_eval, 'summary', None),
        summary_refined=getattr(core_eval, 'refined_summary', None),
        stages=adapted,
        training=_adapt_training(training_data) if training_data else None,
        video=VideoInfo(user_video_path=user_video_path, standard_video_path=standard_video_path)
            if (user_video_path or standard_video_path) else None
    )

def _adapt_stage(stage_obj) -> StageVM:
    metrics_vm = [_adapt_metric(m) for m in getattr(stage_obj, 'measurements', [])]
    suggestion = getattr(stage_obj, 'summary', None)
    # Frame references (optional attributes) - will populate when available
    user_frame_ref = None
    standard_frame_ref = None
    if hasattr(stage_obj, 'user_frame') and stage_obj.user_frame is not None:
        idx = getattr(stage_obj.user_frame, 'frame_index', None)
        vpath = getattr(stage_obj.user_frame, 'video_path', None) or getattr(stage_obj.user_frame, 'source_video', None)
        if idx is not None and vpath:
            user_frame_ref = FrameRef(frame_index=idx, video_path=vpath)
    if hasattr(stage_obj, 'standard_frame') and stage_obj.standard_frame is not None:
        idx = getattr(stage_obj.standard_frame, 'frame_index', None)
        vpath = getattr(stage_obj.standard_frame, 'video_path', None) or getattr(stage_obj.standard_frame, 'source_video', None)
        if idx is not None and vpath:
            standard_frame_ref = FrameRef(frame_index=idx, video_path=vpath)
    original_name = getattr(stage_obj, 'name', 'stage')
    norm_key = normalize_stage_key(original_name)
    display_name = getattr(stage_obj, 'display_name', original_name)
    if display_name.endswith('_stage'):
        display_name = display_name[:-6]
    return StageVM(
        key=norm_key,
        name=display_name,
        score=_score_to_int(getattr(stage_obj, 'score', None)),
        summary_raw=getattr(stage_obj, 'summary', None),
        suggestion=suggestion,
        metrics=metrics_vm,
        user_frame=user_frame_ref,
        standard_frame=standard_frame_ref,
    )

def _adapt_metric(metric_obj) -> MetricVM:
    key = getattr(metric_obj, 'key', 'metric')
    name = getattr(metric_obj, 'display_name', key)
    value = getattr(metric_obj, 'value', None)
    std_val = getattr(metric_obj, 'expected', None) or getattr(metric_obj, 'target', None)
    unit = getattr(metric_obj, 'unit', None)
    deviation = (value - std_val) if (value is not None and std_val is not None) else None
    status = getattr(metric_obj, 'status', None)
    if status is None:
        status = _derive_status(value, std_val)
    return MetricVM(
        key=key,
        name=name,
        user_value=value,
        std_value=std_val,
        unit=unit,
        deviation=deviation,
        status=status or 'na'
    )

def _adapt_training(training_dict: dict) -> TrainingVM:
    return TrainingVM(
        key_issues=list(training_dict.get('key_issues', [])),
        improvement_drills=list(training_dict.get('improvement_drills', [])),
        next_steps=list(training_dict.get('next_steps', [])),
    )

__all__ = ['adapt_action_evaluation']

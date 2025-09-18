from __future__ import annotations
"""High-level pipeline tying Pose -> Metrics -> Evaluation.

This consolidates previously separate demo logic into reusable functions.
"""
from typing import Dict, Tuple, Iterable, Optional
from core.experimental.models.pose_data import BodyPose
from core.experimental.config.sport_configs import ActionConfig
from core.metrics_engine import MetricsEngine, ActionMetricsResult
from core.evaluation import (
    ActionEvaluationConfig, StageRule, MeasurementRule,
    evaluate_action, evaluate_action_incremental
)


def action_metrics_to_eval_dict(result: ActionMetricsResult) -> Dict[str, Dict[str, Dict[str, float]]]:
    out: Dict[str, Dict[str, Dict[str, float]]] = {}
    for stage_res in result.stage_results:
        stage_map: Dict[str, Dict[str, float]] = {}
        for name, mv in stage_res.measurements.items():
            if mv.value is not None:
                stage_map[name] = {'value': mv.value}
        out[stage_res.stage_name] = stage_map
    return out


def build_default_evaluation_config(action_config: ActionConfig, language: str = 'zh_CN') -> ActionEvaluationConfig:
    stages_rules = []
    for st in action_config.stages:
        ms = []
        for mr in st.measurements:
            # Convert tolerance_range to target/tolerance
            target = None
            tolerance = None
            if mr.tolerance_range:
                min_v, max_v = mr.tolerance_range
                target = (min_v + max_v) / 2.0
                tolerance = (max_v - min_v) / 2.0
            ms.append(MeasurementRule(
                key=mr.name,
                target=target,
                tolerance=tolerance,
                min_value=mr.tolerance_range[0] if mr.tolerance_range else None,
                max_value=mr.tolerance_range[1] if mr.tolerance_range else None,
                weight=mr.weight,
                description={'zh_CN': mr.description, 'en_US': mr.description},
                score_strategy='linear'
            ))
        stages_rules.append(StageRule(name=st.name, measurements=ms, weight=st.weight, description={'zh_CN': st.description, 'en_US': st.description}))
    return ActionEvaluationConfig(action_name=action_config.name, stages=stages_rules, language=language, enable_scoring=True, enable_llm_refine=False)


def run_action_evaluation(action_config: ActionConfig, stage_pose_map: Dict[str, Tuple[BodyPose, int]], language: str = 'zh_CN', engine: Optional[MetricsEngine] = None) -> tuple:
    engine = engine or MetricsEngine()
    metrics_result = engine.compute_action(action_config, stage_pose_map)
    metrics_dict = action_metrics_to_eval_dict(metrics_result)
    eval_config = build_default_evaluation_config(action_config, language)
    evaluation = evaluate_action(metrics_dict, eval_config)
    return metrics_result, evaluation


def run_action_evaluation_incremental(previous_evaluation, action_config: ActionConfig, updated_stage_names: Iterable[str], stage_pose_map: Dict[str, Tuple[BodyPose, int]], language: str = 'zh_CN', engine: Optional[MetricsEngine] = None):
    engine = engine or MetricsEngine()
    metrics_result = engine.compute_action(action_config, stage_pose_map)
    metrics_dict = action_metrics_to_eval_dict(metrics_result)
    eval_config = build_default_evaluation_config(action_config, language)
    new_eval = evaluate_action_incremental(previous_evaluation, updated_stage_names, metrics_dict, eval_config)
    return metrics_result, new_eval

__all__ = [
    'run_action_evaluation', 'run_action_evaluation_incremental',
    'build_default_evaluation_config', 'action_metrics_to_eval_dict'
]

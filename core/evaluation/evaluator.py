from __future__ import annotations
from typing import List, Dict, Any, Optional, Iterable
from .models import (
    ActionEvaluationConfig, MeasurementRule, StageRule,
    MeasurementEvaluation, StageEvaluation, ActionEvaluation, EvaluationContext
)
from .scoring import STRATEGIES, deviation_pass
from .generator import generate_measurement_feedback, generate_stage_feedback
from .localization import ACTION_FEEDBACK
from .llm_refiner import refine_summary


def _pick_strategy(rule: MeasurementRule, enable_scoring: bool):
    if not enable_scoring:
        return STRATEGIES['none']
    if rule.score_strategy and rule.score_strategy in STRATEGIES:
        return STRATEGIES[rule.score_strategy]
    return STRATEGIES['linear']


def _evaluate_stage(stage_rule: StageRule, stage_metrics: Dict[str, Dict[str, Any]], config: ActionEvaluationConfig) -> StageEvaluation:
    measurement_evals: List[MeasurementEvaluation] = []
    stage_score_acc = 0.0
    stage_weight_sum = 0.0
    language = config.language
    for m_rule in stage_rule.measurements:
        raw = stage_metrics.get(m_rule.key, {})
        value = raw.get('value')
        expected = m_rule.target if m_rule.target is not None else raw.get('expected')
        deviation = None
        if value is not None and expected is not None:
            deviation = abs(value - expected)
        passed = deviation_pass(m_rule, value) if value is not None else None
        strat = _pick_strategy(m_rule, config.enable_scoring)
        score = strat(m_rule, value) if (value is not None) else None
        if score is not None:
            stage_score_acc += score * m_rule.weight
            stage_weight_sum += m_rule.weight
        me = MeasurementEvaluation(
            key=m_rule.key,
            value=value,
            expected=expected,
            deviation=deviation,
            score=score,
            passed=passed,
            feedback=None,
        )
        me.feedback = generate_measurement_feedback(m_rule, me, language)
        measurement_evals.append(me)
    stage_score = None
    if stage_weight_sum > 0:
        stage_score = stage_score_acc / stage_weight_sum
    stage_feedback = generate_stage_feedback(StageEvaluation(stage_rule.name, measurement_evals, stage_score, None), language)
    return StageEvaluation(name=stage_rule.name, measurements=measurement_evals, score=stage_score, feedback=stage_feedback)


def evaluate_action(metrics: Dict[str, Dict[str, Dict[str, Any]]], config: ActionEvaluationConfig) -> ActionEvaluation:
    stage_evals: List[StageEvaluation] = []
    total_score_acc = 0.0
    total_weight = 0.0
    for stage_rule in config.stages:
        stage_metrics = metrics.get(stage_rule.name, {})
        stage_eval = _evaluate_stage(stage_rule, stage_metrics, config)
        stage_evals.append(stage_eval)
        if stage_eval.score is not None:
            total_score_acc += stage_eval.score * stage_rule.weight
            total_weight += stage_rule.weight
    overall_score = None
    if total_weight > 0:
        overall_score = total_score_acc / total_weight
    loc = ACTION_FEEDBACK.get(config.language, ACTION_FEEDBACK['en_US'])
    if overall_score is None:
        summary_key = 'overall_mixed'
    elif overall_score >= 0.8:
        summary_key = 'overall_good'
    elif overall_score >= 0.4:
        summary_key = 'overall_mixed'
    else:
        summary_key = 'overall_poor'
    summary = loc[summary_key].format(action=config.action_name)
    refined = None
    if config.enable_llm_refine:
        refined = refine_summary(summary, config.language, config.llm_style)
    return ActionEvaluation(action_name=config.action_name, stages=stage_evals, score=overall_score, summary=summary, refined_summary=refined, language=config.language)


def evaluate_action_incremental(previous: Optional[ActionEvaluation], updated_stage_names: Iterable[str], metrics: Dict[str, Dict[str, Dict[str, Any]]], config: ActionEvaluationConfig) -> ActionEvaluation:
    if previous is None:
        return evaluate_action(metrics, config)
    # Build map of existing stage evaluations
    stage_map = {s.name: s for s in previous.stages}
    # Recompute only specified stages
    for name in updated_stage_names:
        rule = next((r for r in config.stages if r.name == name), None)
        if rule is None:
            continue
        stage_metrics = metrics.get(name, {})
        stage_map[name] = _evaluate_stage(rule, stage_metrics, config)
    # Rebuild ordered list according to config order
    ordered = []
    total_score_acc = 0.0
    total_weight = 0.0
    for rule in config.stages:
        st = stage_map.get(rule.name)
        if st is None:
            st = _evaluate_stage(rule, metrics.get(rule.name, {}), config)
            stage_map[rule.name] = st
        ordered.append(st)
        if st.score is not None:
            total_score_acc += st.score * rule.weight
            total_weight += rule.weight
    overall_score = None
    if total_weight > 0:
        overall_score = total_score_acc / total_weight
    loc = ACTION_FEEDBACK.get(config.language, ACTION_FEEDBACK['en_US'])
    if overall_score is None:
        summary_key = 'overall_mixed'
    elif overall_score >= 0.8:
        summary_key = 'overall_good'
    elif overall_score >= 0.4:
        summary_key = 'overall_mixed'
    else:
        summary_key = 'overall_poor'
    summary = loc[summary_key].format(action=config.action_name)
    refined = None
    if config.enable_llm_refine:
        refined = refine_summary(summary, config.language, config.llm_style)
    return ActionEvaluation(action_name=config.action_name, stages=ordered, score=overall_score, summary=summary, refined_summary=refined, language=config.language)

__all__ = ['evaluate_action', 'evaluate_action_incremental']

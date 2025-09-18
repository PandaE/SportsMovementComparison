from __future__ import annotations
from typing import Optional
from .models import MeasurementRule, MeasurementEvaluation, StageEvaluation
from .localization import MEASUREMENT_FEEDBACK, STAGE_FEEDBACK, DEFAULT_DESC


def generate_measurement_feedback(rule: MeasurementRule, eval_obj: MeasurementEvaluation, language: str) -> str:
    loc = MEASUREMENT_FEEDBACK.get(language, MEASUREMENT_FEEDBACK['en_US'])
    desc = (rule.description or {}).get(language) or DEFAULT_DESC.get(language, 'Metric')
    if eval_obj.passed is True:
        return loc['default_pass'].format(desc=desc, value=eval_obj.value if eval_obj.value is not None else 0)
    if rule.target is not None and rule.tolerance is not None and eval_obj.deviation is not None:
        return loc['deviation_fail'].format(desc=desc, dev=eval_obj.deviation, target=rule.target, tol=rule.tolerance, value=eval_obj.value)
    return loc['default_fail'].format(desc=desc, value=eval_obj.value if eval_obj.value is not None else 0)


def generate_stage_feedback(stage_eval: StageEvaluation, language: str) -> str:
    loc = STAGE_FEEDBACK.get(language, STAGE_FEEDBACK['en_US'])
    stage_name = stage_eval.name
    passed = sum(1 for m in stage_eval.measurements if m.passed is True)
    total = len(stage_eval.measurements)
    if total == 0:
        return ''
    ratio = passed / total
    if ratio >= 0.8:
        key = 'summary_good'
    elif ratio >= 0.4:
        key = 'summary_mixed'
    else:
        key = 'summary_poor'
    return loc[key].format(stage=stage_name)

__all__ = ['generate_measurement_feedback', 'generate_stage_feedback']

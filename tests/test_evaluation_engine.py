import sys, os
import math
import pytest

# Ensure project root on path
ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)
if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from core.metrics_engine import MeasurementValue, StageMetricsResult, ActionMetricsResult
from core.evaluation import (
    MeasurementRule, StageRule, ActionEvaluationConfig, evaluate_action, evaluate_action_incremental
)


def build_dummy_metrics():
    # Simulate metrics_engine output shape: { stage: { key: { 'value': float } } }
    return {
        'prepare': {
            'elbow_angle': {'value': 175.0},
            'knee_angle': {'value': 160.0},
        },
        'swing': {
            'racket_height': {'value': 1.85},
            'torso_rotation': {'value': 42.0},
        }
    }


def test_evaluation_no_scoring():
    metrics = build_dummy_metrics()
    config = ActionEvaluationConfig(
        action_name='badminton_swing',
        stages=[
            StageRule(
                name='prepare',
                measurements=[
                    MeasurementRule(key='elbow_angle', target=180, tolerance=10, weight=1.0),
                    MeasurementRule(key='knee_angle', target=165, tolerance=15, weight=1.0),
                ],
                weight=1.0
            ),
            StageRule(
                name='swing',
                measurements=[
                    MeasurementRule(key='racket_height', min_value=1.5, max_value=2.0, weight=1.0),
                    MeasurementRule(key='torso_rotation', target=45, tolerance=10, weight=1.0),
                ],
                weight=1.0
            )
        ],
        language='en_US',
        enable_scoring=False,
    )
    result = evaluate_action(metrics, config)
    assert result.action_name == 'badminton_swing'
    # scoring disabled -> measurement scores should be 1.0 (none strategy), overall score still aggregated
    assert result.score == pytest.approx(1.0)
    assert len(result.stages) == 2


def test_evaluation_with_scoring_and_refine():
    metrics = build_dummy_metrics()
    config = ActionEvaluationConfig(
        action_name='badminton_swing',
        stages=[
            StageRule(
                name='prepare',
                measurements=[
                    MeasurementRule(key='elbow_angle', target=180, tolerance=5, weight=1.0),  # more strict
                    MeasurementRule(key='knee_angle', target=170, tolerance=5, weight=1.0),
                ],
                weight=1.0
            ),
            StageRule(
                name='swing',
                measurements=[
                    MeasurementRule(key='racket_height', min_value=1.5, max_value=2.0, weight=1.0),
                    MeasurementRule(key='torso_rotation', target=50, tolerance=5, weight=1.0),
                ],
                weight=1.0
            )
        ],
        language='zh_CN',
        enable_scoring=True,
        enable_llm_refine=True,
        llm_style='coach'
    )
    result = evaluate_action(metrics, config)
    assert result.score is not None
    assert result.refined_summary is not None
    # Expect not perfect due to strict tolerances
    assert result.score < 1.0
    # Ensure each stage has measurements
    for st in result.stages:
        assert st.measurements


def test_incremental_update():
    metrics = build_dummy_metrics()
    config = ActionEvaluationConfig(
        action_name='badminton_swing',
        stages=[
            StageRule(
                name='prepare',
                measurements=[
                    MeasurementRule(key='elbow_angle', target=180, tolerance=10, weight=1.0),
                    MeasurementRule(key='knee_angle', target=165, tolerance=10, weight=1.0),
                ],
                weight=1.0
            ),
            StageRule(
                name='swing',
                measurements=[
                    MeasurementRule(key='racket_height', min_value=1.5, max_value=2.0, weight=1.0),
                    MeasurementRule(key='torso_rotation', target=45, tolerance=10, weight=1.0),
                ],
                weight=1.0
            )
        ],
        language='en_US',
        enable_scoring=True,
    )
    first = evaluate_action(metrics, config)
    # simulate user adjustment only affecting 'swing' stage measurements
    metrics['swing']['torso_rotation']['value'] = 55.0  # worse deviation
    second = evaluate_action_incremental(first, ['swing'], metrics, config)
    # prepare stage object should be reused logically (same score)
    first_prepare = next(s for s in first.stages if s.name == 'prepare')
    second_prepare = next(s for s in second.stages if s.name == 'prepare')
    assert abs(first_prepare.score - second_prepare.score) < 1e-9
    # swing stage score should change
    first_swing = next(s for s in first.stages if s.name == 'swing')
    second_swing = next(s for s in second.stages if s.name == 'swing')
    assert (second_swing.score is not None) and (first_swing.score is not None)
    assert second_swing.score <= first_swing.score
    # overall score should reflect new swing degradation
    assert second.score <= first.score


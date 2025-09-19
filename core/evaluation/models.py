from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

# Basic threshold & weighting config for a single measurement
@dataclass
class MeasurementRule:
    key: str  # measurement key from metrics engine
    target: Optional[float] = None  # expected ideal value (if applicable)
    tolerance: Optional[float] = None  # acceptable absolute deviation around target
    min_value: Optional[float] = None  # range lower bound (for normalization)
    max_value: Optional[float] = None  # range upper bound (for normalization)
    weight: float = 1.0  # relative weight when aggregating stage/action
    advice: Optional[Dict[str, str]] = None  # language -> advice template
    description: Optional[Dict[str, str]] = None  # language -> description template
    score_strategy: Optional[str] = None  # named strategy (e.g., 'linear')

# Config for a stage - grouping of measurement rules
@dataclass
class StageRule:
    name: str
    measurements: List[MeasurementRule]
    weight: float = 1.0
    advice: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None

# Overall action evaluation config
@dataclass
class ActionEvaluationConfig:
    action_name: str
    stages: List[StageRule]
    language: str = "zh_CN"
    enable_scoring: bool = True
    enable_llm_refine: bool = False
    llm_style: Optional[str] = None  # e.g., 'coach', 'concise'

# Result structures
@dataclass
class MeasurementEvaluation:
    key: str
    value: Optional[float]
    expected: Optional[float]
    deviation: Optional[float]
    score: Optional[float]
    passed: Optional[bool]
    feedback: Optional[str]

@dataclass
class StageEvaluation:
    name: str
    measurements: List[MeasurementEvaluation]
    score: Optional[float]
    feedback: Optional[str]

@dataclass
class ActionEvaluation:
    action_name: str
    stages: List[StageEvaluation]
    score: Optional[float]
    summary: Optional[str]
    refined_summary: Optional[str] = None
    language: str = "zh_CN"

# Type alias for metrics input: expecting ActionMetricsResult structure from metrics_engine
MetricsDict = Dict[str, Dict[str, Dict[str, Any]]]
# metrics[action_stage][measurement_key] -> { value, expected(optional) }

# Callback type for scoring strategies
ScoreFunc = Callable[[MeasurementRule, float], float]

@dataclass
class EvaluationContext:
    config: ActionEvaluationConfig
    metrics: MetricsDict
    score_strategies: Dict[str, ScoreFunc]
    language: str

__all__ = [
    'MeasurementRule', 'StageRule', 'ActionEvaluationConfig',
    'MeasurementEvaluation', 'StageEvaluation', 'ActionEvaluation',
    'EvaluationContext', 'MetricsDict'
]

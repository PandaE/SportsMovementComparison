from __future__ import annotations
from typing import Optional
from .models import MeasurementRule

# Basic scoring strategies. All return value in [0,1].

def none_strategy(rule: MeasurementRule, value: float) -> float:
    return 1.0  # treat as perfect when scoring disabled per measurement

def linear_strategy(rule: MeasurementRule, value: float) -> float:
    # Use target + tolerance if provided; else min/max normalization; else 1.0
    if rule.target is not None and rule.tolerance is not None:
        deviation = abs(value - rule.target)
        if deviation <= rule.tolerance:
            return 1.0
        # beyond tolerance degrade linearly until 0 at 3 * tolerance
        max_dev = rule.tolerance * 3
        if deviation >= max_dev:
            return 0.0
        return max(0.0, 1 - (deviation - rule.tolerance) / (max_dev - rule.tolerance))
    if rule.min_value is not None and rule.max_value is not None and rule.max_value > rule.min_value:
        span = rule.max_value - rule.min_value
        clamped = max(rule.min_value, min(rule.max_value, value))
        return (clamped - rule.min_value) / span
    return 1.0

def deviation_pass(rule: MeasurementRule, value: float) -> Optional[bool]:
    if rule.target is not None and rule.tolerance is not None:
        return abs(value - rule.target) <= rule.tolerance
    return None

STRATEGIES = {
    'none': none_strategy,
    'linear': linear_strategy,
}

__all__ = ['STRATEGIES', 'linear_strategy', 'none_strategy', 'deviation_pass']

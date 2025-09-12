"""
Configuration package for experimental motion analysis.
"""
from .sport_configs import SportConfigs, ActionConfig, StageConfig, MeasurementRule
from .comparison_rules import ComparisonRules, LLMPromptTemplates

__all__ = [
    'SportConfigs',
    'ActionConfig', 
    'StageConfig',
    'MeasurementRule',
    'ComparisonRules',
    'LLMPromptTemplates'
]
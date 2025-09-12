"""
Comparison result models.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from .pose_data import FrameAnalysis


@dataclass
class MeasurementComparison:
    """单个测量值的对比结果"""
    measurement_name: str
    user_value: float
    standard_value: float
    difference: float
    percentage_diff: float
    is_within_tolerance: bool
    tolerance_range: tuple  # (min, max)
    
    @property
    def similarity_score(self) -> float:
        """相似度评分 (0-100)"""
        if self.is_within_tolerance:
            return max(0, 100 - abs(self.percentage_diff))
        else:
            # 超出容忍范围时，分数快速下降
            return max(0, 100 - abs(self.percentage_diff) * 2)


@dataclass
class FrameComparison:
    """帧对比结果"""
    stage_name: str  # 如 "架拍阶段结束"
    user_frame: FrameAnalysis
    standard_frame: FrameAnalysis
    measurements: List[MeasurementComparison]
    overall_score: float
    
    def get_measurement_comparison(self, name: str) -> Optional[MeasurementComparison]:
        """获取特定测量的对比结果"""
        for measurement in self.measurements:
            if measurement.measurement_name == name:
                return measurement
        return None


@dataclass
class LLMEvaluation:
    """LLM评价结果"""
    overall_assessment: str
    specific_feedback: List[str]
    improvement_suggestions: List[str]
    score_explanation: str
    confidence: float = 0.0


@dataclass
class ComprehensiveComparison:
    """综合对比结果"""
    sport: str
    action: str
    frame_comparisons: List[FrameComparison]
    overall_score: float
    llm_evaluation: Optional[LLMEvaluation] = None
    
    def get_stage_comparison(self, stage_name: str) -> Optional[FrameComparison]:
        """获取特定阶段的对比结果"""
        for comparison in self.frame_comparisons:
            if comparison.stage_name == stage_name:
                return comparison
        return None
    
    def calculate_weighted_score(self, stage_weights: Dict[str, float] = None) -> float:
        """计算加权平均分"""
        if not stage_weights:
            # 默认等权重
            stage_weights = {comp.stage_name: 1.0 for comp in self.frame_comparisons}
        
        total_weighted_score = 0
        total_weight = 0
        
        for comparison in self.frame_comparisons:
            weight = stage_weights.get(comparison.stage_name, 1.0)
            total_weighted_score += comparison.overall_score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0
"""
Rule-Based Evaluation Engine
基于规则的评价引擎

A comprehensive evaluation engine that uses the new configuration system
to provide accurate, professional sports movement analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from dataclasses import dataclass
from .evaluation_config import (
    MeasurementSpec, StageSpec, ActionSpec, EvaluationStandards,
    ImportanceLevel, get_config_manager
)


@dataclass
class MeasurementResult:
    """单个测量结果"""
    name: str
    value: float
    ideal_value: float
    unit: str
    score: float  # 0-100
    level: str   # "perfect", "excellent", "good", "needs_improvement", "poor"
    feedback: str
    within_range: bool
    importance: ImportanceLevel


@dataclass  
class StageResult:
    """阶段评价结果"""
    name: str
    display_name: str
    measurements: List[MeasurementResult]
    stage_score: float  # 0-100
    weighted_score: float  # 考虑权重后的分数贡献
    weight: float
    feedback: str
    valid_measurements_count: int


@dataclass
class OverallResult:
    """总体评价结果"""
    action_name: str
    display_name: str
    sport: str
    total_score: float  # 0-100
    level: str
    stages: List[StageResult]
    summary: str
    improvement_suggestions: List[str]
    strengths: List[str]


class RuleBasedEvaluator:
    """基于规则的评价引擎"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.standards = EvaluationStandards()
    
    def evaluate(self, sport: str, action: str, measurements: Dict[str, float]) -> OverallResult:
        """
        执行完整评价
        
        Args:
            sport: 运动类型 (如 "badminton")
            action: 动作类型 (如 "clear") 
            measurements: 测量数据 {"measurement_name": value, ...}
            
        Returns:
            OverallResult: 完整的评价结果
        """
        # 获取配置
        action_config = self.config_manager.get_action_config(sport, action)
        if not action_config:
            raise ValueError(f"不支持的运动动作组合: {sport} - {action}")
        
        # 评价各个阶段
        stage_results = []
        total_weighted_score = 0.0
        
        for stage_spec in action_config.stages:
            stage_result = self._evaluate_stage(stage_spec, measurements)
            stage_results.append(stage_result)
            total_weighted_score += stage_result.weighted_score
        
        # 生成总体结果
        total_score = min(100, max(0, total_weighted_score))
        level = self._get_score_level(total_score)
        
        # 生成反馈
        summary = self._generate_summary(total_score, level, action_config.display_name)
        improvements = self._generate_improvement_suggestions(stage_results)
        strengths = self._generate_strengths(stage_results)
        
        return OverallResult(
            action_name=action_config.name,
            display_name=action_config.display_name,
            sport=sport,
            total_score=total_score,
            level=level,
            stages=stage_results,
            summary=summary,
            improvement_suggestions=improvements,
            strengths=strengths
        )
    
    def _evaluate_stage(self, stage_spec: StageSpec, measurements: Dict[str, float]) -> StageResult:
        """评价单个阶段"""
        measurement_results = []
        total_score = 0.0
        total_weight = 0.0
        valid_count = 0
        
        for measurement_spec in stage_spec.measurements:
            if measurement_spec.name in measurements:
                value = measurements[measurement_spec.name]
                result = self._evaluate_measurement(measurement_spec, value)
                measurement_results.append(result)
                
                # 计算加权分数
                weight = measurement_spec.weight
                importance_multiplier = self.standards.importance_multipliers[measurement_spec.importance.value]
                effective_weight = weight * importance_multiplier
                
                total_score += result.score * effective_weight
                total_weight += effective_weight
                valid_count += 1
        
        # 计算阶段分数
        if total_weight > 0:
            stage_score = total_score / total_weight
        else:
            stage_score = 0.0
        
        # 检查是否满足最小有效测量数要求
        if valid_count < stage_spec.min_measurements_for_valid:
            stage_score *= 0.5  # 惩罚不完整的阶段
        
        weighted_score = stage_score * stage_spec.weight
        
        # 生成阶段反馈
        feedback = self._generate_stage_feedback(stage_spec.display_name, stage_score, valid_count, len(stage_spec.measurements))
        
        return StageResult(
            name=stage_spec.name,
            display_name=stage_spec.display_name,
            measurements=measurement_results,
            stage_score=stage_score,
            weighted_score=weighted_score,
            weight=stage_spec.weight,
            feedback=feedback,
            valid_measurements_count=valid_count
        )
    
    def _evaluate_measurement(self, measurement_spec: MeasurementSpec, value: float) -> MeasurementResult:
        """评价单个测量项"""
        ideal = measurement_spec.ideal_value
        
        # 判断所在范围并计算分数
        score, level, within_range = self._calculate_measurement_score(value, measurement_spec)
        
        # 生成反馈
        feedback = self._generate_measurement_feedback(measurement_spec, value, ideal, level)
        
        return MeasurementResult(
            name=measurement_spec.name,
            value=value,
            ideal_value=ideal,
            unit=measurement_spec.unit,
            score=score,
            level=level,
            feedback=feedback,
            within_range=within_range,
            importance=measurement_spec.importance
        )
    
    def _calculate_measurement_score(self, value: float, spec: MeasurementSpec) -> Tuple[float, str, bool]:
        """计算测量分数和等级"""
        
        # 检查各个范围
        if self._in_range(value, spec.excellent_range):
            # 优秀范围 - 90-100分
            base_score = self.standards.scoring_params["excellent_base"]
            diff_ratio = abs(value - spec.ideal_value) / (spec.excellent_range[1] - spec.excellent_range[0])
            score = min(100, base_score + (1 - diff_ratio) * 10)
            level = "excellent"
            within_range = True
            
        elif self._in_range(value, spec.good_range):
            # 良好范围 - 75-89分
            base_score = self.standards.scoring_params["good_base"]
            range_width = spec.good_range[1] - spec.good_range[0]
            distance_from_ideal = abs(value - spec.ideal_value)
            score = max(75, base_score - (distance_from_ideal / range_width) * 15)
            level = "good"
            within_range = True
            
        elif self._in_range(value, spec.acceptable_range):
            # 可接受范围 - 60-74分
            base_score = self.standards.scoring_params["acceptable_base"]
            range_width = spec.acceptable_range[1] - spec.acceptable_range[0]
            distance_from_ideal = abs(value - spec.ideal_value)
            score = max(50, base_score - (distance_from_ideal / range_width) * 15)
            level = "needs_improvement"
            within_range = True
            
        else:
            # 超出可接受范围 - 0-59分
            distance_from_acceptable = min(
                abs(value - spec.acceptable_range[0]),
                abs(value - spec.acceptable_range[1])
            )
            penalty = distance_from_acceptable * self.standards.scoring_params["out_of_range_penalty"]
            score = max(0, 50 - penalty)
            level = "poor"
            within_range = False
        
        return score, level, within_range
    
    def _in_range(self, value: float, range_tuple: tuple) -> bool:
        """检查值是否在范围内"""
        return range_tuple[0] <= value <= range_tuple[1]
    
    def _get_score_level(self, score: float) -> str:
        """根据分数获取等级"""
        for level_name, level_info in sorted(
            self.standards.score_levels.items(),
            key=lambda x: x[1]['min_score'],
            reverse=True
        ):
            if score >= level_info['min_score']:
                return level_name
        return "poor"
    
    def _generate_measurement_feedback(self, spec: MeasurementSpec, value: float, ideal: float, level: str) -> str:
        """生成测量项反馈"""
        templates = spec.feedback_templates
        
        if level == "excellent" or level == "good":
            return templates.get("perfect", f"{spec.description}表现很好")
        elif value < ideal:
            return templates.get("insufficient", templates.get("too_low", f"{spec.description}偏低，建议改进"))
        else:
            return templates.get("excessive", templates.get("too_high", f"{spec.description}偏高，建议调整"))
    
    def _generate_stage_feedback(self, stage_name: str, score: float, valid_count: int, total_count: int) -> str:
        """生成阶段反馈"""
        completeness = valid_count / total_count if total_count > 0 else 0
        
        if score >= 90:
            base_feedback = f"{stage_name}技术非常标准"
        elif score >= 75:
            base_feedback = f"{stage_name}技术基本正确"
        elif score >= 60:
            base_feedback = f"{stage_name}技术需要改进"
        else:
            base_feedback = f"{stage_name}技术存在明显问题"
        
        if completeness < 1.0:
            base_feedback += f"（检测到 {valid_count}/{total_count} 项指标）"
        
        return base_feedback
    
    def _generate_summary(self, total_score: float, level: str, action_name: str) -> str:
        """生成总体评价总结"""
        level_info = self.standards.score_levels[level]
        
        return f"{action_name}技术评价：{level_info['title']}（{total_score:.1f}分）。{level_info.get('description', '')}"
    
    def _generate_improvement_suggestions(self, stage_results: List[StageResult]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 找出分数最低的测量项
        all_measurements = []
        for stage in stage_results:
            all_measurements.extend(stage.measurements)
        
        # 按分数排序，重点关注分数低且重要的项目
        sorted_measurements = sorted(
            all_measurements,
            key=lambda x: (x.score, x.importance.value != "critical")
        )
        
        # 生成针对性建议
        for measurement in sorted_measurements[:3]:  # 最多3条建议
            if measurement.score < 70:
                if measurement.importance == ImportanceLevel.CRITICAL:
                    suggestions.append(f"【重点】{measurement.feedback}")
                else:
                    suggestions.append(measurement.feedback)
        
        # 如果没有低分项，给出一般性建议
        if not suggestions:
            suggestions.append("整体技术良好，建议继续保持并追求更高的一致性")
        
        return suggestions
    
    def _generate_strengths(self, stage_results: List[StageResult]) -> List[str]:
        """生成优势点总结"""
        strengths = []
        
        # 找出表现好的方面
        for stage in stage_results:
            if stage.stage_score >= 85:
                strengths.append(f"{stage.display_name}技术扎实")
            
            # 找出优秀的测量项
            excellent_measurements = [
                m for m in stage.measurements
                if m.score >= 90 and m.importance in [ImportanceLevel.CRITICAL, ImportanceLevel.IMPORTANT]
            ]
            
            for measurement in excellent_measurements[:2]:  # 最多2个优点
                strengths.append(f"{measurement.name}表现优秀")
        
        if not strengths:
            strengths.append("基础动作已掌握，继续努力提升")
        
        return strengths


def create_evaluator() -> RuleBasedEvaluator:
    """创建评价器实例"""
    return RuleBasedEvaluator()
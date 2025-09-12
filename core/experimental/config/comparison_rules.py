"""
General comparison rules and utilities.
"""
from typing import Dict, Any
import math


class ComparisonRules:
    """对比规则工具类"""
    
    @staticmethod
    def calculate_percentage_difference(user_value: float, standard_value: float) -> float:
        """计算百分比差异"""
        if standard_value == 0:
            return float('inf') if user_value != 0 else 0
        return ((user_value - standard_value) / standard_value) * 100
    
    @staticmethod
    def is_within_tolerance(value: float, tolerance_range: tuple) -> bool:
        """检查值是否在容忍范围内"""
        min_val, max_val = tolerance_range
        return min_val <= value <= max_val
    
    @staticmethod
    def calculate_similarity_score(user_value: float, standard_value: float, 
                                 tolerance_range: tuple) -> float:
        """计算相似度评分 (0-100)"""
        diff_percentage = abs(ComparisonRules.calculate_percentage_difference(
            user_value, standard_value))
        
        # 在容忍范围内，根据差异程度给分
        if ComparisonRules.is_within_tolerance(user_value, tolerance_range):
            if diff_percentage <= 5:  # 5%以内差异，几乎满分
                return 95 + (5 - diff_percentage)
            elif diff_percentage <= 15:  # 15%以内，线性递减
                return 85 - (diff_percentage - 5) * 1.5
            else:  # 超过15%但在容忍范围内
                return max(70, 85 - diff_percentage)
        else:
            # 超出容忍范围，分数快速下降
            excess_diff = max(0, diff_percentage - 20)  # 超出20%的部分
            return max(0, 60 - excess_diff * 2)
    
    @staticmethod
    def normalize_angle(angle: float) -> float:
        """标准化角度到0-180度范围"""
        if angle < 0:
            angle = abs(angle)
        if angle > 180:
            angle = 360 - angle
        return angle
    
    @staticmethod
    def calculate_weighted_average(scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """计算加权平均分"""
        total_weighted_score = 0
        total_weight = 0
        
        for name, score in scores.items():
            weight = weights.get(name, 1.0)
            total_weighted_score += score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0


class LLMPromptTemplates:
    """LLM提示词模板"""
    
    @staticmethod
    def get_evaluation_prompt(sport: str, action: str, comparison_data: Dict[str, Any]) -> str:
        """生成评价提示词"""
        prompt = f"""
你是一位专业的{sport}教练，正在分析学员的{action}技术动作。

以下是技术动作的详细对比数据：

"""
        
        for stage_name, stage_data in comparison_data.items():
            prompt += f"\n【{stage_name}】\n"
            for measurement in stage_data.get('measurements', []):
                name = measurement.get('name', '')
                user_val = measurement.get('user_value', 0)
                standard_val = measurement.get('standard_value', 0)
                diff = measurement.get('difference', 0)
                unit = measurement.get('unit', '')
                
                prompt += f"- {name}: 学员 {user_val}{unit}, 标准 {standard_val}{unit}, 差异 {diff:.1f}{unit}\n"
        
        prompt += f"""

请基于以上数据，提供专业的技术分析和改进建议：

1. 总体评价：用1-2句话概括学员的技术水平
2. 具体反馈：针对每个关键测量点的表现给出具体评价
3. 改进建议：提供3-5条具体的训练建议
4. 评分说明：解释为什么给出这个分数

请用专业但易懂的语言回答，重点关注技术要点和实用的改进方法。
"""
        return prompt
    
    @staticmethod
    def get_quick_feedback_prompt(measurement_name: str, user_value: float, 
                                standard_value: float, unit: str) -> str:
        """生成快速反馈提示词"""
        return f"""
针对{measurement_name}这一技术要点：
- 你的数值：{user_value}{unit}
- 标准数值：{standard_value}{unit}

请用一句话给出简洁的技术建议。
"""
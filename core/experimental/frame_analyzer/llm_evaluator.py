"""
LLM-based evaluation and feedback generation.
"""
import json
from typing import Optional, Dict, Any
from ..models.comparison_result import ComprehensiveComparison, LLMEvaluation
from ..config.comparison_rules import LLMPromptTemplates


class LLMEvaluator:
    """LLM评价生成器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        初始化LLM评价器
        
        Args:
            api_key: API密钥
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                print(f"LLM客户端初始化成功，使用模型: {self.model}")
            except ImportError:
                print("OpenAI库未安装，将使用模拟评价")
                self.client = None
        else:
            print("未提供API密钥，将使用模拟评价")
    
    def generate_evaluation(self, comparison_result: ComprehensiveComparison) -> LLMEvaluation:
        """
        生成综合评价
        
        Args:
            comparison_result: 对比结果
            
        Returns:
            LLM评价结果
        """
        if self.client:
            return self._generate_real_evaluation(comparison_result)
        else:
            return self._generate_mock_evaluation(comparison_result)
    
    def _generate_real_evaluation(self, comparison_result: ComprehensiveComparison) -> LLMEvaluation:
        """使用真实LLM生成评价"""
        # 准备数据
        comparison_data = self._prepare_comparison_data(comparison_result)
        
        # 生成提示词
        prompt = LLMPromptTemplates.get_evaluation_prompt(
            comparison_result.sport, 
            comparison_result.action, 
            comparison_data
        )
        
        try:
            # 调用LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位专业的体育教练，擅长技术动作分析。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # 解析响应
            content = response.choices[0].message.content
            return self._parse_llm_response(content, comparison_result.overall_score)
            
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self._generate_mock_evaluation(comparison_result)
    
    def _generate_mock_evaluation(self, comparison_result: ComprehensiveComparison) -> LLMEvaluation:
        """生成模拟评价（用于测试和无API密钥时）"""
        score = comparison_result.overall_score
        
        # 根据分数生成不同的评价
        if score >= 90:
            overall_assessment = "技术动作非常标准，各项指标都接近专业水平。"
            improvement_suggestions = [
                "保持当前的技术水平，注意动作的一致性",
                "可以适当增加训练强度，提升动作的稳定性"
            ]
        elif score >= 75:
            overall_assessment = "技术动作基本正确，但在某些细节上还有改进空间。"
            improvement_suggestions = [
                "注意架拍时的肘关节角度，保持在90-110度之间",
                "加强核心力量训练，提升身体稳定性",
                "练习时注意动作的完整性和流畅性"
            ]
        elif score >= 60:
            overall_assessment = "技术动作有一定基础，但存在明显的问题需要纠正。"
            improvement_suggestions = [
                "重点改善架拍姿势，确保大臂与小臂形成合适的夹角",
                "加强基础动作练习，特别是手臂和身体的协调",
                "建议进行分解动作练习，逐步改善技术细节"
            ]
        else:
            overall_assessment = "技术动作存在较多问题，需要系统性的纠正和练习。"
            improvement_suggestions = [
                "建议从基础动作开始重新学习",
                "加强力量和柔韧性训练",
                "寻求专业教练的指导，进行系统性的技术改进"
            ]
        
        # 生成具体反馈
        specific_feedback = []
        for frame_comp in comparison_result.frame_comparisons:
            stage_feedback = f"【{frame_comp.stage_name}】得分: {frame_comp.overall_score:.1f}"
            for measurement in frame_comp.measurements:
                if not measurement.is_within_tolerance:
                    stage_feedback += f" - {measurement.measurement_name}需要改进"
            specific_feedback.append(stage_feedback)
        
        return LLMEvaluation(
            overall_assessment=overall_assessment,
            specific_feedback=specific_feedback,
            improvement_suggestions=improvement_suggestions,
            score_explanation=f"综合评分 {score:.1f}/100，基于各阶段技术动作的准确性计算。",
            confidence=0.85
        )
    
    def _prepare_comparison_data(self, comparison_result: ComprehensiveComparison) -> Dict[str, Any]:
        """准备用于LLM的对比数据"""
        data = {}
        
        for frame_comp in comparison_result.frame_comparisons:
            stage_data = {
                'score': frame_comp.overall_score,
                'measurements': []
            }
            
            for measurement in frame_comp.measurements:
                stage_data['measurements'].append({
                    'name': measurement.measurement_name,
                    'user_value': measurement.user_value,
                    'standard_value': measurement.standard_value,
                    'difference': measurement.difference,
                    'unit': '度',  # 可以从配置获取
                    'within_tolerance': measurement.is_within_tolerance
                })
            
            data[frame_comp.stage_name] = stage_data
        
        return data
    
    def _parse_llm_response(self, content: str, overall_score: float) -> LLMEvaluation:
        """解析LLM响应"""
        lines = content.strip().split('\n')
        
        overall_assessment = ""
        specific_feedback = []
        improvement_suggestions = []
        score_explanation = ""
        
        current_section = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "总体评价" in line or "overall" in line.lower():
                current_section = "overall"
                overall_assessment = line.split("：", 1)[-1] if "：" in line else line
            elif "具体反馈" in line or "feedback" in line.lower():
                current_section = "feedback"
            elif "改进建议" in line or "suggestion" in line.lower():
                current_section = "suggestions"
            elif "评分说明" in line or "score" in line.lower():
                current_section = "explanation"
                score_explanation = line.split("：", 1)[-1] if "：" in line else line
            else:
                if current_section == "overall" and not overall_assessment:
                    overall_assessment = line
                elif current_section == "feedback":
                    if line.startswith(("-", "•", "1.", "2.", "3.")):
                        specific_feedback.append(line[2:].strip())
                elif current_section == "suggestions":
                    if line.startswith(("-", "•", "1.", "2.", "3.")):
                        improvement_suggestions.append(line[2:].strip())
                elif current_section == "explanation" and not score_explanation:
                    score_explanation = line
        
        return LLMEvaluation(
            overall_assessment=overall_assessment or "技术动作分析完成。",
            specific_feedback=specific_feedback or ["详细分析已完成"],
            improvement_suggestions=improvement_suggestions or ["继续练习以提升技术水平"],
            score_explanation=score_explanation or f"综合评分: {overall_score:.1f}/100",
            confidence=0.9
        )
    
    def generate_quick_feedback(self, measurement_name: str, user_value: float, 
                              standard_value: float, unit: str) -> str:
        """生成单项快速反馈"""
        if self.client:
            prompt = LLMPromptTemplates.get_quick_feedback_prompt(
                measurement_name, user_value, standard_value, unit)
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一位体育教练，给出简洁的技术建议。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"快速反馈生成失败: {e}")
        
        # 模拟反馈
        diff = abs(user_value - standard_value)
        if diff < 5:
            return f"{measurement_name}很好，继续保持这个水平。"
        elif diff < 15:
            return f"{measurement_name}基本正确，稍作调整会更好。"
        else:
            return f"{measurement_name}需要明显改进，注意技术要点。"
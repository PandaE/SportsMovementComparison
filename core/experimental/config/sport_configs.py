"""
Sport-specific configuration and analysis rules.
"""
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class MeasurementRule:
    """单个测量规则 - 支持多种测量类型"""
    name: str
    description: str
    measurement_type: str  # "angle", "height", "distance", "ratio", "horizontal_distance", "vertical_distance"
    keypoints: List[str]  # 涉及的关键点列表，根据测量类型而定
    unit: str
    tolerance_range: Tuple[float, float]  # 容忍范围 (min, max)
    weight: float = 1.0  # 在总分中的权重
    reference_point: str = None  # 参考点（用于高度、距离等测量）
    direction: str = None  # 方向指示（如"up", "down", "left", "right"）


@dataclass 
class StageConfig:
    """运动阶段配置"""
    name: str
    description: str
    measurements: List[MeasurementRule]
    weight: float = 1.0  # 在总评分中的权重


@dataclass
class ActionConfig:
    """动作配置"""
    name: str
    description: str
    stages: List[StageConfig]


class SportConfigs:
    """运动配置管理器"""
    
    @staticmethod
    def get_badminton_forehand_clear() -> ActionConfig:
        """羽毛球正手高远球配置"""
        
        # 引拍阶段结束的测量规则
        backswing_measurements = [
            MeasurementRule(
                name="肘部高度",
                description="右肘相对于右肩的垂直高度差",
                measurement_type="vertical_distance",
                keypoints=["right_elbow"],
                unit="像素",
                tolerance_range=(-50, 50),  # 允许肘部在肩部上下50像素范围内
                weight=1.0,
                reference_point="right_shoulder",
                direction="up"
            ),
            MeasurementRule(
                name="手腕后摆",
                description="手腕相对于肘部的水平后摆距离",
                measurement_type="horizontal_distance", 
                keypoints=["right_wrist"],
                unit="像素",
                tolerance_range=(30, 120),  # 手腕应该后摆30-120像素
                weight=1.0,
                reference_point="right_elbow",
                direction="back"
            )
        ]
        
        # 发力阶段结束的测量规则
        power_measurements = [
            MeasurementRule(
                name="击球时手臂舒展度",
                description="击球瞬间大臂到手腕的伸展角度，反映发力充分程度",
                measurement_type="angle",
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],
                unit="度",
                tolerance_range=(140, 180),  # 手臂应该相对伸直，140-180度
                weight=1.0
            )
        ]
        
        # 架拍阶段结束的测量规则
        setup_measurements = [
            MeasurementRule(
                name="大臂小臂夹角",
                description="肘关节角度，反映架拍高度",
                measurement_type="angle",
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],  # 三点确定角度
                unit="度",
                tolerance_range=(20, 150),
                weight=1.0
            )
        ]
        
        return ActionConfig(
            name="正手高远球",
            description="羽毛球正手高远球技术动作",
            stages=[
                StageConfig(
                    name="setup_stage",
                    description="准备击球的架拍姿势",
                    measurements=setup_measurements,
                    weight=0.3  # 架拍阶段权重30%
                ),
                StageConfig(
                    name="backswing_stage",
                    description="拍子向后引拍到位的姿势",
                    measurements=backswing_measurements,
                    weight=0.2  # 引拍阶段权重20%
                ),
                StageConfig(
                    name="power_stage",
                    description="击球瞬间的发力姿势",
                    measurements=power_measurements,
                    weight=0.5  # 发力阶段权重50%，最重要的击球瞬间
                )
            ]
        )
    
    @staticmethod
    def get_config(sport: str, action: str) -> ActionConfig:
        """根据运动和动作获取配置"""
        # 支持中英文运动名称匹配
        is_badminton = (
            sport.lower() == "badminton" or 
            "羽毛球" in sport or 
            "badminton" in sport.lower()
        )
        
        # 支持中英文动作名称匹配
        is_clear_shot = (
            "clear" in action.lower() or 
            "正手高远" in action or
            "高远球" in action
        )
        
        if is_badminton and is_clear_shot:
            return SportConfigs.get_badminton_forehand_clear()
        else:
            raise ValueError(f"不支持的运动动作组合: {sport} - {action}")
    
    @staticmethod 
    def list_available_configs() -> List[Tuple[str, str]]:
        """列出所有可用的配置"""
        return [
            ("Badminton", "正手高远球")
        ]
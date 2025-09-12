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
                    name="架拍阶段结束",
                    description="准备击球的架拍姿势",
                    measurements=setup_measurements,
                    weight=1.0  # 目前只有一个阶段，权重为1
                )
            ]
        )
    
    @staticmethod
    def get_config(sport: str, action: str) -> ActionConfig:
        """根据运动和动作获取配置"""
        if sport.lower() == "badminton" and ("clear" in action.lower() or "正手高远" in action):
            return SportConfigs.get_badminton_forehand_clear()
        else:
            raise ValueError(f"不支持的运动动作组合: {sport} - {action}")
    
    @staticmethod 
    def list_available_configs() -> List[Tuple[str, str]]:
        """列出所有可用的配置"""
        return [
            ("Badminton", "正手高远球")
        ]
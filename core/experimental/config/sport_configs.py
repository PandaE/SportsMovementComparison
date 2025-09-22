"""
Sport-specific configuration and analysis rules.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MeasurementRule:
    """单个测量规则 - 支持多种测量类型

    name: 原始（当前为中文）标识，作为内部 key。
    display_en: 英文显示名称（新增，方案A）。未提供时可回退到 name。
    """
    name: str
    description: str
    measurement_type: str  # "angle", "height", "distance", "ratio", "horizontal_distance", "vertical_distance"
    keypoints: List[str]
    unit: str
    tolerance_range: Tuple[float, float]
    weight: float = 1.0
    reference_point: Optional[str] = None
    direction: Optional[str] = None
    display_en: Optional[str] = None


@dataclass 
class StageConfig:
    """运动阶段配置

    name: 原始阶段名（含 *_stage 后缀）保持不变，用于旧体系兼容。
    display_en: 英文显示名称（可选）。
    """
    name: str
    description: str
    measurements: List[MeasurementRule]
    weight: float = 1.0
    display_en: Optional[str] = None


@dataclass
class ActionConfig:
    """动作配置

    name: 原始动作名（当前中文）。
    display_en: 英文显示名（可选）。
    """
    name: str
    description: str
    stages: List[StageConfig]
    display_en: Optional[str] = None


class SportConfigs:
    """运动配置管理器"""
    
    @staticmethod
    def get_badminton_forehand_clear() -> ActionConfig:
        """羽毛球正手高远球配置"""
        
        # 引拍阶段结束的测量规则
        backswing_measurements = [
            MeasurementRule(
                name="肘部高度",
                display_en="Elbow Height",
                description="右肘相对于右肩的垂直高度差",
                measurement_type="vertical_distance",
                keypoints=["right_elbow"],
                unit="像素",
                tolerance_range=(-50, 50),
                weight=1.0,
                reference_point="right_shoulder",
                direction="up"
            ),
            MeasurementRule(
                name="手腕后摆",
                display_en="Wrist Backswing Distance",
                description="手腕相对于肘部的水平后摆距离",
                measurement_type="horizontal_distance", 
                keypoints=["right_wrist"],
                unit="像素",
                tolerance_range=(30, 120),
                weight=1.0,
                reference_point="right_elbow",
                direction="back"
            )
        ]
        
        # 发力阶段结束的测量规则
        power_measurements = [
            MeasurementRule(
                name="击球时手臂舒展度",
                display_en="Arm Extension at Impact",
                description="击球瞬间大臂到手腕的伸展角度，反映发力充分程度",
                measurement_type="angle",
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],
                unit="度",
                tolerance_range=(140, 180),
                weight=1.0
            )
        ]
        
        # 架拍阶段结束的测量规则
        setup_measurements = [
            MeasurementRule(
                name="大臂小臂夹角",
                display_en="Upper-Lower Arm Angle",
                description="肘关节角度，反映架拍高度",
                measurement_type="angle",
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],
                unit="度",
                tolerance_range=(20, 150),
                weight=1.0
            )
        ]
        
        return ActionConfig(
            name="正手高远球",
            display_en="Forehand Clear",
            description="羽毛球正手高远球技术动作",
            stages=[
                StageConfig(
                    name="setup_stage",
                    display_en="Setup",
                    description="准备击球的架拍姿势",
                    measurements=setup_measurements,
                    weight=0.3
                ),
                StageConfig(
                    name="backswing_stage",
                    display_en="Backswing",
                    description="拍子向后引拍到位的姿势",
                    measurements=backswing_measurements,
                    weight=0.2
                ),
                StageConfig(
                    name="power_stage",
                    display_en="Power / Impact",
                    description="击球瞬间的发力姿势",
                    measurements=power_measurements,
                    weight=0.5
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
            ("Badminton", "正手高远球"),  # display_en 可通过 ActionConfig.display_en 暴露
        ]
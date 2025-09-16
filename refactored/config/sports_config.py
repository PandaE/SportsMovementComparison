"""
Sports Configuration Module
运动配置模块

Based on the original experimental sport_configs.py, providing sport-specific measurement rules.
基于原始实验性配置文件，提供运动特定的测量规则。

This file strictly follows the original configuration format and content.
严格按照原始配置格式和内容。
"""

from typing import Dict, List, Any, Tuple
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


def get_sport_config(sport: str, action: str) -> ActionConfig:
    """
    Get configuration for specific sport and action.
    获取特定运动和动作的配置
    
    Args:
        sport: Sport name (e.g., "badminton")
        action: Action name (e.g., "clear")
        
    Returns:
        ActionConfig object
    """
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
        return get_badminton_forehand_clear()
    else:
        raise ValueError(f"不支持的运动动作组合: {sport} - {action}")


def get_badminton_forehand_clear() -> ActionConfig:
    """羽毛球正手高远球配置 - 完全基于原始配置"""
    
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


def get_available_configs() -> List[Tuple[str, str]]:
    """
    列出所有可用的配置 - 基于原始配置
    
    Returns:
        List of (sport, action) tuples
    """
    return [
        ("Badminton", "正手高远球")
    ]


def validate_measurement_rule(measurement: MeasurementRule) -> bool:
    """
    Validate a measurement rule.
    验证测量规则
    
    Args:
        measurement: MeasurementRule to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    if not measurement.name or not measurement.measurement_type:
        return False
    
    # Check keypoints
    if not measurement.keypoints or len(measurement.keypoints) < 1:
        return False
    
    # Check measurement type - 基于原始配置的测量类型
    valid_types = ["angle", "height", "distance", "ratio", "horizontal_distance", "vertical_distance"]
    if measurement.measurement_type not in valid_types:
        return False
    
    # Check tolerance range
    if not measurement.tolerance_range or len(measurement.tolerance_range) != 2:
        return False
    
    min_val, max_val = measurement.tolerance_range
    if min_val >= max_val:
        return False
    
    return True


def validate_action_config(config: ActionConfig) -> bool:
    """
    Validate an action configuration.
    验证动作配置
    
    Args:
        config: ActionConfig to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    if not config.name or not config.description:
        return False
    
    # Check stages
    if not config.stages or len(config.stages) == 0:
        return False
    
    # Validate each stage
    for stage in config.stages:
        if not isinstance(stage, StageConfig):
            return False
        
        # Validate measurements
        for measurement in stage.measurements:
            if not validate_measurement_rule(measurement):
                return False
    
    return True
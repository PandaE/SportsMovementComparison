"""
Evaluation Configuration System
评价配置系统

A new, simplified configuration system designed specifically for rule-based evaluation.
专为规则引擎评价设计的全新简化配置系统。
"""

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum


class MeasurementType(Enum):
    """测量类型枚举"""
    ANGLE = "angle"                    # 角度测量
    DISTANCE = "distance"              # 距离测量
    HEIGHT_DIFF = "height_diff"        # 高度差测量
    POSITION_RATIO = "position_ratio"  # 位置比例
    SPEED = "speed"                    # 速度测量


class ImportanceLevel(Enum):
    """重要性级别"""
    CRITICAL = "critical"     # 关键指标，权重 x1.5
    IMPORTANT = "important"   # 重要指标，权重 x1.2
    NORMAL = "normal"         # 普通指标，权重 x1.0
    MINOR = "minor"          # 次要指标，权重 x0.8


@dataclass
class MeasurementSpec:
    """测量规格定义"""
    name: str                           # 测量名称
    description: str                    # 详细描述
    measurement_type: MeasurementType   # 测量类型
    keypoints: List[str]               # 关键点列表
    unit: str                          # 单位
    
    # 评价标准
    ideal_value: float                 # 理想值
    excellent_range: tuple            # 优秀范围 (min, max)
    good_range: tuple                 # 良好范围 (min, max)
    acceptable_range: tuple           # 可接受范围 (min, max)
    
    # 权重和重要性
    weight: float = 1.0               # 在阶段中的权重
    importance: ImportanceLevel = ImportanceLevel.NORMAL
    
    # 反馈模板
    feedback_templates: Dict[str, str] = field(default_factory=dict)


@dataclass
class StageSpec:
    """阶段规格定义"""
    name: str                         # 阶段名称
    display_name: str                 # 显示名称
    description: str                  # 阶段描述
    weight: float                     # 在总评分中的权重
    measurements: List[MeasurementSpec]  # 测量项列表
    
    # 阶段特定配置
    min_measurements_for_valid: int = 1  # 最少需要多少个有效测量


@dataclass
class ActionSpec:
    """动作规格定义"""
    name: str                         # 动作名称
    display_name: str                 # 显示名称
    description: str                  # 动作描述
    sport: str                        # 所属运动
    stages: List[StageSpec]           # 阶段列表
    
    # 总体评价配置
    overall_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationStandards:
    """评价标准定义"""
    
    # 分数等级定义
    score_levels: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "perfect": {"min_score": 95, "title": "完美", "color": "#00C851"},
        "excellent": {"min_score": 85, "title": "优秀", "color": "#007E33"},
        "good": {"min_score": 70, "title": "良好", "color": "#FF8800"},
        "needs_improvement": {"min_score": 50, "title": "需改进", "color": "#FF4444"},
        "poor": {"min_score": 0, "title": "较差", "color": "#CC0000"}
    })
    
    # 评分计算参数
    scoring_params: Dict[str, float] = field(default_factory=lambda: {
        "perfect_bonus": 5,        # 完美范围内的加分
        "excellent_base": 90,      # 优秀范围的基础分
        "good_base": 75,          # 良好范围的基础分
        "acceptable_base": 60,    # 可接受范围的基础分
        "out_of_range_penalty": 2.0  # 超出范围的惩罚系数
    })
    
    # 重要性权重倍数
    importance_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "critical": 1.5,
        "important": 1.2,
        "normal": 1.0,
        "minor": 0.8
    })


class EvaluationConfigManager:
    """评价配置管理器"""
    
    def __init__(self):
        self.actions: Dict[str, ActionSpec] = {}
        self.standards = EvaluationStandards()
        self._load_default_configs()
    
    def _load_default_configs(self):
        """加载默认配置"""
        # 添加羽毛球正手高远球配置
        self.actions["badminton_clear"] = self._create_badminton_clear_config()
    
    def _create_badminton_clear_config(self) -> ActionSpec:
        """创建羽毛球正手高远球配置"""
        
        # 准备阶段测量
        preparation_measurements = [
            MeasurementSpec(
                name="stance_width",
                description="双脚站位宽度",
                measurement_type=MeasurementType.DISTANCE,
                keypoints=["left_ankle", "right_ankle"],
                unit="cm",
                ideal_value=50,
                excellent_range=(45, 55),
                good_range=(40, 60),
                acceptable_range=(35, 65),
                weight=0.4,
                importance=ImportanceLevel.IMPORTANT,
                feedback_templates={
                    "too_narrow": "站位略窄，建议适当放宽双脚距离以增强稳定性",
                    "too_wide": "站位过宽，建议收紧双脚以便于移动",
                    "perfect": "站位宽度很好，保持这个稳定的基础姿势"
                }
            ),
            MeasurementSpec(
                name="racket_ready_angle",
                description="球拍准备位置角度",
                measurement_type=MeasurementType.ANGLE,
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],
                unit="度",
                ideal_value=110,
                excellent_range=(105, 115),
                good_range=(95, 125),
                acceptable_range=(85, 135),
                weight=0.6,
                importance=ImportanceLevel.CRITICAL,
                feedback_templates={
                    "too_low": "球拍位置偏低，建议抬高准备位置以便快速反应",
                    "too_high": "球拍位置过高，建议降低到舒适的准备位置",
                    "perfect": "球拍准备位置很标准，有利于快速启动"
                }
            )
        ]
        
        # 引拍阶段测量
        backswing_measurements = [
            MeasurementSpec(
                name="shoulder_rotation",
                description="肩部转动角度",
                measurement_type=MeasurementType.ANGLE,
                keypoints=["left_shoulder", "right_shoulder", "center_hip"],
                unit="度",
                ideal_value=45,
                excellent_range=(40, 50),
                good_range=(30, 60),
                acceptable_range=(20, 70),
                weight=0.3,
                importance=ImportanceLevel.IMPORTANT,
                feedback_templates={
                    "insufficient": "肩部转动不足，影响发力，建议增加转肩幅度",
                    "excessive": "肩部转动过度，容易失衡，注意控制转动幅度",
                    "perfect": "肩部转动角度很好，为发力做好了准备"
                }
            ),
            MeasurementSpec(
                name="elbow_height",
                description="肘部相对肩部高度",
                measurement_type=MeasurementType.HEIGHT_DIFF,
                keypoints=["right_elbow", "right_shoulder"],
                unit="cm",
                ideal_value=0,  # 肘部与肩部同高
                excellent_range=(-5, 5),
                good_range=(-10, 10),
                acceptable_range=(-15, 15),
                weight=0.4,
                importance=ImportanceLevel.CRITICAL,
                feedback_templates={
                    "too_low": "肘部位置偏低，建议抬高肘部到肩部水平",
                    "too_high": "肘部位置过高，建议降低到舒适高度",
                    "perfect": "肘部高度很标准，有利于稳定发力"
                }
            ),
            MeasurementSpec(
                name="wrist_extension",
                description="手腕后摆距离",
                measurement_type=MeasurementType.DISTANCE,
                keypoints=["right_wrist", "right_elbow"],
                unit="cm",
                ideal_value=25,
                excellent_range=(20, 30),
                good_range=(15, 35),
                acceptable_range=(10, 40),
                weight=0.3,
                importance=ImportanceLevel.NORMAL,
                feedback_templates={
                    "insufficient": "手腕后摆不足，影响发力蓄势，建议增加引拍幅度",
                    "excessive": "手腕后摆过度，容易失控，注意保持适中幅度",
                    "perfect": "手腕后摆距离很好，蓄势充分"
                }
            )
        ]
        
        # 击球阶段测量
        contact_measurements = [
            MeasurementSpec(
                name="arm_extension",
                description="手臂伸展角度",
                measurement_type=MeasurementType.ANGLE,
                keypoints=["right_shoulder", "right_elbow", "right_wrist"],
                unit="度",
                ideal_value=160,
                excellent_range=(155, 165),
                good_range=(145, 175),
                acceptable_range=(135, 180),
                weight=0.4,
                importance=ImportanceLevel.CRITICAL,
                feedback_templates={
                    "insufficient": "击球时手臂伸展不充分，影响发力效果",
                    "over_extended": "手臂过度伸展，注意保持自然伸展角度",
                    "perfect": "击球时手臂伸展角度很好，发力充分"
                }
            ),
            MeasurementSpec(
                name="contact_height",
                description="击球点高度",
                measurement_type=MeasurementType.HEIGHT_DIFF,
                keypoints=["racket_contact_point", "right_shoulder"],
                unit="cm",
                ideal_value=30,  # 击球点应该在肩部上方30cm
                excellent_range=(25, 35),
                good_range=(20, 40),
                acceptable_range=(15, 45),
                weight=0.35,
                importance=ImportanceLevel.CRITICAL,
                feedback_templates={
                    "too_low": "击球点偏低，影响球的轨迹，建议提高击球点",
                    "too_high": "击球点过高，难以控制，注意适当降低",
                    "perfect": "击球点高度很好，有利于高远球轨迹"
                }
            ),
            MeasurementSpec(
                name="body_lean",
                description="击球时身体前倾角度",
                measurement_type=MeasurementType.ANGLE,
                keypoints=["head", "center_hip", "center_ankle"],
                unit="度",
                ideal_value=15,
                excellent_range=(10, 20),
                good_range=(5, 25),
                acceptable_range=(0, 30),
                weight=0.25,
                importance=ImportanceLevel.NORMAL,
                feedback_templates={
                    "too_upright": "身体过于直立，建议适当前倾增加发力",
                    "too_forward": "身体前倾过度，注意保持平衡",
                    "perfect": "身体前倾角度很好，发力与平衡兼顾"
                }
            )
        ]
        
        # 创建阶段配置
        stages = [
            StageSpec(
                name="preparation",
                display_name="准备阶段",
                description="准备击球的基础姿势",
                weight=0.2,
                measurements=preparation_measurements,
                min_measurements_for_valid=1
            ),
            StageSpec(
                name="backswing",
                display_name="引拍阶段", 
                description="向后引拍蓄势的动作",
                weight=0.3,
                measurements=backswing_measurements,
                min_measurements_for_valid=2
            ),
            StageSpec(
                name="contact",
                display_name="击球阶段",
                description="击球瞬间的技术动作",
                weight=0.5,
                measurements=contact_measurements,
                min_measurements_for_valid=2
            )
        ]
        
        return ActionSpec(
            name="badminton_clear",
            display_name="正手高远球",
            description="羽毛球正手高远球技术动作",
            sport="badminton",
            stages=stages,
            overall_config={
                "min_total_score": 50,  # 最低总分要求
                "weight_balance_check": True,  # 是否检查权重平衡
                "require_all_stages": False  # 是否要求所有阶段都有效
            }
        )
    
    def get_action_config(self, sport: str, action: str) -> Optional[ActionSpec]:
        """获取动作配置"""
        key = f"{sport}_{action}"
        return self.actions.get(key)
    
    def list_available_actions(self) -> List[tuple]:
        """列出所有可用的动作配置"""
        result = []
        for key, config in self.actions.items():
            result.append((config.sport, config.name, config.display_name))
        return result
    
    def validate_config(self, action_spec: ActionSpec) -> List[str]:
        """验证配置的有效性"""
        errors = []
        
        # 检查阶段权重总和
        total_weight = sum(stage.weight for stage in action_spec.stages)
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"阶段权重总和 {total_weight:.2f} 不等于 1.0")
        
        # 检查每个阶段的测量权重
        for stage in action_spec.stages:
            stage_total = sum(m.weight for m in stage.measurements)
            if len(stage.measurements) > 1 and abs(stage_total - 1.0) > 0.01:
                errors.append(f"阶段 '{stage.name}' 测量权重总和 {stage_total:.2f} 不等于 1.0")
        
        return errors


# 全局配置管理器实例
config_manager = EvaluationConfigManager()


def get_config_manager() -> EvaluationConfigManager:
    """获取配置管理器实例"""
    return config_manager


def get_badminton_clear_config() -> ActionSpec:
    """获取羽毛球正手高远球配置（兼容接口）"""
    return config_manager.get_action_config("badminton", "clear")
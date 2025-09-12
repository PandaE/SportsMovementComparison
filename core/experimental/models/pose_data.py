"""
Pose data models for frame analysis.
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class PoseKeypoint:
    """单个关键点的姿态数据"""
    x: float
    y: float
    z: float = 0.0  # 可选的深度信息
    confidence: float = 1.0
    
    def to_tuple(self) -> Tuple[float, float]:
        """返回2D坐标"""
        return (self.x, self.y)
    
    def to_array(self) -> np.ndarray:
        """返回numpy数组格式"""
        return np.array([self.x, self.y, self.z])


@dataclass
class BodyPose:
    """完整的人体姿态数据"""
    # 主要关键点 (基于MediaPipe或类似框架)
    nose: Optional[PoseKeypoint] = None
    left_shoulder: Optional[PoseKeypoint] = None
    right_shoulder: Optional[PoseKeypoint] = None
    left_elbow: Optional[PoseKeypoint] = None
    right_elbow: Optional[PoseKeypoint] = None
    left_wrist: Optional[PoseKeypoint] = None
    right_wrist: Optional[PoseKeypoint] = None
    left_hip: Optional[PoseKeypoint] = None
    right_hip: Optional[PoseKeypoint] = None
    left_knee: Optional[PoseKeypoint] = None
    right_knee: Optional[PoseKeypoint] = None
    left_ankle: Optional[PoseKeypoint] = None
    right_ankle: Optional[PoseKeypoint] = None
    
    timestamp: float = 0.0  # 时间戳
    frame_index: int = 0    # 帧索引
    
    def get_keypoint(self, name: str) -> Optional[PoseKeypoint]:
        """根据名称获取关键点"""
        return getattr(self, name, None)
    
    def calculate_angle(self, point1_name: str, vertex_name: str, point2_name: str) -> Optional[float]:
        """计算三点间的角度（以vertex为顶点）"""
        point1 = self.get_keypoint(point1_name)
        vertex = self.get_keypoint(vertex_name)
        point2 = self.get_keypoint(point2_name)
        
        if not all([point1, vertex, point2]):
            return None
            
        # 计算向量
        vec1 = np.array([point1.x - vertex.x, point1.y - vertex.y])
        vec2 = np.array([point2.x - vertex.x, point2.y - vertex.y])
        
        # 计算角度
        cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        return np.degrees(angle)


@dataclass
class FrameAnalysis:
    """单帧分析结果"""
    frame_index: int
    pose: BodyPose
    analysis_data: Dict = None  # 存储计算出的角度、距离等
    
    def __post_init__(self):
        if self.analysis_data is None:
            self.analysis_data = {}
    
    def add_measurement(self, name: str, value: float, unit: str = ""):
        """添加测量数据"""
        self.analysis_data[name] = {
            'value': value,
            'unit': unit
        }
    
    def get_measurement(self, name: str) -> Optional[float]:
        """获取测量值"""
        return self.analysis_data.get(name, {}).get('value')
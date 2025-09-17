"""
Pose extraction from images using MediaPipe or other pose detection libraries.
"""
import cv2
import numpy as np
from typing import Optional, List
from ..models.pose_data import PoseKeypoint, BodyPose


class PoseExtractor:
    """姿态提取器 - 从图像中提取人体姿态"""
    
    def __init__(self, backend: str = "mediapipe"):
        """
        初始化姿态提取器
        
        Args:
            backend: 后端选择 ("mediapipe", "openpose", "mock")
        """
        self.backend = backend
        self._init_backend()
    
    def _init_backend(self):
        """初始化后端"""
        if self.backend == "mediapipe":
            try:
                import mediapipe as mp
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=2,
                    enable_segmentation=False,
                    min_detection_confidence=0.5
                )
                self.mp_drawing = mp.solutions.drawing_utils
                print("MediaPipe姿态检测器初始化成功")
            except ImportError:
                print("MediaPipe未安装，切换到模拟模式")
                self.backend = "mock"
        
        if self.backend == "mock":
            print("使用模拟姿态检测器")
    
    def extract_pose_from_image(self, image: np.ndarray, frame_index: int = 0) -> Optional[BodyPose]:
        """
        从图像中提取姿态
        
        Args:
            image: 输入图像 (BGR格式)
            frame_index: 帧索引
            
        Returns:
            BodyPose对象或None
        """
        if self.backend == "mediapipe":
            return self._extract_with_mediapipe(image, frame_index)
        elif self.backend == "mock":
            return self._extract_mock_pose(image, frame_index)
        else:
            raise ValueError(f"不支持的后端: {self.backend}")
    
    def _extract_with_mediapipe(self, image: np.ndarray, frame_index: int) -> Optional[BodyPose]:
        """使用MediaPipe提取姿态"""
        # 转换颜色空间
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 进行姿态检测
        results = self.pose.process(rgb_image)
        
        if not results.pose_landmarks:
            return None
        
        # 提取关键点
        landmarks = results.pose_landmarks.landmark
        h, w = image.shape[:2]
        
        def extract_keypoint(landmark_idx: int) -> Optional[PoseKeypoint]:
            if landmark_idx < len(landmarks):
                lm = landmarks[landmark_idx]
                return PoseKeypoint(
                    x=lm.x * w,
                    y=lm.y * h, 
                    z=lm.z,
                    confidence=lm.visibility
                )
            return None
        
        # MediaPipe pose landmark indices
        pose = BodyPose(
            nose=extract_keypoint(0),
            left_shoulder=extract_keypoint(11),
            right_shoulder=extract_keypoint(12),
            left_elbow=extract_keypoint(13),
            right_elbow=extract_keypoint(14),
            left_wrist=extract_keypoint(15),
            right_wrist=extract_keypoint(16),
            left_hip=extract_keypoint(23),
            right_hip=extract_keypoint(24),
            left_knee=extract_keypoint(25),
            right_knee=extract_keypoint(26),
            left_ankle=extract_keypoint(27),
            right_ankle=extract_keypoint(28),
            frame_index=frame_index
        )
        
        return pose
    
    def _extract_mock_pose(self, image: np.ndarray, frame_index: int) -> BodyPose:
        """生成模拟姿态数据（用于测试）"""
        h, w = image.shape[:2]
        
        # 生成合理的模拟关键点位置
        center_x, center_y = w // 2, h // 2
        
        # 模拟一个标准的站立姿态
        mock_pose = BodyPose(
            nose=PoseKeypoint(center_x, center_y - h * 0.3, confidence=0.9),
            left_shoulder=PoseKeypoint(center_x - w * 0.1, center_y - h * 0.2, confidence=0.9),
            right_shoulder=PoseKeypoint(center_x + w * 0.1, center_y - h * 0.2, confidence=0.9),
            left_elbow=PoseKeypoint(center_x - w * 0.15, center_y - h * 0.05, confidence=0.9),
            right_elbow=PoseKeypoint(center_x + w * 0.15, center_y - h * 0.05, confidence=0.9),
            left_wrist=PoseKeypoint(center_x - w * 0.2, center_y + h * 0.1, confidence=0.9),
            right_wrist=PoseKeypoint(center_x + w * 0.2, center_y + h * 0.1, confidence=0.9),
            left_hip=PoseKeypoint(center_x - w * 0.08, center_y + h * 0.05, confidence=0.9),
            right_hip=PoseKeypoint(center_x + w * 0.08, center_y + h * 0.05, confidence=0.9),
            left_knee=PoseKeypoint(center_x - w * 0.05, center_y + h * 0.25, confidence=0.9),
            right_knee=PoseKeypoint(center_x + w * 0.05, center_y + h * 0.25, confidence=0.9),
            left_ankle=PoseKeypoint(center_x - w * 0.03, center_y + h * 0.45, confidence=0.9),
            right_ankle=PoseKeypoint(center_x + w * 0.03, center_y + h * 0.45, confidence=0.9),
            frame_index=frame_index
        )
        
        return mock_pose
    
    def visualize_pose(self, image: np.ndarray, pose: BodyPose, color: tuple = (0, 255, 0)) -> np.ndarray:
        """在图像上可视化姿态"""
        vis_image = image.copy()
        
        # 绘制关键点
        keypoints = [
            ('nose', pose.nose),
            ('left_shoulder', pose.left_shoulder),
            ('right_shoulder', pose.right_shoulder),
            ('left_elbow', pose.left_elbow),
            ('right_elbow', pose.right_elbow),
            ('left_wrist', pose.left_wrist),
            ('right_wrist', pose.right_wrist),
            ('left_hip', pose.left_hip),
            ('right_hip', pose.right_hip),
            ('left_knee', pose.left_knee),
            ('right_knee', pose.right_knee),
            ('left_ankle', pose.left_ankle),
            ('right_ankle', pose.right_ankle)
        ]
        
        # 绘制点
        for name, keypoint in keypoints:
            if keypoint:
                cv2.circle(vis_image, (int(keypoint.x), int(keypoint.y)), 5, color, -1)
                cv2.putText(vis_image, name[:4], (int(keypoint.x), int(keypoint.y-10)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        # 绘制连接线
        connections = [
            (pose.left_shoulder, pose.left_elbow),
            (pose.left_elbow, pose.left_wrist),
            (pose.right_shoulder, pose.right_elbow),
            (pose.right_elbow, pose.right_wrist),
            (pose.left_shoulder, pose.right_shoulder),
            (pose.left_hip, pose.right_hip),
            (pose.left_shoulder, pose.left_hip),
            (pose.right_shoulder, pose.right_hip),
            (pose.left_hip, pose.left_knee),
            (pose.left_knee, pose.left_ankle),
            (pose.right_hip, pose.right_knee),
            (pose.right_knee, pose.right_ankle)
        ]
        
        for pt1, pt2 in connections:
            if pt1 and pt2:
                cv2.line(vis_image, (int(pt1.x), int(pt1.y)), (int(pt2.x), int(pt2.y)), 
                        color, 2)
        
        return vis_image
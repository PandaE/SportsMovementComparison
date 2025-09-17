"""
Pose Detection Module
姿态检测模块

Handles pose detection, keypoint extraction, and pose-based measurements.
"""

import cv2
import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any, NamedTuple
from dataclasses import dataclass


@dataclass
class PoseKeypoint:
    """Pose keypoint data structure"""
    x: float
    y: float
    confidence: float = 1.0


@dataclass
class BodyPose:
    """Body pose data structure"""
    # Head
    nose: Optional[PoseKeypoint] = None
    
    # Upper body
    left_shoulder: Optional[PoseKeypoint] = None
    right_shoulder: Optional[PoseKeypoint] = None
    left_elbow: Optional[PoseKeypoint] = None
    right_elbow: Optional[PoseKeypoint] = None
    left_wrist: Optional[PoseKeypoint] = None
    right_wrist: Optional[PoseKeypoint] = None
    
    # Lower body
    left_hip: Optional[PoseKeypoint] = None
    right_hip: Optional[PoseKeypoint] = None
    left_knee: Optional[PoseKeypoint] = None
    right_knee: Optional[PoseKeypoint] = None
    left_ankle: Optional[PoseKeypoint] = None
    right_ankle: Optional[PoseKeypoint] = None


class PoseDetector:
    """
    Pose detection and analysis utility.
    姿态检测和分析工具
    """
    
    def __init__(self, backend: str = "mediapipe"):
        """
        Initialize pose detector.
        
        Args:
            backend: Detection backend ("mediapipe" or "opencv")
        """
        self.backend = backend
        self.detector = None
        self.confidence_threshold = 0.5
        
        self._init_detector()
    
    def _init_detector(self):
        """Initialize the pose detection backend"""
        try:
            if self.backend == "mediapipe":
                self._init_mediapipe()
            elif self.backend == "opencv":
                self._init_opencv()
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        except ImportError as e:
            print(f"Failed to initialize {self.backend} backend: {e}")
            self._init_fallback()
    
    def _init_mediapipe(self):
        """Initialize MediaPipe pose detection"""
        import mediapipe as mp
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.detector = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=self.confidence_threshold
        )
        print("✅ MediaPipe pose detector initialized")
    
    def _init_opencv(self):
        """Initialize OpenCV pose detection (DNN-based)"""
        # This would require a pre-trained pose estimation model
        # For now, we'll use a placeholder
        print("⚠️ OpenCV pose detection not fully implemented")
        self._init_fallback()
    
    def _init_fallback(self):
        """Initialize fallback detection (mock)"""
        self.detector = "fallback"
        print("⚠️ Using fallback pose detection (mock data)")
    
    def detect_pose(self, image: np.ndarray) -> Optional[BodyPose]:
        """
        Detect pose in image.
        在图像中检测姿态
        
        Args:
            image: Input image
            
        Returns:
            BodyPose object or None if detection failed
        """
        if image is None or image.size == 0:
            return None
        
        try:
            if self.backend == "mediapipe" and self.detector:
                return self._detect_mediapipe(image)
            else:
                return self._detect_fallback(image)
        except Exception as e:
            print(f"Pose detection failed: {e}")
            return None
    
    def _detect_mediapipe(self, image: np.ndarray) -> Optional[BodyPose]:
        """Detect pose using MediaPipe"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process image
        results = self.detector.process(rgb_image)
        
        if not results.pose_landmarks:
            return None
        
        # Extract landmarks
        landmarks = results.pose_landmarks.landmark
        h, w = image.shape[:2]
        
        def extract_keypoint(landmark_idx: int) -> Optional[PoseKeypoint]:
            if landmark_idx < len(landmarks):
                lm = landmarks[landmark_idx]
                if lm.visibility > self.confidence_threshold:
                    return PoseKeypoint(
                        x=lm.x * w,
                        y=lm.y * h,
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
            right_ankle=extract_keypoint(28)
        )
        
        return pose
    
    def _detect_fallback(self, image: np.ndarray) -> Optional[BodyPose]:
        """Fallback pose detection (generates mock data)"""
        h, w = image.shape[:2]
        
        # Generate mock pose data for testing
        center_x, center_y = w // 2, h // 2
        
        return BodyPose(
            nose=PoseKeypoint(center_x, center_y - h//4, 0.9),
            left_shoulder=PoseKeypoint(center_x - w//8, center_y - h//6, 0.9),
            right_shoulder=PoseKeypoint(center_x + w//8, center_y - h//6, 0.9),
            left_elbow=PoseKeypoint(center_x - w//6, center_y, 0.8),
            right_elbow=PoseKeypoint(center_x + w//6, center_y, 0.8),
            left_wrist=PoseKeypoint(center_x - w//4, center_y + h//8, 0.8),
            right_wrist=PoseKeypoint(center_x + w//4, center_y + h//8, 0.8),
            left_hip=PoseKeypoint(center_x - w//12, center_y + h//8, 0.9),
            right_hip=PoseKeypoint(center_x + w//12, center_y + h//8, 0.9),
            left_knee=PoseKeypoint(center_x - w//12, center_y + h//4, 0.8),
            right_knee=PoseKeypoint(center_x + w//12, center_y + h//4, 0.8),
            left_ankle=PoseKeypoint(center_x - w//12, center_y + h//3, 0.8),
            right_ankle=PoseKeypoint(center_x + w//12, center_y + h//3, 0.8)
        )
    
    def visualize_pose(self, image: np.ndarray, pose: BodyPose = None) -> np.ndarray:
        """
        Visualize pose on image.
        在图像上可视化姿态
        
        Args:
            image: Input image
            pose: Pose to visualize (detect if None)
            
        Returns:
            Image with pose visualization
        """
        if image is None:
            return image
        
        if pose is None:
            pose = self.detect_pose(image)
        
        if pose is None:
            return image
        
        # Create a copy for visualization
        vis_image = image.copy()
        
        # Draw keypoints
        keypoints = [
            pose.nose, pose.left_shoulder, pose.right_shoulder,
            pose.left_elbow, pose.right_elbow, pose.left_wrist, pose.right_wrist,
            pose.left_hip, pose.right_hip, pose.left_knee, pose.right_knee,
            pose.left_ankle, pose.right_ankle
        ]
        
        # Draw keypoints
        for kp in keypoints:
            if kp and kp.confidence > self.confidence_threshold:
                cv2.circle(vis_image, (int(kp.x), int(kp.y)), 5, (0, 255, 0), -1)
        
        # Draw connections
        connections = [
            # Head to shoulders
            (pose.nose, pose.left_shoulder),
            (pose.nose, pose.right_shoulder),
            # Arms
            (pose.left_shoulder, pose.left_elbow),
            (pose.left_elbow, pose.left_wrist),
            (pose.right_shoulder, pose.right_elbow),
            (pose.right_elbow, pose.right_wrist),
            # Torso
            (pose.left_shoulder, pose.right_shoulder),
            (pose.left_shoulder, pose.left_hip),
            (pose.right_shoulder, pose.right_hip),
            (pose.left_hip, pose.right_hip),
            # Legs
            (pose.left_hip, pose.left_knee),
            (pose.left_knee, pose.left_ankle),
            (pose.right_hip, pose.right_knee),
            (pose.right_knee, pose.right_ankle)
        ]
        
        for start_kp, end_kp in connections:
            if (start_kp and end_kp and 
                start_kp.confidence > self.confidence_threshold and 
                end_kp.confidence > self.confidence_threshold):
                
                start_point = (int(start_kp.x), int(start_kp.y))
                end_point = (int(end_kp.x), int(end_kp.y))
                cv2.line(vis_image, start_point, end_point, (255, 0, 0), 2)
        
        return vis_image
    
    def calculate_angle(self, point1: PoseKeypoint, point2: PoseKeypoint, 
                       point3: PoseKeypoint) -> Optional[float]:
        """
        Calculate angle between three points.
        计算三点之间的角度
        
        Args:
            point1: First point
            point2: Vertex point
            point3: Third point
            
        Returns:
            Angle in degrees or None if calculation failed
        """
        if not all([point1, point2, point3]):
            return None
        
        if any(kp.confidence < self.confidence_threshold for kp in [point1, point2, point3]):
            return None
        
        # Calculate vectors
        v1 = np.array([point1.x - point2.x, point1.y - point2.y])
        v2 = np.array([point3.x - point2.x, point3.y - point2.y])
        
        # Calculate angle
        try:
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)  # Clamp to valid range
            angle = np.arccos(cos_angle)
            return math.degrees(angle)
        except:
            return None
    
    def calculate_distance(self, point1: PoseKeypoint, point2: PoseKeypoint) -> Optional[float]:
        """
        Calculate distance between two points.
        计算两点之间的距离
        
        Args:
            point1: First point
            point2: Second point
            
        Returns:
            Distance or None if calculation failed
        """
        if not all([point1, point2]):
            return None
        
        if any(kp.confidence < self.confidence_threshold for kp in [point1, point2]):
            return None
        
        dx = point1.x - point2.x
        dy = point1.y - point2.y
        return math.sqrt(dx * dx + dy * dy)
    
    def calculate_measurement(self, user_pose: BodyPose, standard_pose: BodyPose, 
                            measurement_config: Dict) -> Dict[str, Any]:
        """
        Calculate specific measurement between two poses.
        计算两个姿态之间的特定测量
        
        Args:
            user_pose: User's pose
            standard_pose: Standard reference pose
            measurement_config: Measurement configuration
            
        Returns:
            Measurement result dictionary
        """
        measurement_type = measurement_config.get('type', 'angle')
        keypoints = measurement_config.get('keypoints', [])
        tolerance = measurement_config.get('tolerance', 10.0)
        
        result = {
            'name': measurement_config.get('name', 'Unknown'),
            'type': measurement_type,
            'user_value': None,
            'standard_value': None,
            'difference': None,
            'score': 0.0,
            'is_within_tolerance': False
        }
        
        try:
            if measurement_type == 'angle' and len(keypoints) == 3:
                # Get keypoints from poses
                user_kps = [self._get_keypoint(user_pose, kp_name) for kp_name in keypoints]
                standard_kps = [self._get_keypoint(standard_pose, kp_name) for kp_name in keypoints]
                
                if all(user_kps) and all(standard_kps):
                    user_angle = self.calculate_angle(*user_kps)
                    standard_angle = self.calculate_angle(*standard_kps)
                    
                    if user_angle is not None and standard_angle is not None:
                        result['user_value'] = user_angle
                        result['standard_value'] = standard_angle
                        result['difference'] = abs(user_angle - standard_angle)
                        result['is_within_tolerance'] = result['difference'] <= tolerance
                        
                        # Calculate score based on difference
                        if result['difference'] <= tolerance:
                            result['score'] = 1.0
                        else:
                            result['score'] = max(0.0, 1.0 - (result['difference'] - tolerance) / tolerance)
            
            elif measurement_type == 'distance' and len(keypoints) == 2:
                # Similar logic for distance measurements
                user_kps = [self._get_keypoint(user_pose, kp_name) for kp_name in keypoints]
                standard_kps = [self._get_keypoint(standard_pose, kp_name) for kp_name in keypoints]
                
                if all(user_kps) and all(standard_kps):
                    user_dist = self.calculate_distance(*user_kps)
                    standard_dist = self.calculate_distance(*standard_kps)
                    
                    if user_dist is not None and standard_dist is not None:
                        result['user_value'] = user_dist
                        result['standard_value'] = standard_dist
                        
                        # Normalize by image size for comparison
                        if standard_dist > 0:
                            relative_diff = abs(user_dist - standard_dist) / standard_dist
                            result['difference'] = relative_diff
                            result['is_within_tolerance'] = relative_diff <= (tolerance / 100.0)
                            result['score'] = max(0.0, 1.0 - relative_diff)
        
        except Exception as e:
            print(f"Measurement calculation failed: {e}")
        
        return result
    
    def _get_keypoint(self, pose: BodyPose, keypoint_name: str) -> Optional[PoseKeypoint]:
        """Get keypoint by name from pose"""
        keypoint_map = {
            'nose': pose.nose,
            'left_shoulder': pose.left_shoulder,
            'right_shoulder': pose.right_shoulder,
            'left_elbow': pose.left_elbow,
            'right_elbow': pose.right_elbow,
            'left_wrist': pose.left_wrist,
            'right_wrist': pose.right_wrist,
            'left_hip': pose.left_hip,
            'right_hip': pose.right_hip,
            'left_knee': pose.left_knee,
            'right_knee': pose.right_knee,
            'left_ankle': pose.left_ankle,
            'right_ankle': pose.right_ankle
        }
        
        return keypoint_map.get(keypoint_name)
    
    def update_settings(self, settings: Dict[str, Any]):
        """Update detector settings"""
        if 'pose_backend' in settings and settings['pose_backend'] != self.backend:
            self.backend = settings['pose_backend']
            self._init_detector()
        
        if 'confidence_threshold' in settings:
            self.confidence_threshold = settings['confidence_threshold']
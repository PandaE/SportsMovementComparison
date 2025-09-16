"""
Image processing utilities.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from ..experimental.models.pose_data import BodyPose, PoseKeypoint


class ImageUtils:
    """图像处理工具类"""
    
    @staticmethod
    def resize_image(image: np.ndarray, target_size: Tuple[int, int], 
                    keep_aspect_ratio: bool = True) -> np.ndarray:
        """
        调整图像尺寸
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            keep_aspect_ratio: 是否保持宽高比
            
        Returns:
            调整后的图像
        """
        if not keep_aspect_ratio:
            return cv2.resize(image, target_size)
        
        h, w = image.shape[:2]
        target_w, target_h = target_size
        
        # 计算缩放比例
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # 调整尺寸
        resized = cv2.resize(image, (new_w, new_h))
        
        # 创建目标尺寸的图像并居中放置
        result = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        y_offset = (target_h - new_h) // 2
        x_offset = (target_w - new_w) // 2
        result[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return result
    
    @staticmethod
    def extract_frame_from_video(video_path: str, frame_index: int) -> Optional[np.ndarray]:
        """
        从视频中提取指定帧
        
        Args:
            video_path: 视频文件路径
            frame_index: 帧索引
            
        Returns:
            图像帧或None
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return None
        
        # 设置帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    @staticmethod
    def create_side_by_side_image(img1: np.ndarray, img2: np.ndarray, 
                                labels: Tuple[str, str] = None) -> np.ndarray:
        """
        创建并排对比图像
        
        Args:
            img1: 左侧图像
            img2: 右侧图像
            labels: 图像标签 (左, 右)
            
        Returns:
            并排拼接的图像
        """
        # 统一尺寸
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        target_h = max(h1, h2)
        target_w = max(w1, w2)
        
        img1_resized = ImageUtils.resize_image(img1, (target_w, target_h))
        img2_resized = ImageUtils.resize_image(img2, (target_w, target_h))
        
        # 水平拼接
        result = np.hstack([img1_resized, img2_resized])
        
        # 添加标签
        if labels:
            cv2.putText(result, labels[0], (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(result, labels[1], (target_w + 10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        return result
    
    @staticmethod
    def add_text_overlay(image: np.ndarray, text: str, 
                        position: Tuple[int, int] = (10, 30),
                        font_scale: float = 0.7,
                        color: Tuple[int, int, int] = (255, 255, 255),
                        thickness: int = 2) -> np.ndarray:
        """
        在图像上添加文字覆盖层
        
        Args:
            image: 输入图像
            text: 要添加的文字
            position: 文字位置 (x, y)
            font_scale: 字体大小
            color: 文字颜色 (B, G, R)
            thickness: 线条粗细
            
        Returns:
            添加文字后的图像
        """
        result = image.copy()
        cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, thickness)
        return result
    
    @staticmethod
    def draw_stick_figure(image: np.ndarray, pose: BodyPose, 
                         color: Tuple[int, int, int] = (0, 255, 0),
                         thickness: int = 2,
                         point_radius: int = 4,
                         confidence_threshold: float = 0.5) -> np.ndarray:
        """
        在图像上绘制火柴人姿态
        
        Args:
            image: 输入图像
            pose: 姿态数据
            color: 绘制颜色 (B, G, R)
            thickness: 线条粗细
            point_radius: 关键点半径
            confidence_threshold: 置信度阈值，低于此值的点不绘制
            
        Returns:
            绘制火柴人后的图像
        """
        if not pose:
            return image
        
        result = image.copy()
        
        # 定义骨骼连接
        connections = [
            # 头部到躯干
            ('nose', 'left_shoulder'),
            ('nose', 'right_shoulder'),
            
            # 躯干
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            
            # 左臂
            ('left_shoulder', 'left_elbow'),
            ('left_elbow', 'left_wrist'),
            
            # 右臂
            ('right_shoulder', 'right_elbow'),
            ('right_elbow', 'right_wrist'),
            
            # 左腿
            ('left_hip', 'left_knee'),
            ('left_knee', 'left_ankle'),
            
            # 右腿
            ('right_hip', 'right_knee'),
            ('right_knee', 'right_ankle')
        ]
        
        # 绘制连接线
        for start_name, end_name in connections:
            start_point = pose.get_keypoint(start_name)
            end_point = pose.get_keypoint(end_name)
            
            if (start_point and end_point and 
                start_point.confidence >= confidence_threshold and 
                end_point.confidence >= confidence_threshold):
                
                start_pos = (int(start_point.x), int(start_point.y))
                end_pos = (int(end_point.x), int(end_point.y))
                
                cv2.line(result, start_pos, end_pos, color, thickness)
        
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
        
        for name, keypoint in keypoints:
            if keypoint and keypoint.confidence >= confidence_threshold:
                pos = (int(keypoint.x), int(keypoint.y))
                cv2.circle(result, pos, point_radius, color, -1)
                
                # 可选：添加关键点标签（调试用）
                # cv2.putText(result, name[:4], (pos[0], pos[1]-10), 
                #            cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        return result
    
    @staticmethod
    def create_pose_preview_image(image: np.ndarray, pose: BodyPose = None,
                                 title: str = "", 
                                 target_size: Tuple[int, int] = (200, 150)) -> np.ndarray:
        """
        创建带有姿态预览的缩略图
        
        Args:
            image: 原始图像
            pose: 姿态数据（可选）
            title: 图像标题
            target_size: 目标尺寸
            
        Returns:
            带有火柴人的预览图像
        """
        # 调整图像尺寸
        preview_img = ImageUtils.resize_image(image, target_size, keep_aspect_ratio=True)
        
        # 如果有姿态数据，绘制火柴人
        if pose:
            # 计算缩放比例以适配调整后的图像
            h_orig, w_orig = image.shape[:2]
            h_new, w_new = preview_img.shape[:2]
            
            # 创建缩放后的姿态副本
            scaled_pose = ImageUtils._scale_pose(pose, w_orig, h_orig, w_new, h_new)
            preview_img = ImageUtils.draw_stick_figure(preview_img, scaled_pose, 
                                                      color=(0, 255, 0), thickness=2)
        
        # 添加标题
        if title:
            preview_img = ImageUtils.add_text_overlay(preview_img, title, 
                                                     position=(5, 15), 
                                                     font_scale=0.4, 
                                                     color=(255, 255, 255))
        
        return preview_img
    
    @staticmethod
    def _scale_pose(pose: BodyPose, orig_w: int, orig_h: int, 
                   new_w: int, new_h: int) -> BodyPose:
        """
        缩放姿态数据以适配新的图像尺寸
        
        Args:
            pose: 原始姿态
            orig_w, orig_h: 原始图像尺寸
            new_w, new_h: 新图像尺寸
            
        Returns:
            缩放后的姿态
        """
        if not pose:
            return pose
        
        # 计算实际的缩放和偏移
        scale = min(new_w / orig_w, new_h / orig_h)
        scaled_w, scaled_h = int(orig_w * scale), int(orig_h * scale)
        x_offset = (new_w - scaled_w) // 2
        y_offset = (new_h - scaled_h) // 2
        
        def scale_keypoint(kp: PoseKeypoint) -> PoseKeypoint:
            if not kp:
                return kp
            return PoseKeypoint(
                x=kp.x * scale + x_offset,
                y=kp.y * scale + y_offset,
                z=kp.z,
                confidence=kp.confidence
            )
        
        # 创建缩放后的姿态
        from ..experimental.models.pose_data import BodyPose
        scaled_pose = BodyPose(
            nose=scale_keypoint(pose.nose),
            left_shoulder=scale_keypoint(pose.left_shoulder),
            right_shoulder=scale_keypoint(pose.right_shoulder),
            left_elbow=scale_keypoint(pose.left_elbow),
            right_elbow=scale_keypoint(pose.right_elbow),
            left_wrist=scale_keypoint(pose.left_wrist),
            right_wrist=scale_keypoint(pose.right_wrist),
            left_hip=scale_keypoint(pose.left_hip),
            right_hip=scale_keypoint(pose.right_hip),
            left_knee=scale_keypoint(pose.left_knee),
            right_knee=scale_keypoint(pose.right_knee),
            left_ankle=scale_keypoint(pose.left_ankle),
            right_ankle=scale_keypoint(pose.right_ankle),
            frame_index=pose.frame_index
        )
        
        return scaled_pose
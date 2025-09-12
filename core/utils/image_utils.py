"""
Image processing utilities.
"""
import cv2
import numpy as np
from typing import Tuple, Optional


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
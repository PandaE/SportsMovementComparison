"""
video_frame_extractor.py
视频关键帧提取和图像处理工具
"""
import cv2
import numpy as np
import os
from typing import List, Tuple, Optional
from pathlib import Path


class VideoFrameExtractor:
    """视频帧提取器"""
    
    def __init__(self):
        """初始化提取器"""
        pass
    
    def extract_key_frames(self, video_path: str, method: str = "uniform", 
                          num_frames: int = 5) -> List[Tuple[np.ndarray, int]]:
        """
        提取关键帧
        
        Args:
            video_path: 视频文件路径
            method: 提取方法 ("uniform", "middle", "motion_based")
            num_frames: 提取帧数
            
        Returns:
            List of (frame, frame_index) tuples
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        if method == "uniform":
            frame_indices = self._get_uniform_indices(total_frames, num_frames)
        elif method == "middle":
            frame_indices = [total_frames // 2]
        elif method == "motion_based":
            frame_indices = self._get_motion_based_indices(cap, num_frames)
        else:
            raise ValueError(f"不支持的提取方法: {method}")
        
        frames = []
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frames.append((frame, frame_idx))
        
        cap.release()
        return frames
    
    def _get_uniform_indices(self, total_frames: int, num_frames: int) -> List[int]:
        """获取均匀分布的帧索引"""
        if num_frames >= total_frames:
            return list(range(total_frames))
        
        step = total_frames / num_frames
        return [int(i * step) for i in range(num_frames)]
    
    def _get_motion_based_indices(self, cap: cv2.VideoCapture, num_frames: int) -> List[int]:
        """基于运动检测的关键帧提取"""
        motion_scores = []
        prev_frame = None
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # 计算光流或帧差
                diff = cv2.absdiff(prev_frame, gray)
                motion_score = np.mean(diff)
                motion_scores.append((frame_idx, motion_score))
            
            prev_frame = gray
            frame_idx += 1
        
        # 重置视频位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 选择运动最明显的帧
        motion_scores.sort(key=lambda x: x[1], reverse=True)
        selected_indices = [idx for idx, score in motion_scores[:num_frames]]
        selected_indices.sort()
        
        return selected_indices
    
    def extract_frame_at_time(self, video_path: str, time_seconds: float) -> Optional[np.ndarray]:
        """在指定时间提取帧"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(time_seconds * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    def save_frames_as_images(self, frames: List[Tuple[np.ndarray, int]], 
                             output_dir: str, prefix: str = "frame") -> List[str]:
        """保存帧为图片文件"""
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        
        for i, (frame, frame_idx) in enumerate(frames):
            filename = f"{prefix}_{frame_idx:04d}.jpg"
            filepath = os.path.join(output_dir, filename)
            cv2.imwrite(filepath, frame)
            saved_paths.append(filepath)
        
        return saved_paths
    
    def enhance_frame_quality(self, frame: np.ndarray) -> np.ndarray:
        """增强帧质量"""
        # 去噪
        denoised = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
        
        # 锐化
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # 对比度增强
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_channel = clahe.apply(l_channel)
        enhanced = cv2.merge((l_channel, a, b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def get_video_info(self, video_path: str) -> dict:
        """获取视频信息"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}
        
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info


class FrameQualityAssessor:
    """帧质量评估器"""
    
    @staticmethod
    def assess_blur(frame: np.ndarray) -> float:
        """评估模糊度（越高越清晰）"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    @staticmethod
    def assess_brightness(frame: np.ndarray) -> float:
        """评估亮度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)
    
    @staticmethod
    def assess_contrast(frame: np.ndarray) -> float:
        """评估对比度"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return np.std(gray)
    
    @staticmethod
    def assess_overall_quality(frame: np.ndarray) -> dict:
        """综合质量评估"""
        blur_score = FrameQualityAssessor.assess_blur(frame)
        brightness = FrameQualityAssessor.assess_brightness(frame)
        contrast = FrameQualityAssessor.assess_contrast(frame)
        
        # 标准化分数 (0-1)
        blur_normalized = min(blur_score / 1000, 1.0)  # 假设1000为高质量阈值
        brightness_normalized = 1.0 - abs(brightness - 127.5) / 127.5  # 理想亮度127.5
        contrast_normalized = min(contrast / 64, 1.0)  # 假设64为好对比度
        
        overall_score = (blur_normalized * 0.5 + brightness_normalized * 0.2 + contrast_normalized * 0.3)
        
        return {
            'blur_score': blur_score,
            'brightness': brightness,
            'contrast': contrast,
            'overall_quality': overall_score,
            'is_good_quality': overall_score > 0.6
        }


class SmartFrameSelector:
    """智能帧选择器"""
    
    def __init__(self):
        self.extractor = VideoFrameExtractor()
        self.assessor = FrameQualityAssessor()
    
    def select_best_frames_for_pose(self, video_path: str, target_phases: List[str], 
                                   max_frames: int = 3) -> List[Tuple[np.ndarray, int, str]]:
        """
        为姿态分析选择最佳帧
        
        Args:
            video_path: 视频路径
            target_phases: 目标动作阶段 ["preparation", "execution", "follow_through"]
            max_frames: 最大帧数
            
        Returns:
            List of (frame, frame_index, phase) tuples
        """
        # 首先提取候选帧
        candidate_frames = self.extractor.extract_key_frames(video_path, "uniform", max_frames * 3)
        
        # 评估每帧质量
        quality_frames = []
        for frame, frame_idx in candidate_frames:
            quality = self.assessor.assess_overall_quality(frame)
            if quality['is_good_quality']:
                quality_frames.append((frame, frame_idx, quality['overall_quality']))
        
        # 按质量排序并选择最佳帧
        quality_frames.sort(key=lambda x: x[2], reverse=True)
        
        selected_frames = []
        video_info = self.extractor.get_video_info(video_path)
        total_frames = video_info.get('total_frames', 1)
        
        # 根据帧位置分配阶段
        for i, (frame, frame_idx, quality) in enumerate(quality_frames[:max_frames]):
            position_ratio = frame_idx / total_frames
            
            if position_ratio < 0.3:
                phase = "preparation"
            elif position_ratio < 0.7:
                phase = "execution"
            else:
                phase = "follow_through"
            
            if not target_phases or phase in target_phases:
                selected_frames.append((frame, frame_idx, phase))
        
        return selected_frames
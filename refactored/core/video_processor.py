"""
Video Processing Module
视频处理模块

Handles video import, frame extraction, quality assessment, and preprocessing.
"""

import cv2
import numpy as np
import os
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from config.settings import AppSettings


class VideoProcessor:
    """
    Video processing and frame extraction utility.
    视频处理和帧提取工具
    """
    
    def __init__(self):
        """Initialize video processor"""
        self.quality_threshold = AppSettings.DEFAULT_SETTINGS['video_quality_check']
        
    def validate_video(self, video_path: str) -> Tuple[bool, str]:
        """
        Validate video file.
        验证视频文件
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(video_path):
            return False, "Video file does not exist"
        
        # Check file extension
        ext = Path(video_path).suffix.lower()
        if ext not in AppSettings.SUPPORTED_VIDEO_FORMATS:
            return False, f"Unsupported video format: {ext}"
        
        # Check if video can be opened
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            return False, "Cannot open video file"
        
        # Check video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        # Validate duration
        if duration > AppSettings.MAX_VIDEO_DURATION:
            return False, f"Video too long: {duration:.1f}s (max: {AppSettings.MAX_VIDEO_DURATION}s)"
        
        if duration < 1.0:
            return False, "Video too short (minimum: 1 second)"
        
        return True, "Video is valid"
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information.
        获取视频信息
        
        Args:
            video_path: Path to video file
            
        Returns:
            Video information dictionary
        """
        if not os.path.exists(video_path):
            return {'error': 'File does not exist'}
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {'error': 'Cannot open video'}
        
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': 0,
            'file_size': os.path.getsize(video_path),
            'format': Path(video_path).suffix.lower()
        }
        
        if info['fps'] > 0:
            info['duration'] = info['frame_count'] / info['fps']
        
        cap.release()
        return info
    
    def extract_frame(self, video_path: str, frame_number: int) -> Optional[np.ndarray]:
        """
        Extract specific frame from video.
        从视频中提取指定帧
        
        Args:
            video_path: Path to video file
            frame_number: Frame number to extract
            
        Returns:
            Frame as numpy array or None if failed
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        return frame if ret else None
    
    def extract_frames_at_times(self, video_path: str, time_points: List[float]) -> List[Tuple[float, np.ndarray]]:
        """
        Extract frames at specific time points.
        在指定时间点提取帧
        
        Args:
            video_path: Path to video file
            time_points: List of time points in seconds
            
        Returns:
            List of (time, frame) tuples
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        
        for time_point in time_points:
            frame_number = int(time_point * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                frames.append((time_point, frame))
        
        cap.release()
        return frames
    
    def extract_key_frames(self, video_path: str, sport: str, action: str, 
                          num_stages: int = 5) -> Dict[str, np.ndarray]:
        """
        Extract key frames for movement analysis.
        提取用于运动分析的关键帧
        
        Args:
            video_path: Path to video file
            sport: Sport type
            action: Action type
            num_stages: Number of movement stages
            
        Returns:
            Dictionary mapping stage names to frames
        """
        # Get stage definitions
        stage_names = self._get_stage_names(sport, action, num_stages)
        
        # Calculate time points for each stage
        info = self.get_video_info(video_path)
        if 'error' in info:
            return {}
        
        duration = info['duration']
        time_points = []
        
        for i in range(num_stages):
            # Distribute stages evenly across video duration
            time_point = (i + 1) * duration / (num_stages + 1)
            time_points.append(time_point)
        
        # Extract frames
        frame_data = self.extract_frames_at_times(video_path, time_points)
        
        # Map to stage names
        key_frames = {}
        for i, (time_point, frame) in enumerate(frame_data):
            if i < len(stage_names):
                stage_name = stage_names[i]
                key_frames[stage_name] = frame
        
        return key_frames
    
    def _get_stage_names(self, sport: str, action: str, num_stages: int) -> List[str]:
        """Get stage names for sport and action"""
        # Default stage names for badminton clear shot
        if sport == "badminton" and action == "clear":
            return [
                "准备阶段",
                "引拍阶段", 
                "发力阶段",
                "击球瞬间",
                "随挥阶段"
            ][:num_stages]
        
        # Generic stage names
        return [f"阶段{i+1}" for i in range(num_stages)]
    
    def assess_frame_quality(self, frame: np.ndarray) -> Dict[str, float]:
        """
        Assess frame quality metrics.
        评估帧质量指标
        
        Args:
            frame: Frame as numpy array
            
        Returns:
            Quality metrics dictionary
        """
        if frame is None or frame.size == 0:
            return {'error': 'Invalid frame'}
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # Calculate metrics
        metrics = {}
        
        # 1. Sharpness (using Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        metrics['sharpness'] = laplacian.var()
        
        # 2. Brightness
        metrics['brightness'] = np.mean(gray) / 255.0
        
        # 3. Contrast (standard deviation)
        metrics['contrast'] = np.std(gray) / 255.0
        
        # 4. Overall quality score
        sharpness_score = min(1.0, metrics['sharpness'] / 500.0)  # Normalize
        brightness_score = 1.0 - abs(metrics['brightness'] - 0.5) * 2  # Optimal around 0.5
        contrast_score = min(1.0, metrics['contrast'] * 4)  # Higher contrast is better
        
        metrics['overall_quality'] = (sharpness_score + brightness_score + contrast_score) / 3.0
        
        return metrics
    
    def enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance frame quality for analysis.
        增强帧质量用于分析
        
        Args:
            frame: Input frame
            
        Returns:
            Enhanced frame
        """
        if frame is None:
            return frame
        
        # Create a copy to avoid modifying original
        enhanced = frame.copy()
        
        # 1. Noise reduction
        enhanced = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # 2. Contrast enhancement
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        return enhanced
    
    def resize_frame(self, frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Resize frame while maintaining aspect ratio.
        调整帧大小并保持宽高比
        
        Args:
            frame: Input frame
            target_size: Target (width, height)
            
        Returns:
            Resized frame
        """
        if frame is None:
            return frame
        
        h, w = frame.shape[:2]
        target_w, target_h = target_size
        
        # Calculate scaling factor
        scale = min(target_w / w, target_h / h)
        
        # Calculate new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Add padding if necessary
        if new_w != target_w or new_h != target_h:
            # Create black background
            padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
            
            # Calculate position to center the image
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            
            # Place resized image in center
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return padded
        
        return resized
    
    def extract_thumbnail(self, video_path: str, time_point: float = None) -> Optional[np.ndarray]:
        """
        Extract thumbnail from video.
        从视频中提取缩略图
        
        Args:
            video_path: Path to video file
            time_point: Time point in seconds (middle if None)
            
        Returns:
            Thumbnail frame
        """
        if time_point is None:
            # Use middle of video
            info = self.get_video_info(video_path)
            if 'error' in info:
                return None
            time_point = info['duration'] / 2
        
        # Extract frame at time point
        frames = self.extract_frames_at_times(video_path, [time_point])
        if not frames:
            return None
        
        _, frame = frames[0]
        
        # Resize to thumbnail size
        thumbnail_size = (160, 120)  # Standard thumbnail size
        return self.resize_frame(frame, thumbnail_size)
    
    def save_frame(self, frame: np.ndarray, output_path: str) -> bool:
        """
        Save frame to file.
        保存帧到文件
        
        Args:
            frame: Frame to save
            output_path: Output file path
            
        Returns:
            Success status
        """
        try:
            return cv2.imwrite(output_path, frame)
        except Exception as e:
            print(f"Failed to save frame: {e}")
            return False
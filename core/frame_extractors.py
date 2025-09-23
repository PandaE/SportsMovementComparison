import os
import cv2
from typing import List, Dict, Any, Optional
from .frame_extraction_config import get_preconfig_keyframes, get_stage_count

class ExtractedFrame:
    def __init__(self, frame_index: int, timestamp: float, label: Optional[str] = None):
        self.frame_index = frame_index
        self.timestamp = timestamp
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        return {'frame_index': self.frame_index, 'timestamp': self.timestamp, 'label': self.label}


class PreconfiguredFrameExtractor:
    """预配置帧提取器: 传入 sport/action/video_basename
    返回事先配置好的关键帧（帧号 + label），并计算时间戳
    """
    def extract(self, sport: str, action: str, video_path: str) -> List[ExtractedFrame]:
        basename = os.path.basename(video_path)
        predefined = get_preconfig_keyframes(sport, action, basename)
        if not predefined:
            return []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        results: List[ExtractedFrame] = []
        for item in predefined:
            fi = int(item.get('frame', 0))
            ts = fi / fps if fps > 0 else 0.0
            results.append(ExtractedFrame(frame_index=fi, timestamp=ts, label=item.get('label')))
        cap.release()
        return results


class EvenlySpacedFrameExtractor:
    """均分帧提取器: 根据配置阶段数量，均匀选取对应数量关键帧
    - 读取视频帧总数与 FPS
    - 按阶段数量将 [0, total_frames-1] 均分成 N 段，取每段中心帧
    """
    def extract(self, sport: str, action: str, video_path: str) -> List[ExtractedFrame]:
        stage_count = get_stage_count(sport, action)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        if total_frames <= 0 or stage_count <= 0:
            cap.release(); return []
        # 计算每段的范围
        segment_length = total_frames / stage_count
        frames: List[ExtractedFrame] = []
        for i in range(stage_count):
            center = int(segment_length * (i + 0.5))
            if center >= total_frames:
                center = total_frames - 1
            timestamp = center / fps if fps > 0 else 0.0
            frames.append(ExtractedFrame(frame_index=center, timestamp=timestamp, label=f'Stage {i+1}'))
        cap.release()
        return frames

__all__ = [
    'ExtractedFrame',
    'PreconfiguredFrameExtractor',
    'EvenlySpacedFrameExtractor'
]

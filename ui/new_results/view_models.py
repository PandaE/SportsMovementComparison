from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union

@dataclass
class FrameRef:
    frame_index: int
    video_path: str

@dataclass
class MetricVM:
    key: str
    name: str
    user_value: Union[float, int, None]
    std_value: Union[float, int, None]
    unit: Optional[str] = None
    deviation: Union[float, int, None] = None
    status: str = 'na'  # ok | warn | bad | na

@dataclass
class StageVM:
    key: str
    name: str
    score: int  # 0-100
    summary_raw: Optional[str] = None
    suggestion: Optional[str] = None
    metrics: List[MetricVM] = field(default_factory=list)
    user_frame: Optional[FrameRef] = None
    standard_frame: Optional[FrameRef] = None

@dataclass
class TrainingVM:
    key_issues: List[str] = field(default_factory=list)
    improvement_drills: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

@dataclass
class VideoInfo:
    user_video_path: Optional[str] = None
    standard_video_path: Optional[str] = None

@dataclass
class ActionEvaluationVM:
    sport: str
    action_name: str
    score: int  # 0-100
    summary_raw: Optional[str] = None
    summary_refined: Optional[str] = None
    stages: List[StageVM] = field(default_factory=list)
    training: Optional[TrainingVM] = None
    video: Optional[VideoInfo] = None

__all__ = [
    'ActionEvaluationVM', 'StageVM', 'MetricVM', 'TrainingVM', 'FrameRef', 'VideoInfo'
]

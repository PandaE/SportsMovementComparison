from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any

# --- Configuration Layer -------------------------------------------------

@dataclass(frozen=True)
class MetricConfig:
    key: str
    name: str
    unit: Optional[str] = None
    formula: Optional[str] = None  # symbolic reference or adapter key
    weight: float = 1.0
    direction: str = 'closer-better'  # 'higher-better' | 'lower-better' | 'closer-better'
    target: Optional[float] = None   # for closer-better
    warn_threshold: Optional[float] = None
    bad_threshold: Optional[float] = None

@dataclass(frozen=True)
class StageConfig:
    key: str
    name: str
    metrics: List[MetricConfig] = field(default_factory=list)
    weight: float = 1.0

@dataclass(frozen=True)
class ScoringPolicy:
    stage_weights: Dict[str, float] = field(default_factory=dict)
    normalize: bool = True

@dataclass(frozen=True)
class ActionConfig:
    sport: str
    action: str
    stages: List[StageConfig]
    scoring: ScoringPolicy = field(default_factory=ScoringPolicy)

    @property
    def stage_map(self) -> Dict[str, StageConfig]:
        return {s.key: s for s in self.stages}

# --- Keyframes -----------------------------------------------------------

@dataclass
class FrameRef:
    video_path: str
    frame_index: int

@dataclass
class KeyframeSet:
    user: Dict[str, FrameRef]
    standard: Dict[str, FrameRef]

    def update_user(self, stage_key: str, frame_index: Optional[int] = None, video_path: Optional[str] = None):
        ref = self.user.get(stage_key)
        if ref is None:
            if video_path is None or frame_index is None:
                raise ValueError('Need both video_path and frame_index for new keyframe')
            self.user[stage_key] = FrameRef(video_path=video_path, frame_index=frame_index)
            return
        if frame_index is not None:
            ref.frame_index = frame_index
        if video_path is not None:
            ref.video_path = video_path

    def update_standard(self, stage_key: str, frame_index: Optional[int] = None, video_path: Optional[str] = None):
        ref = self.standard.get(stage_key)
        if ref is None:
            if video_path is None or frame_index is None:
                raise ValueError('Need both video_path and frame_index for new keyframe')
            self.standard[stage_key] = FrameRef(video_path=video_path, frame_index=frame_index)
            return
        if frame_index is not None:
            ref.frame_index = frame_index
        if video_path is not None:
            ref.video_path = video_path

# --- Evaluation Results --------------------------------------------------

@dataclass
class MetricValue:
    key: str
    name: str
    unit: Optional[str]
    user_value: Optional[float]
    std_value: Optional[float]
    deviation: Optional[float]
    status: str  # ok | warn | bad | na

@dataclass
class StageResult:
    stage_key: str
    score: int
    metrics: List[MetricValue]
    suggestion: Optional[str] = None
    summary: Optional[str] = None
    suggestion_refined: Optional[str] = None

@dataclass
class TrainingBundle:
    key_issues: List[str] = field(default_factory=list)
    improvement_drills: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    key_issues_refined: List[str] = field(default_factory=list)
    improvement_drills_refined: List[str] = field(default_factory=list)
    next_steps_refined: List[str] = field(default_factory=list)

@dataclass
class EvaluationState:
    action: str
    sport: str
    stages: Dict[str, StageResult] = field(default_factory=dict)
    overall_score: Optional[int] = None
    training: Optional[TrainingBundle] = None
    dirty: set = field(default_factory=set)
    version: int = 0  # increment on each mutation
    # High-level summaries
    summary_raw: Optional[str] = None
    refined_summary: Optional[str] = None

    def mark_dirty(self, stage_key: str):
        self.dirty.add(stage_key)
        self.version += 1

    def clear_dirty(self, stage_key: str):
        if stage_key in self.dirty:
            self.dirty.remove(stage_key)
            self.version += 1

__all__ = [
    'MetricConfig','StageConfig','ScoringPolicy','ActionConfig',
    'FrameRef','KeyframeSet','MetricValue','StageResult','TrainingBundle','EvaluationState'
]

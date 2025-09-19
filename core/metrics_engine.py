from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Any
import time
import numpy as np

from .experimental.models.pose_data import BodyPose, PoseKeypoint
from .experimental.config.sport_configs import StageConfig, ActionConfig, MeasurementRule


@dataclass
class MeasurementValue:
    name: str
    value: Optional[float]
    unit: str
    status: str  # 'ok' | 'missing' | 'invalid'
    components: Dict[str, Dict[str, float]] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class StageMetricsResult:
    stage_name: str
    frame_index: int
    measurements: Dict[str, MeasurementValue]
    missing_keypoints: List[str]
    processing_time_ms: float


@dataclass
class ActionMetricsResult:
    action_name: str
    stage_results: List[StageMetricsResult]


HandlerType = Callable[[BodyPose, MeasurementRule], MeasurementValue]


class MetricsEngine:
    """Engine to compute configured measurements from pose data."""

    def __init__(self):
        self._handlers: Dict[str, HandlerType] = {}
        self._register_builtin_handlers()

    # --- Public API ---
    def compute_stage(self, stage_config: StageConfig, pose: BodyPose, frame_index: int = 0) -> StageMetricsResult:
        start = time.time()
        measurements: Dict[str, MeasurementValue] = {}

        # Collect all keypoints needed by this stage for early missing detection
        required = set()
        for rule in stage_config.measurements:
            required.update(rule.keypoints)
            if rule.reference_point:
                required.add(rule.reference_point)
        missing = [kp for kp in required if pose.get_keypoint(kp) is None]

        for rule in stage_config.measurements:
            handler = self._handlers.get(rule.measurement_type)
            if not handler:
                mv = MeasurementValue(
                    name=rule.name,
                    value=None,
                    unit=rule.unit,
                    status='invalid',
                    notes=[f"unsupported measurement_type: {rule.measurement_type}"]
                )
            else:
                mv = handler(pose, rule)
            measurements[rule.name] = mv

        elapsed = (time.time() - start) * 1000.0
        return StageMetricsResult(
            stage_name=stage_config.name,
            frame_index=frame_index,
            measurements=measurements,
            missing_keypoints=missing,
            processing_time_ms=elapsed
        )

    def compute_action(self, action_config: ActionConfig, stage_pose_map: Dict[str, Tuple[BodyPose, int]]) -> ActionMetricsResult:
        stage_results: List[StageMetricsResult] = []
        for stage_config in action_config.stages:
            if stage_config.name not in stage_pose_map:
                # Skip silently (could also create an empty result)
                continue
            pose, frame_index = stage_pose_map[stage_config.name]
            stage_results.append(self.compute_stage(stage_config, pose, frame_index))
        return ActionMetricsResult(action_name=action_config.name, stage_results=stage_results)

    def register_handler(self, measurement_type: str, handler: HandlerType):
        self._handlers[measurement_type] = handler

    # --- Built-in handlers ---
    def _register_builtin_handlers(self):
        self.register_handler('angle', self._handle_angle)
        self.register_handler('distance', self._handle_distance)
        self.register_handler('height', self._handle_height)
        self.register_handler('vertical_distance', self._handle_vertical_distance)
        self.register_handler('horizontal_distance', self._handle_horizontal_distance)

    # Utility
    @staticmethod
    def _kp_dict(kp: PoseKeypoint) -> Dict[str, float]:
        return {'x': kp.x, 'y': kp.y, 'z': kp.z, 'confidence': kp.confidence}

    def _handle_angle(self, pose: BodyPose, rule: MeasurementRule) -> MeasurementValue:
        needed = rule.keypoints[:3]
        if len(needed) < 3:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['need 3 keypoints'])
        pts = [pose.get_keypoint(k) for k in needed]
        if any(p is None for p in pts):
            missing = [k for k, p in zip(needed, pts) if p is None]
            return MeasurementValue(rule.name, None, rule.unit, 'missing', notes=[f'missing: {missing}'])
        a, b, c = pts
        vec1 = np.array([a.x - b.x, a.y - b.y])
        vec2 = np.array([c.x - b.x, c.y - b.y])
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['zero-length vector'])
        cos_angle = np.dot(vec1, vec2) / (norm1 * norm2)
        angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
        return MeasurementValue(rule.name, float(angle), rule.unit, 'ok', components={k: self._kp_dict(p) for k, p in zip(needed, pts)})

    def _handle_distance(self, pose: BodyPose, rule: MeasurementRule) -> MeasurementValue:
        needed = rule.keypoints[:2]
        if len(needed) < 2:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['need 2 keypoints'])
        pts = [pose.get_keypoint(k) for k in needed]
        if any(p is None for p in pts):
            missing = [k for k, p in zip(needed, pts) if p is None]
            return MeasurementValue(rule.name, None, rule.unit, 'missing', notes=[f'missing: {missing}'])
        p1, p2 = pts
        dist = float(np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2))
        return MeasurementValue(rule.name, dist, rule.unit, 'ok', components={k: self._kp_dict(p) for k, p in zip(needed, pts)})

    def _handle_height(self, pose: BodyPose, rule: MeasurementRule) -> MeasurementValue:
        if not rule.keypoints or not rule.reference_point:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['need keypoint and reference_point'])
        target = pose.get_keypoint(rule.keypoints[0])
        ref = pose.get_keypoint(rule.reference_point)
        if not target or not ref:
            missing = [k for k in [rule.keypoints[0], rule.reference_point] if pose.get_keypoint(k) is None]
            return MeasurementValue(rule.name, None, rule.unit, 'missing', notes=[f'missing: {missing}'])
        val = ref.y - target.y
        return MeasurementValue(rule.name, float(val), rule.unit, 'ok', components={rule.keypoints[0]: self._kp_dict(target), rule.reference_point: self._kp_dict(ref)})

    def _handle_vertical_distance(self, pose: BodyPose, rule: MeasurementRule) -> MeasurementValue:
        if not rule.keypoints or not rule.reference_point:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['need keypoint and reference_point'])
        target = pose.get_keypoint(rule.keypoints[0])
        ref = pose.get_keypoint(rule.reference_point)
        if not target or not ref:
            missing = [k for k in [rule.keypoints[0], rule.reference_point] if pose.get_keypoint(k) is None]
            return MeasurementValue(rule.name, None, rule.unit, 'missing', notes=[f'missing: {missing}'])
        distance = ref.y - target.y
        if rule.direction == 'up':
            val = distance
        elif rule.direction == 'down':
            val = -distance
        else:
            val = distance
        return MeasurementValue(rule.name, float(val), rule.unit, 'ok', components={rule.keypoints[0]: self._kp_dict(target), rule.reference_point: self._kp_dict(ref)})

    def _handle_horizontal_distance(self, pose: BodyPose, rule: MeasurementRule) -> MeasurementValue:
        if not rule.keypoints or not rule.reference_point:
            return MeasurementValue(rule.name, None, rule.unit, 'invalid', notes=['need keypoint and reference_point'])
        target = pose.get_keypoint(rule.keypoints[0])
        ref = pose.get_keypoint(rule.reference_point)
        if not target or not ref:
            missing = [k for k in [rule.keypoints[0], rule.reference_point] if pose.get_keypoint(k) is None]
            return MeasurementValue(rule.name, None, rule.unit, 'missing', notes=[f'missing: {missing}'])
        distance = target.x - ref.x
        if rule.direction in ('back', 'backward'):
            val = -distance
        elif rule.direction == 'forward':
            val = distance
        else:
            val = abs(distance)
        return MeasurementValue(rule.name, float(val), rule.unit, 'ok', components={rule.keypoints[0]: self._kp_dict(target), rule.reference_point: self._kp_dict(ref)})


__all__ = [
    'MetricsEngine',
    'MeasurementValue',
    'StageMetricsResult',
    'ActionMetricsResult'
]

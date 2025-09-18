import math
import os
import sys

# Ensure project root is on path when tests executed from repository root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.metrics_engine import MetricsEngine
from core.experimental.models.pose_data import BodyPose, PoseKeypoint
from core.experimental.config.sport_configs import MeasurementRule, StageConfig, ActionConfig


def make_pose():
    # Simple pose with right arm extended horizontally
    return BodyPose(
        right_shoulder=PoseKeypoint(100, 100),
        right_elbow=PoseKeypoint(150, 100),
        right_wrist=PoseKeypoint(200, 100),
        left_shoulder=PoseKeypoint(80, 100),
        left_elbow=PoseKeypoint(60, 120),
        left_wrist=PoseKeypoint(40, 140),
        frame_index=0
    )


def test_angle_distance_vertical_horizontal():
    engine = MetricsEngine()
    pose = make_pose()

    rules = [
        MeasurementRule(
            name='右臂角度', description='', measurement_type='angle',
            keypoints=['right_shoulder', 'right_elbow', 'right_wrist'], unit='度', tolerance_range=(0, 999)
        ),
        MeasurementRule(
            name='右肘到手腕距离', description='', measurement_type='distance',
            keypoints=['right_elbow', 'right_wrist'], unit='px', tolerance_range=(0, 999)
        ),
        MeasurementRule(
            name='手腕高度', description='', measurement_type='height',
            keypoints=['right_wrist'], reference_point='right_elbow', unit='px', tolerance_range=(-999, 999)
        ),
        MeasurementRule(
            name='手腕垂直距离', description='', measurement_type='vertical_distance',
            keypoints=['right_wrist'], reference_point='right_elbow', unit='px', direction='up', tolerance_range=(-999, 999)
        ),
        MeasurementRule(
            name='手腕水平距离', description='', measurement_type='horizontal_distance',
            keypoints=['right_wrist'], reference_point='right_elbow', unit='px', direction='forward', tolerance_range=(-999, 999)
        ),
    ]

    stage = StageConfig(name='test_stage', description='', measurements=rules)
    res = engine.compute_stage(stage, pose, frame_index=0)

    mv_angle = res.measurements['右臂角度']
    assert mv_angle.status == 'ok'
    # Arm is straight line: angle ~180 degrees
    assert 179 <= mv_angle.value <= 181

    mv_dist = res.measurements['右肘到手腕距离']
    assert mv_dist.value == 50

    mv_height = res.measurements['手腕高度']
    assert mv_height.value == 0  # same y

    mv_vertical = res.measurements['手腕垂直距离']
    assert mv_vertical.value == 0

    mv_horizontal = res.measurements['手腕水平距离']
    assert mv_horizontal.value == 50


def test_missing_keypoint():
    engine = MetricsEngine()
    pose = BodyPose(right_shoulder=PoseKeypoint(0, 0))  # others missing
    rules = [
        MeasurementRule(
            name='角度', description='', measurement_type='angle',
            keypoints=['right_shoulder', 'right_elbow', 'right_wrist'], unit='度', tolerance_range=(0, 999)
        )
    ]
    stage = StageConfig(name='missing_stage', description='', measurements=rules)
    res = engine.compute_stage(stage, pose, frame_index=1)
    mv = res.measurements['角度']
    assert mv.status == 'missing'
    assert 'missing' in mv.notes[0]


def test_compute_action():
    engine = MetricsEngine()
    pose = make_pose()
    stage = StageConfig(name='stage1', description='', measurements=[
        MeasurementRule(
            name='右臂角度', description='', measurement_type='angle',
            keypoints=['right_shoulder', 'right_elbow', 'right_wrist'], unit='度', tolerance_range=(0, 999)
        )
    ])
    action = ActionConfig(name='动作A', description='', stages=[stage])
    result = engine.compute_action(action, {'stage1': (pose, 0)})
    assert len(result.stage_results) == 1
    assert '右臂角度' in result.stage_results[0].measurements

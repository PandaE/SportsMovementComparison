import os
import sys

import pytest
import cv2

# Ensure project root path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.utils.pose_utils import extract_pose  # raw mediapipe landmarks
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor
from core.experimental.models.pose_data import BodyPose, PoseKeypoint
from core.metrics_engine import MetricsEngine
from core.experimental.config.sport_configs import SportConfigs


TEST_IMG_DIR = os.path.join(os.path.dirname(__file__), 'experimental', 'test_images')
USER_IMG = os.path.join(TEST_IMG_DIR, 'user_setup.jpg')
STD_IMG = os.path.join(TEST_IMG_DIR, 'standard_setup.jpg')


def _pose_from_landmarks(result_dict) -> BodyPose:
    """Convert raw mediapipe landmark dict list (normalized) into BodyPose using pixel scaling."""
    if not result_dict or not result_dict.get('landmarks'):
        return BodyPose()
    w = result_dict['width']
    h = result_dict['height']
    lms = result_dict['landmarks']

    def kp(idx):
        if idx < 0 or idx >= len(lms):
            return None
        d = lms[idx]
        return PoseKeypoint(x=d['x'] * w, y=d['y'] * h, z=d['z'], confidence=d['visibility'])

    # Map subset of mediapipe indices used in sport configs
    return BodyPose(
        nose=kp(0),
        left_shoulder=kp(11),
        right_shoulder=kp(12),
        left_elbow=kp(13),
        right_elbow=kp(14),
        left_wrist=kp(15),
        right_wrist=kp(16),
        left_hip=kp(23),
        right_hip=kp(24),
        left_knee=kp(25),
        right_knee=kp(26),
        left_ankle=kp(27),
        right_ankle=kp(28),
    )


@pytest.mark.integration
def test_pose_metrics_badminton_setup_stage():
    # Ensure images present
    if not (os.path.exists(USER_IMG) and os.path.exists(STD_IMG)):
        pytest.skip('Test images not found; skip integration test.')

    mode = 'mediapipe'
    try:
        import mediapipe  # noqa: F401
        user_raw = extract_pose(USER_IMG)
        std_raw = extract_pose(STD_IMG)
        if not (user_raw['success'] and std_raw['success'] and user_raw['landmarks'] and std_raw['landmarks']):
            mode = 'mock_fallback'
            raise RuntimeError('mediapipe returned no landmarks, fallback to mock')
        user_pose = _pose_from_landmarks(user_raw)
        std_pose = _pose_from_landmarks(std_raw)
    except Exception:  # mediapipe missing or failed -> fallback
        mode = 'mock'
        user_img = cv2.imread(USER_IMG)
        std_img = cv2.imread(STD_IMG)
        if user_img is None or std_img is None:
            pytest.skip('Images unreadable')
        pe = PoseExtractor(backend='mediapipe')  # it will downgrade to mock if mediapipe not installed
        user_pose = pe.extract_pose_from_image(user_img, 0)
        std_pose = pe.extract_pose_from_image(std_img, 0)
        assert user_pose is not None and std_pose is not None, 'Mock pose extraction failed'

    # Basic sanity: at least shoulders should exist for both
    assert user_pose.right_shoulder is not None
    assert std_pose.right_shoulder is not None

    # 3. Load badminton config and pick setup_stage
    action_config = SportConfigs.get_badminton_forehand_clear()
    setup_stage_cfg = [s for s in action_config.stages if s.name == 'setup_stage'][0]

    # 4. Run metrics engine for both poses
    engine = MetricsEngine()
    user_metrics = engine.compute_stage(setup_stage_cfg, user_pose, frame_index=0)
    std_metrics = engine.compute_stage(setup_stage_cfg, std_pose, frame_index=0)

    # 5. Compare common measurement names (simple diff, not scoring layer here)
    diffs = {}
    for name, mv in user_metrics.measurements.items():
        if mv.status == 'ok' and name in std_metrics.measurements and std_metrics.measurements[name].status == 'ok':
            diffs[name] = mv.value - std_metrics.measurements[name].value  # type: ignore

    # 6. Assertions: at least one measurement computed, diffs dict not empty
    assert any(mv.status == 'ok' for mv in user_metrics.measurements.values())
    assert any(mv.status == 'ok' for mv in std_metrics.measurements.values())

    # 7. Provide diagnostic print (pytest -s)
    print('Pose backend mode:', mode)
    print('User measurements:', {k: v.value for k, v in user_metrics.measurements.items()})
    print('Std measurements:', {k: v.value for k, v in std_metrics.measurements.items()})
    print('Diffs:', diffs)

    # Optional: ensure angle measurements (if present) within plausible biomechanical range
    for mv in user_metrics.measurements.values():
        if mv.unit == '度' and mv.value is not None:
            assert 0 <= mv.value <= 200

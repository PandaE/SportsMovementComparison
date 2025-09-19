import os, sys, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.pipeline.evaluation_pipeline import run_action_evaluation
from core.experimental.config.sport_configs import SportConfigs
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor

TEST_IMG_DIR = os.path.join(os.path.dirname(__file__), 'experimental', 'test_images')
USER_IMG = os.path.join(TEST_IMG_DIR, 'user_setup.jpg')

@pytest.mark.integration
def test_pipeline_end_to_end_single_frame():
    if not os.path.exists(USER_IMG):
        pytest.skip('missing test image')
    # Pose
    pe = PoseExtractor(backend='mediapipe')  # falls back automatically
    img = __import__('cv2').imread(USER_IMG)
    assert img is not None
    pose = pe.extract_pose_from_image(img, 0)
    assert pose is not None

    # Config
    action_cfg = SportConfigs.get_badminton_forehand_clear()

    # Stage pose map (reuse single frame)
    spm = {st.name: (pose, 0) for st in action_cfg.stages}

    metrics_result, evaluation = run_action_evaluation(action_cfg, spm, language='en_US')

    # Basic assertions
    assert evaluation.action_name == action_cfg.name
    assert evaluation.stages
    # Score should be within [0,1]
    if evaluation.score is not None:
        assert 0.0 <= evaluation.score <= 1.0

    print('E2E evaluation summary:', evaluation.summary)

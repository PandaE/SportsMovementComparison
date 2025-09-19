import os
import sys
import pytest

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import cv2
from core.experimental.config.sport_configs import SportConfigs
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor
from core.pipeline.evaluation_pipeline import run_action_evaluation

TEST_IMG_DIR = os.path.join(os.path.dirname(__file__), 'experimental', 'test_images')

# Mapping of logical stage names to (user_image, standard_image) filenames.
# We rely on SportConfigs badminton forehand clear stage names.
STAGE_IMAGE_MAP = {
    # Map internal config stage names -> (user_img, standard_img)
    'setup_stage': ('user_setup.jpg', 'standard_setup.jpg'),
    'backswing_stage': ('user_backswing.jpg', 'standard_backwing.jpg'),  # note the spelling in file
    'power_stage': ('user_power.jpg', 'standard_power.jpg'),
}

@pytest.mark.integration
@pytest.mark.skipif(not os.path.exists(TEST_IMG_DIR), reason='test images directory missing')
def test_forehand_clear_multi_stage_pipeline():
    # 1. Load action config
    action_cfg = SportConfigs.get_badminton_forehand_clear()
    assert action_cfg.stages, 'Action config should have stages'

    # 2. Prepare pose extractor (will fallback to mock if mediapipe unavailable)
    pose_extractor = PoseExtractor(backend='mediapipe')

    # 3. Build stage_pose_map using images if available; skip stages missing images
    stage_pose_map = {}
    loaded_stage_names = []

    for stage in action_cfg.stages:
        mapping = STAGE_IMAGE_MAP.get(stage.name)
        if not mapping:
            # Allow unmatched stage names (config change resilience)
            continue
        user_file, std_file = mapping
        user_path = os.path.join(TEST_IMG_DIR, user_file)
        std_path = os.path.join(TEST_IMG_DIR, std_file)
        if not (os.path.exists(user_path) and os.path.exists(std_path)):
            print(f"Skipping stage {stage.name}: missing files {user_path} or {std_path}")
            continue
        user_img = cv2.imread(user_path)
        std_img = cv2.imread(std_path)
        assert user_img is not None, f"Failed to read {user_path}"
        assert std_img is not None, f"Failed to read {std_path}"
        # For evaluation pipeline we only need one pose per stage (user pose). Use user image.
        user_pose = pose_extractor.extract_pose_from_image(user_img, 0)
        assert user_pose is not None, f"Pose extraction failed for {stage.name}" 
        stage_pose_map[stage.name] = (user_pose, 0)
        loaded_stage_names.append(stage.name)

    assert stage_pose_map, 'No stages loaded for evaluation (check image map & files)'

    # 4. Run evaluation (Chinese language to test localization path)
    metrics_result, evaluation = run_action_evaluation(action_cfg, stage_pose_map, language='zh_CN')

    # 5. Assertions
    assert evaluation.action_name == action_cfg.name
    assert evaluation.stages, 'Evaluation should contain stages'
    # Each loaded stage should appear in evaluation (or at least subset if config changed)
    eval_stage_names = {s.name for s in evaluation.stages}
    missing = [s for s in loaded_stage_names if s not in eval_stage_names]
    assert not missing, f"Missing evaluated stages: {missing}"
    # Score boundary check (allow None if scoring disabled, but currently enabled in builder)
    if evaluation.score is not None:
        assert 0.0 <= evaluation.score <= 1.0

    # Print concise debug info + LLM summaries (if enabled)
    print('\nE2E Forehand Clear Evaluation:')
    print('Stages evaluated:', eval_stage_names)
    print('Overall score:', evaluation.score)
    for st in evaluation.stages:
        print(f"  - {st.name}: score={st.score} measurements={len(st.measurements)}")
    print('\nRaw Summary:')
    print(evaluation.summary)
    print('\nLLM Refined Summary:' if evaluation.refined_summary else '\n(No refined summary produced)')
    if evaluation.refined_summary:
        print(evaluation.refined_summary)

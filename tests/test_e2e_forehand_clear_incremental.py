import os
import sys
import pytest
import cv2

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.experimental.config.sport_configs import SportConfigs
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor
from core.pipeline.evaluation_pipeline import run_action_evaluation, run_action_evaluation_incremental

TEST_IMG_DIR = os.path.join(os.path.dirname(__file__), 'experimental', 'test_images')

STAGE_IMAGE_MAP = {
    'setup_stage': 'user_setup.jpg',
    'backswing_stage': 'user_backswing.jpg',
    'power_stage': 'user_power.jpg',
}

@pytest.mark.integration
@pytest.mark.skipif(not os.path.exists(TEST_IMG_DIR), reason='test images directory missing')
def test_forehand_clear_incremental_pipeline():
    action_cfg = SportConfigs.get_badminton_forehand_clear()
    pose_extractor = PoseExtractor(backend='mediapipe')

    # 初始完整 stage pose map
    stage_pose_map = {}
    for stage in action_cfg.stages:
        img_name = STAGE_IMAGE_MAP.get(stage.name)
        if not img_name:
            continue
        img_path = os.path.join(TEST_IMG_DIR, img_name)
        img = cv2.imread(img_path)
        assert img is not None, f"Missing image {img_path}"
        pose = pose_extractor.extract_pose_from_image(img, 0)
        assert pose is not None, f"Pose extraction failed for {stage.name}"
        stage_pose_map[stage.name] = (pose, 0)

    assert stage_pose_map, 'No initial stages loaded'

    # 运行第一次完整评价
    metrics_result_full, evaluation_full = run_action_evaluation(action_cfg, stage_pose_map, language='zh_CN')
    print('\n[Full Evaluation] Score:', evaluation_full.score)
    for st in evaluation_full.stages:
        print(f"  Stage {st.name}: score={st.score} meas={len(st.measurements)}")

    # 模拟用户只调整了 power_stage: 复制原 pose 并轻微修改手腕坐标让角度变化
    original_pose, _ = stage_pose_map['power_stage']
    # 构造一个浅拷贝（直接修改对象以模拟新帧）
    modified_pose = original_pose
    if modified_pose.right_wrist:
        modified_pose.right_wrist.x += 10  # 人为改变位置
        modified_pose.right_wrist.y -= 5

    incremental_map = {
        'power_stage': (modified_pose, 1)  # 新的帧索引 1 表示更新
    }

    # 合并映射：其余阶段沿用旧 pose
    merged_map = dict(stage_pose_map)
    merged_map.update(incremental_map)

    # 运行增量评价（仅更新 power_stage）
    metrics_result_inc, evaluation_inc = run_action_evaluation_incremental(
        evaluation_full,
        action_cfg,
        updated_stage_names=['power_stage'],
        stage_pose_map=merged_map,
        language='zh_CN'
    )

    print('\n[Incremental Evaluation] Score:', evaluation_inc.score)
    for st in evaluation_inc.stages:
        print(f"  Stage {st.name}: score={st.score} meas={len(st.measurements)}")

    # 断言：非更新阶段得分应保持不变
    full_scores = {s.name: s.score for s in evaluation_full.stages}
    inc_scores = {s.name: s.score for s in evaluation_inc.stages}
    for name in full_scores:
        if name != 'power_stage':
            assert abs(full_scores[name] - inc_scores[name]) < 1e-9, f'Stage {name} score changed unexpectedly'

    # power_stage 允许变化（可能提高或降低）
    assert 'power_stage' in inc_scores

    # 总分应重新计算（不强制方向，只要合法范围）
    if evaluation_inc.score is not None:
        assert 0.0 <= evaluation_inc.score <= 1.0

    print('\n[Delta]')
    print('  Full Score:', evaluation_full.score)
    print('  Incremental Score:', evaluation_inc.score)
    print('  Power Stage Score (full -> inc):', full_scores['power_stage'], '->', inc_scores['power_stage'])

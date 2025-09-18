"""End-to-end demo: Pose Extraction -> Metrics -> Evaluation

Usage (ensure venv + mediapipe installed if you want real landmarks):

    python demo_end_to_end_evaluation.py --user tests/experimental/test_images/user_setup.jpg \
        --standard tests/experimental/test_images/standard_setup.jpg --lang zh_CN

If mediapipe is missing or fails, a mock fallback will be used.
"""
from __future__ import annotations
import argparse
import os
import sys
import json
import cv2

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.utils.pose_utils import extract_pose  # type: ignore
from core.experimental.frame_analyzer.pose_extractor import PoseExtractor  # type: ignore
from core.experimental.models.pose_data import BodyPose, PoseKeypoint  # type: ignore
from core.experimental.config.sport_configs import SportConfigs  # type: ignore
from core.metrics_engine import MetricsEngine  # type: ignore
from core.evaluation import (
    MeasurementRule as EvalMeasurementRule,
    StageRule as EvalStageRule,
    ActionEvaluationConfig,
    evaluate_action,
)  # type: ignore


def pose_from_landmarks(result_dict) -> BodyPose:
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


def extract_body_pose(image_path: str) -> BodyPose:
    mode = 'mediapipe'
    try:
        import mediapipe  # noqa: F401
        raw = extract_pose(image_path)
        if not raw.get('success') or not raw.get('landmarks'):
            raise RuntimeError('mediapipe produced no landmarks')
        return pose_from_landmarks(raw)
    except Exception:
        mode = 'mock'
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(image_path)
        pe = PoseExtractor(backend='mediapipe')  # will fallback
        pose = pe.extract_pose_from_image(img, 0)
        if pose is None:
            raise RuntimeError('mock pose extraction failed')
        return pose


def build_evaluation_config(action_config, language: str) -> ActionEvaluationConfig:
    # Map experimental sport config to evaluation config rules.
    stages = []
    for st in action_config.stages:
        eval_rules = []
        for mr in st.measurements:
            # Convert tolerance range (min,max) to center+radius for scoring target/tolerance if angle-like
            target = None
            tolerance = None
            if mr.tolerance_range:
                min_v, max_v = mr.tolerance_range
                target = (min_v + max_v) / 2.0
                tolerance = (max_v - min_v) / 2.0
            eval_rules.append(EvalMeasurementRule(
                key=mr.name,  # reuse measurement name as key
                target=target,
                tolerance=tolerance,
                min_value=mr.tolerance_range[0] if mr.tolerance_range else None,
                max_value=mr.tolerance_range[1] if mr.tolerance_range else None,
                weight=mr.weight,
                description={'zh_CN': mr.description, 'en_US': mr.description},
                score_strategy='linear'
            ))
        stages.append(EvalStageRule(
            name=st.name,
            measurements=eval_rules,
            weight=st.weight,
            description={'zh_CN': st.description, 'en_US': st.description}
        ))
    return ActionEvaluationConfig(
        action_name=action_config.name,
        stages=stages,
        language=language,
        enable_scoring=True,
        enable_llm_refine=False,
    )


def build_metrics_dict(action_result) -> dict:
    # Convert ActionMetricsResult -> evaluation metrics dict shape {stage: {measurement_key: {'value': float}}}
    out = {}
    for stage_res in action_result.stage_results:
        md = {}
        for name, mv in stage_res.measurements.items():
            if mv.value is not None:
                md[name] = {'value': mv.value}
        out[stage_res.stage_name] = md
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True, help='User frame image path')
    parser.add_argument('--standard', required=False, help='Optional standard frame path (unused in evaluation)')
    parser.add_argument('--lang', default='zh_CN', choices=['zh_CN', 'en_US'])
    parser.add_argument('--print-json', action='store_true')
    args = parser.parse_args()

    # 1. Load config
    action_config = SportConfigs.get_badminton_forehand_clear()

    # 2. Extract pose for each stage snapshot (for demo we reuse same frame for all stages)
    user_pose = extract_body_pose(args.user)

    # 3. Build a naive stage_pose_map: reuse same pose for all configured stages
    stage_pose_map = {st.name: (user_pose, 0) for st in action_config.stages}

    # 4. Run metrics
    engine = MetricsEngine()
    action_metrics = engine.compute_action(action_config, stage_pose_map)

    # 5. Convert metrics to evaluation input dict
    metrics_dict = build_metrics_dict(action_metrics)

    # 6. Build evaluation config
    eval_config = build_evaluation_config(action_config, args.lang)

    # 7. Evaluate
    evaluation = evaluate_action(metrics_dict, eval_config)

    # 8. Print results
    print('=== Evaluation Summary ===')
    print('Action:', evaluation.action_name)
    print('Overall Score:', f"{evaluation.score:.3f}" if evaluation.score is not None else 'N/A')
    print('Summary:', evaluation.summary)
    for st in evaluation.stages:
        stage_score_str = f"{st.score:.3f}" if st.score is not None else 'N/A'
        print(f"\n[Stage] {st.name} score={stage_score_str}")
        for mv in st.measurements:
            score_str = f"{mv.score:.3f}" if mv.score is not None else 'N/A'
            if isinstance(mv.value, (int, float)) and mv.value is not None:
                value_str = f"{mv.value:.3f}"
            else:
                value_str = str(mv.value)
            print(f"  - {mv.key}: value={value_str} score={score_str} passed={mv.passed} -> {mv.feedback}")

    if args.print_json:
        # Minimal JSON export
        data = {
            'action': evaluation.action_name,
            'score': evaluation.score,
            'summary': evaluation.summary,
            'stages': [
                {
                    'name': st.name,
                    'score': st.score,
                    'measurements': [
                        {
                            'key': mv.key,
                            'value': mv.value,
                            'score': mv.score,
                            'passed': mv.passed,
                            'feedback': mv.feedback,
                        } for mv in st.measurements
                    ]
                } for st in evaluation.stages
            ]
        }
        print('\nJSON Output:')
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

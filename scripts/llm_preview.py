from __future__ import annotations
"""Quick manual preview of LLM refinement without launching UI.
Usage (PowerShell):
  $env:ENABLE_LLM_REFINEMENT=1; python scripts/llm_preview.py --dummy
Or with real Azure (ensure env vars set):
  $env:ENABLE_LLM_REFINEMENT=1; $env:AZURE_OPENAI_ENDPOINT='...'; ...; python scripts/llm_preview.py
"""
import argparse, json, os, sys

# Ensure project root (parent of scripts/) is on sys.path so that 'core' package resolves
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.new_evaluation.session import EvaluationSession  # type: ignore
from core.new_evaluation.data_models import ActionConfig, StageConfig, MetricConfig, KeyframeSet, FrameRef  # type: ignore
from core.llm.llm_refiner import SuggestionRefiner  # type: ignore

def build_dummy_state():
    stages = [
        StageConfig(key='setup', name='Setup', metrics=[MetricConfig(key='arm_extension', name='Arm Extension at Impact', unit='°', target=170.0)]),
        StageConfig(key='backswing', name='Backswing', metrics=[MetricConfig(key='wrist_backswing', name='Wrist Backswing Distance', unit='px', target=80.0)])
    ]
    action_cfg = ActionConfig(sport='badminton', action='forehand_clear', stages=stages)
    keyframes = KeyframeSet(user={'setup': FrameRef('user.mp4', 10)}, standard={'setup': FrameRef('std.mp4', 10)})
    session = EvaluationSession(action_cfg, keyframes, user_video='user.mp4', standard_video='std.mp4')
    session.evaluate()  # populates state with synthetic placeholder metrics
    return session.get_state()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump-payload', action='store_true', help='Print payload only (no model call).')
    ap.add_argument('--dummy', action='store_true', help='Force dummy provider (ignore Azure env).')
    args = ap.parse_args()

    if args.dummy:
        os.environ['ENABLE_LLM_REFINEMENT'] = '0'  # force dummy path in SuggestionRefiner init fallback

    state = build_dummy_state()
    refiner = SuggestionRefiner(enable=not args.dummy)
    payload = refiner._build_payload(state)  # type: ignore (intentional access for preview)

    if args.dump_payload:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    result = refiner._refine(payload)  # type: ignore
    print('=== Refined Summary ===')
    print(result.refined_action_summary)
    print('\n=== Stage Suggestions ===')
    for k, v in result.stage_suggestions.items():
        print(f"- {k}: {v}")
    print('\n=== Training ===')
    print('Key Issues:', result.training_key_issues)
    print('Drills:', result.training_drills)
    print('Next Steps:', result.training_next_steps)

if __name__ == '__main__':
    main()

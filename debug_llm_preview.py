import os, sys
from core.evaluation.llm_config import reload_llm_config
from core.evaluation.evaluator import evaluate_action
from core.evaluation.models import ActionEvaluationConfig, StageRule, MeasurementRule

# Minimal metrics example
metrics = {
    'stage1': {
        'elbow_angle': {'value': 172.0},
        'knee_angle': {'value': 160.0},
    },
    'stage2': {
        'racket_height': {'value': 1.78},
        'torso_rotation': {'value': 40.0},
    }
}

config = ActionEvaluationConfig(
    action_name='ForehandClear',
    stages=[
        StageRule(
            name='stage1',
            measurements=[
                MeasurementRule(key='elbow_angle', target=180, tolerance=10),
                MeasurementRule(key='knee_angle', target=165, tolerance=15),
            ],
            weight=0.5
        ),
        StageRule(
            name='stage2',
            measurements=[
                MeasurementRule(key='racket_height', min_value=1.6, max_value=2.0),
                MeasurementRule(key='torso_rotation', target=45, tolerance=8),
            ],
            weight=0.5
        )
    ],
    language='zh_CN',
    enable_scoring=True,
    enable_llm_refine=True,
    llm_style='coach'
)

cfg = reload_llm_config()
print(f"LLM Enabled: {cfg.enabled} provider={cfg.provider} api_key_set={bool(cfg.api_key)} allow_fallback={cfg.allow_fallback}")

eval_result = evaluate_action(metrics, config)
print("\n=== RAW SUMMARY ===")
print(eval_result.summary)
print("\n=== REFINED SUMMARY ===")
print(eval_result.refined_summary)

for st in eval_result.stages:
    print(f"\n--- Stage: {st.name} (score={st.score}) ---")
    print("Raw Stage Feedback:")
    print(st.feedback)
    print("Refined Stage Feedback:")
    print(st.refined_feedback)
    for m in st.measurements:
        print(f"  * Measurement {m.key}: val={m.value} score={m.score} passed={m.passed}")
        print(f"    Raw: {m.feedback}")
        print(f"    Refined: {m.refined_feedback}")

print("\n(If refined outputs look like mock placeholders, real provider was not available or fell back.)")

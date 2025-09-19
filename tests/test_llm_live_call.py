import os, sys, pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.evaluation.llm_config import reload_llm_config
from core.evaluation.llm_refiner import refine_summary
from core.evaluation.models import ActionEvaluationConfig, StageRule, MeasurementRule
from core.evaluation.evaluator import evaluate_action

RAW = "Baseline movement summary for live LLM refinement test."  # English

@pytest.mark.integration
def test_live_llm_refine_summary():
    cfg = reload_llm_config()
    # Always attempt refinement; if disabled we get mock output
    out = refine_summary(RAW, 'en_US', 'coach')
    print("\n=== LLM Summary Refinement ===")
    print("Enabled:", cfg.enabled, "Provider:", cfg.provider, "ApiKeyPresent:", bool(cfg.api_key))
    print("Raw:", RAW)
    print("Refined:", out)
    # Basic expectations: refined should not be empty and ideally differ
    assert out
    if cfg.enabled and cfg.api_key:
        assert out != RAW
        assert len(out) >= len(RAW)

@pytest.mark.integration
def test_live_llm_full_evaluation():
    cfg = reload_llm_config()
    stage = StageRule(name='stage1', measurements=[MeasurementRule(key='metric1', target=10, tolerance=5)])
    eval_cfg = ActionEvaluationConfig(action_name='ActionLive', stages=[stage], language='en_US', enable_scoring=True, enable_llm_refine=True, llm_style='coach')
    metrics = {'stage1': {'metric1': {'value': 12.0}}}
    evaluation = evaluate_action(metrics, eval_cfg)
    print("\n=== LLM Full Evaluation Refinement ===")
    print("Enabled:", cfg.enabled, "Provider:", cfg.provider, "ApiKeyPresent:", bool(cfg.api_key))
    print("Raw Summary:", evaluation.summary)
    print("Refined Summary:", evaluation.refined_summary)
    for st in evaluation.stages:
        print(f"Stage: {st.name} score={st.score}")
        print("  Stage refined:", getattr(st, 'refined_feedback', None))
        for meas in st.measurements:
            # MeasurementEvaluation may not expose target directly; print known fields
            printable = [f"value={getattr(meas, 'value', None)}", f"score={getattr(meas, 'score', None)}"]
            print(f"    Measurement {meas.key} " + " ".join(printable))
            print("      Refined:", getattr(meas, 'refined_feedback', None))
    assert evaluation.refined_summary is not None
    st = evaluation.stages[0]
    assert getattr(st, 'refined_feedback', None) is not None
    assert any(getattr(m, 'refined_feedback', None) for m in st.measurements)

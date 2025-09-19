import os
import sys

# Ensure project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.evaluation.llm_config import load_llm_config, reload_llm_config  # type: ignore
from core.evaluation.llm_refiner import refine_summary  # type: ignore
from core.evaluation.models import ActionEvaluationConfig, StageRule, MeasurementRule  # type: ignore
from core.evaluation.evaluator import evaluate_action  # type: ignore

RAW = "Test summary raw base line for movement analysis."  # English baseline


def write_temp_llm_ini(tmp_path, enabled: bool = True, language: str = 'en_US', style: str = 'coach'):
    content = f"""[llm]\nenabled = {'true' if enabled else 'false'}\nprovider = openai\nmodel = gpt-4o-mini\nstyle = {style}\napi_key = \nlanguage = auto\nallow_fallback = true\n\n[prompt]\nsystem = You are a coach. Respond in {{language}} style={{style}}.\nrefine_template = Improve clarity and structure, keep facts. Source:\n{{raw}}\n"""
    ini_path = tmp_path / 'llm_settings.ini'
    ini_path.write_text(content, encoding='utf-8')
    # Place where loader expects (core/evaluation)
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'core', 'evaluation')
    target_file = os.path.abspath(os.path.join(target_dir, 'llm_settings.ini'))
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    return target_file


def test_refine_disabled(tmp_path):
    # Write disabled config
    write_temp_llm_ini(tmp_path, enabled=False)
    reload_llm_config()
    out = refine_summary(RAW, 'en_US', 'coach')
    # Disabled -> returns original
    assert out == RAW


def test_refine_enabled_mock(tmp_path):
    write_temp_llm_ini(tmp_path, enabled=True)
    reload_llm_config()
    out = refine_summary(RAW, 'en_US', 'coach')
    assert out != RAW
    # Expect header marker present
    assert 'Refined' in out or 'LLM Refined' in out or '[LLM' in out


def test_integration_with_evaluator(tmp_path):
    write_temp_llm_ini(tmp_path, enabled=True)
    reload_llm_config()
    # Build minimal config & metrics
    stage = StageRule(name='stage1', measurements=[MeasurementRule(key='m1')])
    cfg = ActionEvaluationConfig(action_name='Action', stages=[stage], language='en_US', enable_scoring=False, enable_llm_refine=True, llm_style='coach')
    metrics = {'stage1': {'m1': {'value': 1.0}}}
    eval_result = evaluate_action(metrics, cfg)
    assert eval_result.summary is not None
    assert eval_result.refined_summary is not None
    assert eval_result.refined_summary != eval_result.summary


def test_azure_provider_fallback(tmp_path):
    # Create azure config but leave api_key blank so provider not ready -> fallback to mock
    content = """[llm]\nenabled = true\nprovider = azure\nmodel = gpt-4o-mini\napi_key = \napi_base = https://example-resource.openai.azure.com\nazure_deployment = gpt-4o-mini\nallow_fallback = true\n[prompt]\nsystem = You are a coach.\nrefine_template = Improve clarity:\n{raw}\n"""
    target_dir = os.path.join(os.path.dirname(__file__), '..', 'core', 'evaluation')
    target_file = os.path.abspath(os.path.join(target_dir, 'llm_settings.ini'))
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(content)
    reload_llm_config()
    out = refine_summary(RAW, 'en_US', 'coach')
    assert out != RAW  # still refined via mock
    assert 'Refined' in out or 'LLM' in out

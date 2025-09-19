from __future__ import annotations
from typing import Optional, List
import textwrap

from .llm_config import load_llm_config
from .llm_providers import AzureOpenAIProvider  # type: ignore
from .models import ActionEvaluation, StageEvaluation, MeasurementEvaluation


def _build_prompt(raw: str, cfg, language: str) -> tuple[str, str]:
    lang = cfg.resolve_language(language)
    style = cfg.style or 'coach'
    system = cfg.system_prompt or (
        '你是一名专业体育教练, 提供结构化改进建议。' if lang.startswith('zh') else 'You are an expert sports coach. Provide structured actionable feedback.'
    )
    template = cfg.refine_template or (
        '请改写并提升以下自动生成的运动分析总结, 保持事实, 输出结构: 1) 总体评价 2) 优势 3) 改进点 4) 训练建议:\n\n{raw}'
        if lang.startswith('zh') else
        'Improve the following auto-generated sports movement analysis. Keep facts. Output sections: 1) Overall Feedback 2) Strengths 3) Areas to Improve 4) Training Suggestions.\n\n{raw}'
    )
    content = template.format(raw=raw, style=style, language=('中文' if lang.startswith('zh') else 'English'))
    return system.format(style=style, language=('中文' if lang.startswith('zh') else 'English')), content


def _mock_refine(raw: str, language: str, style: Optional[str]) -> str:
    zh = not language.startswith('en')
    # Simple heuristic enrichment
    if zh:
        header = '【LLM精炼结果' + (f'-{style}' if style else '') + '】'
        bullet_strength = '优势'
        bullet_improve = '改进'
        bullet_next = '训练建议'
    else:
        header = '[LLM Refined' + (f'-{style}' if style else '') + ']'
        bullet_strength = 'Strengths'
        bullet_improve = 'Improvements'
        bullet_next = 'Next Steps'
    snippet = raw.strip().split('\n')[0][:160]
    enriched = textwrap.dedent(f"""
    {header}\n{snippet}...\n- {bullet_strength}: (mock) 提炼要点 / Key points\n- {bullet_improve}: (mock) 主要改进方向 / Main fixes\n- {bullet_next}: (mock) 具体下一步 / Concrete next steps
    """).strip()
    return enriched


def refine_summary(raw_summary: str, language: str, style: Optional[str] = None) -> str:
    cfg = load_llm_config()
    # If not enabled just return original
    if not cfg.enabled:
        return raw_summary

    lang = cfg.resolve_language(language)
    # Attempt real provider usage if enabled & key present
    if cfg.is_real_call:
        system_prompt, content_prompt = _build_prompt(raw_summary, cfg, lang)
        # Only Azure implemented currently
        if cfg.provider.lower() == 'azure':
            provider = AzureOpenAIProvider(
                api_key=cfg.api_key or '',
                api_base=cfg.api_base or '',
                deployment=cfg.azure_deployment or cfg.model,
                timeout=cfg.timeout
            )
            if provider.available():
                resp = provider.refine(system_prompt, content_prompt, temperature=cfg.temperature, max_tokens=cfg.max_tokens)
                if resp:
                    return resp.strip()
                # fall through to mock if empty
            # provider unavailable or failed
            if not provider.available():
                # Could log provider.reason_unavailable()
                pass
        # Future: other providers (openai, ollama etc.)
        if cfg.allow_fallback:
            return _mock_refine(raw_summary, lang, style or cfg.style)
        return raw_summary
    # No real call path -> mock
    return _mock_refine(raw_summary, lang, style or cfg.style)


# ---- New granular refinement APIs ----
def refine_measurement(me: MeasurementEvaluation, language: str, style: Optional[str]) -> str:
    base = me.feedback or ''
    raw = f"测量: {me.key}\n值: {me.value} 目标: {me.expected} 分数: {me.score}\n反馈: {base}"
    return refine_summary(raw, language, style)


def refine_stage(stage: StageEvaluation, language: str, style: Optional[str]) -> str:
    # Concatenate measurement briefs
    lines: List[str] = []
    for m in stage.measurements:
        part = f"[{m.key}] val={m.value} score={m.score} pass={m.passed} fb={m.feedback}"
        lines.append(part)
    raw = f"阶段: {stage.name}\n总体得分: {stage.score}\n明细:\n" + "\n".join(lines) + f"\n阶段反馈: {stage.feedback or ''}"
    return refine_summary(raw, language, style)


def refine_full_evaluation(evaluation: ActionEvaluation, style: Optional[str]) -> ActionEvaluation:
    cfg = load_llm_config()
    # 如果配置文件未启用但外部调用需要 refined，也使用 mock 路径
    if not cfg.enabled:
        evaluation.refined_summary = _mock_refine(evaluation.summary or '', evaluation.language, style or (cfg.style if hasattr(cfg, 'style') else 'coach'))
        for st in evaluation.stages:
            st.refined_feedback = _mock_refine(st.feedback or '', evaluation.language, style or 'coach')
            for m in st.measurements:
                m.refined_feedback = _mock_refine(m.feedback or '', evaluation.language, style or 'coach')
        return evaluation
    # Refine summary first (existing real or fallback logic)
    evaluation.refined_summary = refine_summary(evaluation.summary or '', evaluation.language, style or cfg.style)
    # Refine per stage
    for st in evaluation.stages:
        st.refined_feedback = refine_stage(st, evaluation.language, style or cfg.style)
        for m in st.measurements:
            m.refined_feedback = refine_measurement(m, evaluation.language, style or cfg.style)
    return evaluation


__all__ = ['refine_summary', 'refine_full_evaluation', 'refine_stage', 'refine_measurement']


__all__ = ['refine_summary']

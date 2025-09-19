from __future__ import annotations
import configparser
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

CONFIG_FILENAME_CANDIDATES = [
    'llm_settings.ini',
    'llm_settings.local.ini',
    'llm_settings.dev.ini'
]

@dataclass
class LLMConfig:
    enabled: bool = False
    provider: str = 'openai'
    model: str = 'gpt-4o-mini'
    api_key: str | None = None
    api_base: str | None = None
    azure_deployment: str | None = None
    style: str = 'coach'
    temperature: float = 0.4
    max_tokens: int = 600
    language: str = 'auto'
    timeout: int = 18
    allow_fallback: bool = True
    system_prompt: str | None = None
    refine_template: str | None = None

    def resolve_language(self, evaluation_language: str) -> str:
        if self.language and self.language != 'auto':
            return self.language
        return evaluation_language or 'zh'

    @property
    def is_real_call(self) -> bool:
        return self.enabled and bool(self.api_key)


def _locate_config(base_dir: str) -> Optional[str]:
    for name in CONFIG_FILENAME_CANDIDATES:
        path = os.path.join(base_dir, name)
        if os.path.isfile(path):
            return path
    return None


@lru_cache(maxsize=1)
def load_llm_config() -> LLMConfig:
    base_dir = os.path.dirname(__file__)
    path = _locate_config(base_dir)
    if not path:
        # No user file; try environment variables fallback
        return LLMConfig(
            enabled=os.getenv('LLM_ENABLED', 'false').lower() == 'true',
            provider=os.getenv('LLM_PROVIDER', 'openai'),
            model=os.getenv('LLM_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('LLM_API_KEY'),
            api_base=os.getenv('LLM_API_BASE'),
            azure_deployment=os.getenv('LLM_AZURE_DEPLOYMENT'),
            style=os.getenv('LLM_STYLE', 'coach'),
            temperature=float(os.getenv('LLM_TEMPERATURE', '0.4')),\
            max_tokens=int(os.getenv('LLM_MAX_TOKENS', '600')),
            language=os.getenv('LLM_LANGUAGE', 'auto'),
            timeout=int(os.getenv('LLM_TIMEOUT', '18')),
            allow_fallback=os.getenv('LLM_ALLOW_FALLBACK', 'true').lower() == 'true',
            system_prompt=os.getenv('LLM_SYSTEM_PROMPT'),
            refine_template=os.getenv('LLM_REFINE_TEMPLATE')
        )

    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding='utf-8')
    except configparser.ParsingError:
        # Minimal manual parse: read lines and extract simple key=value under [llm] section.
        try:
            enabled = False
            provider = 'openai'
            style = 'coach'
            model = 'gpt-4o-mini'
            allow_fallback = True
            with open(path, 'r', encoding='utf-8') as f:
                in_llm = False
                for line in f:
                    t = line.strip()
                    if not t or t.startswith('#'):
                        continue
                    if t.startswith('['):
                        in_llm = (t.lower() == '[llm]')
                        continue
                    if in_llm and '=' in t:
                        k, v = [x.strip() for x in t.split('=', 1)]
                        lk = k.lower()
                        if lk == 'enabled':
                            enabled = v.lower() == 'true'
                        elif lk == 'provider':
                            provider = v or provider
                        elif lk == 'style':
                            style = v or style
                        elif lk == 'model':
                            model = v or model
                        elif lk == 'allow_fallback':
                            allow_fallback = v.lower() == 'true'
            return LLMConfig(enabled=enabled, provider=provider, model=model, style=style, allow_fallback=allow_fallback)
        except Exception:
            return LLMConfig(enabled=False)

    def get(section: str, key: str, default: Optional[str] = None):
        return parser.get(section, key, fallback=default).strip() if parser.has_option(section, key) else default

    enabled = get('llm', 'enabled', 'false').lower() == 'true'
    temperature_str = get('llm', 'temperature', '0.4') or '0.4'
    max_tokens_str = get('llm', 'max_tokens', '600') or '600'

    cfg = LLMConfig(
        enabled=enabled,
        provider=get('llm', 'provider', 'openai') or 'openai',
        model=get('llm', 'model', 'gpt-4o-mini') or 'gpt-4o-mini',
        api_key=get('llm', 'api_key') or None,
        api_base=get('llm', 'api_base') or None,
        azure_deployment=get('llm', 'azure_deployment') or None,
        style=get('llm', 'style', 'coach') or 'coach',
        temperature=float(temperature_str),
        max_tokens=int(max_tokens_str),
        language=get('llm', 'language', 'auto') or 'auto',
        timeout=int(get('llm', 'timeout', '18') or '18'),
        allow_fallback=(get('llm', 'allow_fallback', 'true') or 'true').lower() == 'true',
        system_prompt=get('prompt', 'system'),
        refine_template=get('prompt', 'refine_template')
    )

    # Language specific overrides
    lang_key = cfg.resolve_language('zh')
    if lang_key.startswith('zh'):
        sys_override = get('prompt', 'system_zh')
        ref_override = get('prompt', 'refine_template_zh')
    else:
        sys_override = get('prompt', 'system_en')
        ref_override = get('prompt', 'refine_template_en')
    if sys_override:
        cfg.system_prompt = sys_override
    if ref_override:
        cfg.refine_template = ref_override

    return cfg


def reload_llm_config():
    load_llm_config.cache_clear()  # type: ignore
    return load_llm_config()

from __future__ import annotations
import json, os, hashlib, time, re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class RefineResult:
    refined_action_summary: Optional[str]
    stage_suggestions: Dict[str, str]
    training_key_issues: List[str]
    training_drills: List[str]
    training_next_steps: List[str]
    raw_provider_response: Optional[dict] = None

class _BaseProvider:
    def call(self, system_prompt: str, user_content: str, timeout: float = 12.0) -> str:
        raise NotImplementedError

class DummyProvider(_BaseProvider):
    def call(self, system_prompt: str, user_content: str, timeout: float = 12.0) -> str:
        payload = json.loads(user_content)
        stages = payload.get('stages', [])
        result = {
            'refined_action_summary': 'Preliminary automated coaching summary (dummy provider).',
            'stages': {s['stage_key']: {'refined_suggestion': s.get('raw_suggestion') or 'No change'} for s in stages},
            'training': {
                'key_issues': payload.get('training', {}).get('key_issues', []),
                'improvement_drills': payload.get('training', {}).get('improvement_drills', []),
                'next_steps': payload.get('training', {}).get('next_steps', [])
            }
        }
        return json.dumps(result, ensure_ascii=False)

class AzureOpenAIProvider(_BaseProvider):
    """Provider supporting both legacy 'azure-ai-openai' preview SDK and new 'openai' Azure pattern.

    Tries import order:
      1. azure.ai.openai (preview SDK) -> OpenAIClient
      2. openai (>=1.0) AzureOpenAI client
    """
    def __init__(self):
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        if not all([endpoint, api_key, deployment]):
            missing = [k for k,v in [('AZURE_OPENAI_ENDPOINT',endpoint),('AZURE_OPENAI_API_KEY',api_key),('AZURE_OPENAI_DEPLOYMENT',deployment)] if not v]
            raise RuntimeError(f"Missing Azure OpenAI env vars: {', '.join(missing)}")
        self._deployment = deployment
        self._mode = None  # 'preview' | 'openai'
        # Try preview SDK first
        client = None
        try:  # preview SDK
            from azure.ai.openai import OpenAIClient  # type: ignore
            try:
                from azure.core.credentials import AzureKeyCredential  # type: ignore
                credential = AzureKeyCredential(api_key)
            except Exception:
                credential = api_key  # fallback; some earlier betas accepted raw key
            client = OpenAIClient(endpoint=endpoint, credential=credential, api_version=api_version)
            self._mode = 'preview'
        except Exception:
            try:  # new unified openai library with Azure flavor
                from openai import AzureOpenAI  # type: ignore
                client = AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=endpoint)
                self._mode = 'openai'
            except Exception as e2:  # pragma: no cover
                raise RuntimeError("Neither 'azure-ai-openai' nor 'openai' Azure client is available. Install one: 'pip install azure-ai-openai' or 'pip install openai'. Original error: " + str(e2))
        self._client = client

    def call(self, system_prompt: str, user_content: str, timeout: float = 12.0) -> str:
        try:
            if self._mode == 'preview':
                try:
                    response = self._client.chat.completions.create(  # type: ignore
                        model=self._deployment,
                        messages=[
                            {'role': 'system', 'content': system_prompt},
                            {'role': 'user', 'content': user_content}
                        ],
                        temperature=0.4,
                        max_tokens=800,
                        timeout=timeout
                    )
                except Exception as e_first:
                    # 温度不支持或参数不支持时去掉 temperature 重试
                    if "temperature" in str(e_first).lower():
                        response = self._client.chat.completions.create(  # type: ignore
                            model=self._deployment,
                            messages=[
                                {'role': 'system', 'content': system_prompt},
                                {'role': 'user', 'content': user_content}
                            ],
                            max_tokens=800,
                            timeout=timeout
                        )
                    else:
                        raise
                return response.choices[0].message.content  # type: ignore
            else:  # openai new
                # Newer Azure OpenAI (with unified openai lib) rejects max_tokens; use max_completion_tokens
                kwargs = {
                    'model': self._deployment,
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_content}
                    ],
                    'temperature': 0.4,
                    'max_completion_tokens': 800,
                }
                try:
                    response = self._client.chat.completions.create(**kwargs)  # type: ignore
                except Exception as e_first:
                    # Fallback try legacy param name if environment still expects max_tokens
                    msg_low = str(e_first).lower()
                    if 'max_completion_tokens' in msg_low:
                        kwargs.pop('max_completion_tokens', None)
                        kwargs['max_tokens'] = 800
                        response = self._client.chat.completions.create(**kwargs)  # type: ignore
                    elif 'temperature' in msg_low:
                        # Remove temperature and retry original tokens strategy
                        kwargs.pop('temperature', None)
                        try:
                            response = self._client.chat.completions.create(**kwargs)  # type: ignore
                        except Exception as e_second:
                            # Also try switching tokens param name if still failing
                            if 'max_completion_tokens' in kwargs:
                                mc = kwargs.pop('max_completion_tokens')
                                kwargs['max_tokens'] = mc
                            response = self._client.chat.completions.create(**kwargs)  # type: ignore
                    else:
                        raise
                return response.choices[0].message.content  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI call failed: {e}")

class SuggestionRefiner:
    def __init__(self, enable: bool = True, use_cache: bool = True):
        self.enable = enable and os.getenv('ENABLE_LLM_REFINEMENT', '0') in ('1','true','True')
        # Allow disabling cache via env
        no_cache_env = os.getenv('LLM_NO_CACHE', '0').lower() in ('1','true','yes')
        self.use_cache = use_cache and (not no_cache_env)
        self._cache_dir = os.path.join('.cache', 'llm')
        os.makedirs(self._cache_dir, exist_ok=True)
        self._provider: _BaseProvider
        self._debug = os.getenv('LLM_DEBUG', '0').lower() in ('1','true','yes')
        if not self.enable:
            self._provider = DummyProvider()
        else:
            try:
                self._provider = AzureOpenAIProvider()
            except Exception as e:
                print(f"[LLM] Falling back to DummyProvider: {e}")
                self._provider = DummyProvider()
        if self._debug:
            print(f"[LLM][DEBUG] enable={self.enable} provider={self._provider.__class__.__name__} use_cache={self.use_cache}")

    # Public API -----------------------------------------------------
    def refine_from_state(self, state) -> Optional[RefineResult]:
        try:
            payload = self._build_payload(state)
            return self._refine(payload)
        except Exception as e:
            print(f"[LLM] refine_from_state failed: {e}")
            return None

    # Internal -------------------------------------------------------
    def _build_payload(self, state) -> dict:
        stages = []
        for sk, sr in state.stages.items():
            metrics_data = []
            for m in sr.metrics[:6]:  # cap per stage
                metrics_data.append({
                    'name': m.name,
                    'status': m.status,
                    'user_value': round(m.user_value, 2) if m.user_value is not None else None,
                    'std_value': round(m.std_value, 2) if m.std_value is not None else None,
                    'deviation': round(m.deviation, 2) if m.deviation is not None else None,
                    'unit': m.unit
                })
            stages.append({
                'stage_key': sk,
                'score': sr.score,
                'raw_suggestion': sr.suggestion,
                'metrics': metrics_data
            })
        training = {}
        if state.training:
            training = {
                'key_issues': state.training.key_issues,
                'improvement_drills': state.training.improvement_drills,
                'next_steps': state.training.next_steps
            }
        return {
            'action': state.action,
            'sport': state.sport,
            'overall_score': state.overall_score,
            'stages': stages,
            'training': training,
            'output_schema': {
                'refined_action_summary': 'string',
                'stages': {'<stage_key>': {'refined_suggestion': 'string'}},
                'training': {
                    'key_issues': ['string'],
                    'improvement_drills': ['string'],
                    'next_steps': ['string']
                }
            },
            'style_guidelines': [
                'Use concise actionable coaching language',
                'Do not invent metrics not provided',
                'No markdown, no emojis',
                'Group related issues logically'
            ]
        }

    def _cache_path(self, payload: dict) -> str:
        h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
        return os.path.join(self._cache_dir, f"{h}.json")

    def _refine(self, payload: dict) -> RefineResult:
        cache_file = self._cache_path(payload)
        if self.use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                if self._debug:
                    print(f"[LLM][DEBUG] cache hit {os.path.basename(cache_file)}")
                return self._parse_result(cached, raw=cached)
            except Exception:
                pass
        system_prompt = (
            "You are a sports movement analysis assistant focusing on badminton forehand clear. "
            "Return ONLY valid JSON with no extra commentary."
        )
        user_content = json.dumps(payload, ensure_ascii=False)
        attempts = 0
        data = None
        last_err: Optional[Exception] = None
        while attempts < 3 and data is None:
            try:
                start_ts = time.time()
                resp_text = self._provider.call(system_prompt, user_content)
                duration = time.time() - start_ts
                if self._debug:
                    snippet = (resp_text or '').strip().replace('\n', ' ')[:200]
                    print(f"[LLM][DEBUG] attempt={attempts+1} raw len={len(resp_text) if resp_text else 0} time={duration:.2f}s snippet={snippet}")
                data = self._try_parse_json(resp_text)
                if data is None or not isinstance(data, dict):
                    raise ValueError('Primary JSON parse failed')
            except Exception as e:
                last_err = e
                if self._debug:
                    print(f"[LLM][DEBUG] parse/resp failure attempt {attempts+1}: {e}")
                # exponential backoff small (0.4, 0.8)
                if attempts < 2:
                    time.sleep(0.4 * (2 ** attempts))
                data = None
            finally:
                attempts += 1
        if data is None:
            print(f"[LLM] provider error or JSON parse failed after retries: {last_err}")
            data = {
                'refined_action_summary': payload.get('action') + ' evaluation summary.',
                'stages': {s['stage_key']: {'refined_suggestion': (s.get('raw_suggestion') or 'No immediate issues detected.')} for s in payload['stages']},
                'training': payload.get('training', {})
            }
        if self.use_cache:
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
        return self._parse_result(data, raw=data)

    # More robust JSON extraction (handles code fences and extra text)
    def _try_parse_json(self, text: Optional[str]) -> Optional[dict]:
        if not text:
            return None
        text = text.strip()
        # If already clean JSON
        try:
            return json.loads(text)
        except Exception:
            pass
        # Remove code fences ```json ... ``` or ``` ... ```
        fenced = re.findall(r"```[a-zA-Z]*\n([\s\S]*?)```", text)
        for block in fenced:
            block_stripped = block.strip()
            try:
                return json.loads(block_stripped)
            except Exception:
                continue
        # Braces balancing scan
        first = text.find('{')
        last = text.rfind('}')
        if first != -1 and last != -1 and last > first:
            candidate = text[first:last+1]
            try:
                return json.loads(candidate)
            except Exception:
                # attempt incremental shrink from end
                for i in range(last, first, -1):
                    cand2 = text[first:i]
                    if cand2.count('{') == cand2.count('}'):
                        try:
                            return json.loads(cand2)
                        except Exception:
                            pass
        return None

    def _parse_result(self, data: dict, raw: dict) -> RefineResult:
        refined_summary = data.get('refined_action_summary')
        stage_obj = data.get('stages', {}) or {}
        tr = data.get('training', {}) or {}
        return RefineResult(
            refined_action_summary=refined_summary,
            stage_suggestions={k: (v.get('refined_suggestion') if isinstance(v, dict) else '') for k, v in stage_obj.items()},
            training_key_issues=tr.get('key_issues', []),
            training_drills=tr.get('improvement_drills', []),
            training_next_steps=tr.get('next_steps', []),
            raw_provider_response=raw
        )

__all__ = ['SuggestionRefiner', 'RefineResult']

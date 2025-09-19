from __future__ import annotations
from typing import Optional, Dict, Any

class AzureOpenAIProvider:
    """Lightweight Azure OpenAI wrapper (chat completions style).
    Falls back gracefully if SDK missing or misconfigured.
    """
    def __init__(self, api_key: str, api_base: str, deployment: str, api_version: str = '2024-02-15-preview', timeout: int = 18):
        self.api_key = api_key
        self.api_base = api_base.rstrip('/') if api_base else ''
        self.deployment = deployment
        self.api_version = api_version
        self.timeout = timeout
        self._client = None
        self._ready = False
        self._init_error: Optional[str] = None
        if not (api_key and api_base and deployment):
            self._init_error = 'Missing azure config parameters'
            return
        try:
            # Lazy import SDK if available
            import openai  # type: ignore
            openai.api_type = 'azure'
            openai.api_base = self.api_base
            openai.api_key = self.api_key
            openai.api_version = self.api_version
            self._client = openai
            self._ready = True
        except Exception as e:  # broad by design to keep fallback path
            self._init_error = str(e)
            self._ready = False

    def available(self) -> bool:
        return self._ready

    def reason_unavailable(self) -> Optional[str]:
        if self._ready:
            return None
        return self._init_error or 'Unknown'

    def refine(self, system_prompt: str, user_content: str, temperature: float = 0.4, max_tokens: int = 600) -> Optional[str]:
        if not self._ready or not self._client:
            return None
        try:
            # ChatCompletion style legacy call (SDK differences may require adaptation)
            response = self._client.ChatCompletion.create(
                engine=self.deployment,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ]
            )
            # Extract
            if response and response.get('choices'):
                return response['choices'][0]['message'].get('content')
        except Exception:
            return None
        return None

__all__ = ['AzureOpenAIProvider']

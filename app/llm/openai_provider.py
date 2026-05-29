"""OpenAI 공급자."""
from __future__ import annotations

import os
from typing import Any

from .base import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OPENAI_API_KEY 가 설정되지 않았습니다.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMError("openai 패키지가 필요합니다: pip install openai") from exc
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"OpenAI 호출 실패: {exc}") from exc
        text = resp.choices[0].message.content or "{}"
        return self._extract_json(text)

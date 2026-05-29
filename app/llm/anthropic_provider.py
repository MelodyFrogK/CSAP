"""Anthropic(Claude) 공급자."""
from __future__ import annotations

import os
from typing import Any

from .base import LLMError, LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY 가 설정되지 않았습니다.")
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMError("anthropic 패키지가 필요합니다: pip install anthropic") from exc
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        try:
            resp = self._client.messages.create(
                model=self._model,
                max_tokens=2000,
                temperature=0,
                system=[
                    {
                        "type": "text",
                        "text": system,
                        # 시스템 프롬프트는 항목마다 동일하므로 캐싱
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user}],
            )
        except Exception as exc:  # noqa: BLE001 - 공급자 예외 래핑
            raise LLMError(f"Anthropic 호출 실패: {exc}") from exc
        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        return self._extract_json(text)

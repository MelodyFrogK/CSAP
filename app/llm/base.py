"""LLM 공급자 인터페이스.

모든 공급자는 `complete_json`을 구현한다. 시스템/유저 프롬프트를 받아
JSON 객체(dict)를 돌려준다. 공급자별 JSON 모드/파싱 차이를 여기서 흡수한다.
"""
from __future__ import annotations

import abc
import json
import re
from typing import Any


class LLMError(RuntimeError):
    """공급자 호출 실패."""


class LLMProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        """system+user 프롬프트로 호출하고 JSON dict를 반환한다."""

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        """모델 출력에서 첫 JSON 객체를 견고하게 추출한다."""
        text = text.strip()
        # 코드펜스 제거
        fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence:
            text = fence.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 중괄호 균형 맞춰 첫 객체만 추출
        start = text.find("{")
        if start == -1:
            raise LLMError(f"JSON 객체를 찾지 못했습니다: {text[:200]!r}")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start : i + 1])
                    except json.JSONDecodeError as exc:
                        raise LLMError(f"JSON 파싱 실패: {exc}") from exc
        raise LLMError("닫히지 않은 JSON 객체")

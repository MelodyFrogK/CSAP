"""테스트/오프라인용 더미 공급자.

API 키 없이 파이프라인 전체를 검증할 수 있도록, 제공된 컨텍스트를 바탕으로
규칙 기반의 그럴듯한 결과를 만들어 낸다. 실제 분석 품질은 없으며 데모 전용.
"""
from __future__ import annotations

from typing import Any

from .base import LLMProvider


class EchoProvider(LLMProvider):
    name = "echo"

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        has_context = "관련 문서 발췌" in user and "(관련 발췌 없음)" not in user
        if has_context:
            return {
                "status": "[데모 출력] 제출 문서에서 관련 내용이 확인됩니다. 실제 LLM 연결 시 "
                "문서 근거를 요약한 현황이 여기에 작성됩니다.",
                "gaps": "[데모 출력] 세부 절차/주기/책임자 명시 여부를 점검하세요.",
                "compliance": "부분충족",
                "evidence": "제출 문서 발췌 일부",
            }
        return {
            "status": "",
            "gaps": "[데모 출력] 제출 문서에서 관련 근거를 찾지 못했습니다. 해당 항목에 대한 "
            "정책/절차 문서를 보완하세요.",
            "compliance": "확인불가",
            "evidence": "",
        }

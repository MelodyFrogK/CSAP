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
                "operation": "운영",
                "status": "[데모 출력] 제출 문서에서 관련 이행 내용이 확인됩니다. 실제 LLM "
                "연결 시 문서 근거를 요약한 운영 현황이 여기에 작성됩니다.",
                "related_docs": "[데모] 제출 문서(정책/지침)",
                "evidence": "[데모] 관련 화면/파일",
                "improvement": "[데모 출력] 세부 절차·주기·책임자 명시 여부를 점검하세요.",
            }
        return {
            "operation": "확인불가",
            "status": "",
            "related_docs": "",
            "evidence": "",
            "improvement": "[데모 출력] 제출 문서에서 근거를 찾지 못했습니다. 해당 점검항목 "
            "관련 정책/절차/증적을 보완하세요.",
        }

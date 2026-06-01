"""테스트/오프라인용 더미 공급자.

API 키 없이 파이프라인 전체를 검증할 수 있도록, 점검항목의 핵심어가 제출 문서
발췌에 실제로 등장하는지로 운영/확인불가를 가른다. 실제 분석 품질은 없으며 데모 전용.
(실제 LLM 연결 시 app/llm/factory.py 에서 anthropic/openai 로 전환)
"""
from __future__ import annotations

import re
from typing import Any

from .base import LLMProvider

_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
_STOP = {"클라우드", "정보보호", "서비스", "관련", "있는가", "하고", "위한", "통제", "점검", "항목"}


def _tokens(text: str) -> set[str]:
    return {t for t in (m.group() for m in _TOKEN_RE.finditer(text)) if len(t) > 1 and t not in _STOP}


class EchoProvider(LLMProvider):
    name = "echo"

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        check = ""
        for line in user.splitlines():
            if line.startswith("- 점검항목(질문):"):
                check = line.split(":", 1)[1]
                break
        excerpt = user.split("# 관련 문서 발췌", 1)[-1]
        has_excerpt = "(관련 발췌 없음)" not in excerpt

        q = _tokens(check)
        e = _tokens(excerpt)
        overlap = len(q & e) / len(q) if q else 0.0

        if has_excerpt and overlap >= 0.25:
            return {
                "operation": "Y",
                "assessment": "운영",
                "status": "[데모] 제출 문서에서 관련 이행 내용이 확인됩니다(핵심어 일치). "
                "실제 LLM 연결 시 근거를 요약한 운영 현황이 작성됩니다.",
                "related_docs": "[데모] 제출 문서(정책/지침)",
                "evidence": "[데모] 관련 화면/파일",
                "basis": "[데모] 점검항목 핵심어가 발췌에서 확인됨.",
                "improvement": "[데모] 세부 절차·주기·책임자 명시 여부를 점검하세요.",
                "recommended": "[데모] 관련 정책/지침과 증적 파일을 색인하여 준비하세요.",
                "review_needed": "",
            }
        return {
            "operation": "",
            "assessment": "확인불가",
            "status": "",
            "related_docs": "",
            "evidence": "",
            "basis": "[데모] 발췌에서 이 점검항목의 직접 근거를 찾지 못함.",
            "improvement": "[데모] 제출 문서에서 이 점검항목에 대한 직접 근거를 찾지 못했습니다. "
            "관련 정책/절차/증적을 보완하세요.",
            "recommended": "[데모] 관련 정책/지침·증적 문서를 준비하세요.",
            "review_needed": "Y",
        }

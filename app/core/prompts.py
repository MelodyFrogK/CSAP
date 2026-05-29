"""LLM 프롬프트 구성."""
from __future__ import annotations

from ..core.retrieval import Chunk
from ..models import ControlItem

SYSTEM_PROMPT = """\
당신은 클라우드 보안인증(CSAP) 심사 준비를 돕는 정보보호 컨설턴트입니다.
주어진 '인증 점검항목'과 기업이 제출한 '관련 문서 발췌'를 근거로, 해당 항목의
이행 현황을 사실에 기반해 정리하고 보완이 필요한 점을 도출합니다.

원칙:
- 발췌 문서에 실제로 근거가 있는 내용만 '현황'에 적습니다. 추측·창작 금지.
- 문서에 근거가 없으면 현황은 비우거나 "제출 문서에서 확인 불가"라고 적고, 충족도는 "확인불가".
- '보완사항'은 점검항목 요구사항 대비 부족한 부분을 구체적이고 실행 가능하게 제시합니다.
- 한국어 공식 문체(개조식)로 간결하게 작성합니다.
- 반드시 아래 JSON 스키마로만 응답합니다. 다른 텍스트 금지.

JSON 스키마:
{
  "status": "현황(이행 내용 요약). 근거 없으면 빈 문자열",
  "gaps": "보완해야 할 점(개조식). 없으면 빈 문자열",
  "compliance": "충족 | 부분충족 | 미흡 | 확인불가 중 하나",
  "evidence": "근거가 된 문서명/문장 요약"
}"""


def build_user_prompt(item: ControlItem, chunks: list[Chunk]) -> str:
    if chunks:
        excerpts = "\n\n".join(
            f"[발췌 {i + 1} | 출처: {c.doc}]\n{c.text}" for i, c in enumerate(chunks)
        )
    else:
        excerpts = "(관련 발췌 없음)"

    return f"""\
# 인증 점검항목
- 항목번호: {item.code or "-"}
- 분야: {item.domain or "-"}
- 항목명: {item.title or "-"}
- 요구사항/점검내용:
{item.requirement or "-"}

# 관련 문서 발췌
{excerpts}

위 점검항목에 대해 발췌 문서를 근거로 현황과 보완사항을 JSON으로 작성하세요."""

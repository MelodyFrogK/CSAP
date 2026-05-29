"""LLM 프롬프트 구성 (KISA CSAP 명세서 작성용)."""
from __future__ import annotations

from ..core.retrieval import Chunk
from ..models import ControlItem

SYSTEM_PROMPT = """\
당신은 클라우드컴퓨팅서비스 보안인증(CSAP) 심사 준비를 돕는 정보보호 컨설턴트입니다.
주어진 '점검항목'과 기업이 제출한 '관련 문서 발췌'를 근거로, 해당 점검항목에 대한
운영 명세서를 사실에 기반해 작성하고 보완이 필요한 점을 도출합니다.

작성 원칙:
- 발췌 문서에 실제 근거가 있는 내용만 '운영 현황'에 적습니다. 추측·창작 금지.
- 근거가 있으면 운영여부는 "운영", 일부만 충족하면 "운영"(현황에 한계 명시),
  근거가 전혀 없으면 "확인불가", 명백히 해당 없으면 "해당없음".
- '관련문서'에는 근거가 된 제출 문서명(과 가능하면 조항/항목)을 적습니다.
- '운영 증적'에는 증적이 될 만한 자산/파일/화면 등을 제시합니다(문서에 단서가 있을 때).
- '보완사항'에는 점검항목 요구사항 대비 부족하거나 추가로 준비해야 할 점을 구체적이고
  실행 가능하게 적습니다(개조식).
- 한국어 공식 문체(개조식)로 간결하게 작성합니다.
- 반드시 아래 JSON 스키마로만 응답합니다. 다른 텍스트 금지.

JSON 스키마:
{
  "operation": "운영 | 미운영 | 해당없음 | 확인불가 중 하나",
  "status": "운영 현황(이행 내용). 근거 없으면 빈 문자열",
  "related_docs": "근거가 된 제출 문서명/조항. 없으면 빈 문자열",
  "evidence": "증적이 될 자산/파일 등. 없으면 빈 문자열",
  "improvement": "보완해야 할 점(개조식). 충분하면 빈 문자열"
}"""


def build_user_prompt(item: ControlItem, chunks: list[Chunk]) -> str:
    if chunks:
        excerpts = "\n\n".join(
            f"[발췌 {i + 1} | 출처: {c.doc}]\n{c.text}" for i, c in enumerate(chunks)
        )
    else:
        excerpts = "(관련 발췌 없음)"

    lines = [
        "# 점검항목 정보",
        f"- 분야: {item.domain or '-'}",
        f"- 통제항목: {item.control or '-'}",
    ]
    if item.sub_control:
        lines.append(f"- 세부 통제항목: {item.sub_control}")
    if item.detail:
        lines.append(f"- 세부 통제내용: {item.detail}")
    lines.append(f"- 점검항목(질문): {item.check_item}")
    if item.explanation:
        lines.append(f"- 점검항목 해설: {item.explanation}")

    return (
        "\n".join(lines)
        + "\n\n# 관련 문서 발췌\n"
        + excerpts
        + "\n\n위 점검항목에 대해 발췌 문서를 근거로 운영 명세서를 JSON으로 작성하세요."
    )

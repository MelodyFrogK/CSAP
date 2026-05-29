"""도메인 데이터 모델."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ControlItem(BaseModel):
    """CSAP 명세서의 점검(통제) 항목 한 줄."""

    row: int = Field(..., description="엑셀 원본 행 번호(1-based)")
    code: str = Field("", description="항목 코드 (예: 1.1.1)")
    domain: str = Field("", description="통제 분야/구분")
    title: str = Field("", description="항목명")
    requirement: str = Field("", description="점검내용 / 인증기준 요구사항")

    def context_text(self) -> str:
        parts = [p for p in (self.code, self.domain, self.title, self.requirement) if p]
        return " / ".join(parts)


class ItemResult(BaseModel):
    """LLM이 한 항목에 대해 작성한 결과."""

    row: int
    status: str = Field("", description="현황(작성 내용)")
    gaps: str = Field("", description="보완해야 할 점")
    compliance: str = Field("", description="충족도: 충족 / 부분충족 / 미흡 / 확인불가")
    evidence: str = Field("", description="근거가 된 문서 인용/출처")


class TemplateLayout(BaseModel):
    """감지된 템플릿 열 배치."""

    sheet: str
    header_row: int
    data_start_row: int
    col_code: Optional[int] = None
    col_domain: Optional[int] = None
    col_title: Optional[int] = None
    col_requirement: Optional[int] = None
    # 결과를 써넣을(없으면 새로 추가할) 열
    col_status: Optional[int] = None
    col_gaps: Optional[int] = None
    col_compliance: Optional[int] = None
    col_evidence: Optional[int] = None

"""도메인 데이터 모델 (KISA CSAP 명세서 구조 기준)."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ControlItem(BaseModel):
    """명세서의 점검항목 한 줄(점검항목 = LLM 작성 단위)."""

    sheet: str = Field(..., description="시트명(보호조치 분류)")
    row: int = Field(..., description="엑셀 원본 행 번호(1-based)")

    domain: str = Field("", description="분야")
    control: str = Field("", description="통제항목(중분류)")
    sub_control: str = Field("", description="세부 통제항목 코드/명")
    detail: str = Field("", description="세부 통제내용")
    related_law: str = Field("", description="관련 법규")
    check_item: str = Field("", description="점검항목(점검 질문) — 작성 기준")
    explanation: str = Field("", description="점검항목 해설(최신본)")

    def context_text(self) -> str:
        """근거 검색용 질의 텍스트."""
        parts = [p for p in (self.domain, self.control, self.sub_control, self.detail, self.check_item) if p]
        return " ".join(parts)


class ItemResult(BaseModel):
    """LLM이 한 점검항목에 대해 작성한 결과."""

    sheet: str
    row: int
    # ── 기존 폼(템플릿에 이미 있는 결과 열) ──
    operation: str = Field("", description="운영여부: Y / N / 해당없음 (확인불가 시 공백)")
    status: str = Field("", description="운영 현황(이행 내용, 육하원칙 개조식)")
    related_docs: str = Field("", description="관련문서(정책/지침 + 세부조항번호)")
    evidence: str = Field("", description="운영 증적(자산/파일 등)")
    # ── 오른쪽 추가 열(자동작성) ──
    assessment: str = Field("", description="자동 판정(상세): 운영/부분운영/미운영/해당없음/확인불가")
    basis: str = Field("", description="판단 근거(해설 요건 대조)")
    improvement: str = Field("", description="보완사항")
    recommended: str = Field("", description="준비 권장 증적·문서(색인 예시)")
    review_needed: str = Field("", description="검토 필요: Y / 공백")


class SheetLayout(BaseModel):
    """한 시트의 감지된 열 배치."""

    sheet: str
    header_row: int
    data_start_row: int

    # 입력 열
    col_domain: Optional[int] = None
    col_control: Optional[int] = None
    col_sub_control: Optional[int] = None
    col_detail: Optional[int] = None
    col_related_law: Optional[int] = None
    col_check: Optional[int] = None
    col_explanation: Optional[int] = None

    # 결과 열(템플릿에 이미 존재)
    col_operation: Optional[int] = None
    col_status: Optional[int] = None
    col_related_docs: Optional[int] = None
    col_evidence: Optional[int] = None
    col_person: Optional[int] = None

    # 오른쪽 추가 열(자동작성)
    col_assessment: Optional[int] = None
    col_basis: Optional[int] = None
    col_improvement: Optional[int] = None
    col_recommended: Optional[int] = None
    col_review: Optional[int] = None

    def is_spec_sheet(self) -> bool:
        """점검항목 열이 있으면 명세 시트로 간주."""
        return self.col_check is not None

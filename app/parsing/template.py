"""CSAP 명세서 엑셀 템플릿을 읽어 점검항목 목록과 열 배치를 파악한다.

KISA 양식은 버전마다 헤더 문구/열 위치가 다를 수 있으므로, 헤더 행을
키워드로 탐지하고 열을 매핑한다. 매핑이 안 되면 호출 측에서 직접 지정한다.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from ..models import ControlItem, TemplateLayout

# 헤더 후보 키워드 (소문자/공백 제거 후 부분일치)
_HEADER_KEYWORDS = {
    "code": ["항목번호", "통제번호", "번호", "no", "코드", "분류번호", "항목코드"],
    "domain": ["분야", "구분", "영역", "통제분야", "부문", "범주", "category", "domain"],
    "title": ["항목", "통제항목", "점검항목", "항목명", "통제명", "제목"],
    "requirement": [
        "점검내용",
        "인증기준",
        "세부점검항목",
        "요구사항",
        "상세내용",
        "점검사항",
        "내용",
        "기준",
    ],
    "status": ["현황", "운영현황", "작성", "이행현황", "구현내용", "답변", "현황및근거"],
    "gaps": ["보완", "미흡", "개선", "조치사항", "보완사항", "결함"],
    "compliance": ["충족", "이행여부", "결과", "판정", "준수", "적합"],
    "evidence": ["근거", "증적", "증빙", "출처"],
}

_MAX_SCAN_ROWS = 30


def _norm(v: object) -> str:
    return str(v).replace(" ", "").replace("\n", "").lower() if v is not None else ""


def _match_field(header_text: str) -> str | None:
    """헤더 셀 문구가 어떤 필드에 해당하는지 추정. 더 구체적인 것부터 매칭."""
    # requirement/title이 'title' 키워드와 겹치므로 우선순위 조정
    order = ["status", "gaps", "compliance", "evidence", "requirement", "code", "domain", "title"]
    for field in order:
        for kw in _HEADER_KEYWORDS[field]:
            if kw in header_text:
                return field
    return None


def detect_layout(ws: Worksheet) -> TemplateLayout:
    """헤더 행을 찾아 열 배치를 추정한다."""
    best_row = 1
    best_score = -1
    best_map: dict[str, int] = {}

    for r in range(1, min(_MAX_SCAN_ROWS, ws.max_row) + 1):
        mapping: dict[str, int] = {}
        for c in range(1, ws.max_column + 1):
            field = _match_field(_norm(ws.cell(row=r, column=c).value))
            if field and field not in mapping:
                mapping[field] = c
        score = len(mapping)
        if score > best_score:
            best_score = score
            best_row = r
            best_map = mapping

    layout = TemplateLayout(
        sheet=ws.title,
        header_row=best_row,
        data_start_row=best_row + 1,
        col_code=best_map.get("code"),
        col_domain=best_map.get("domain"),
        col_title=best_map.get("title"),
        col_requirement=best_map.get("requirement"),
        col_status=best_map.get("status"),
        col_gaps=best_map.get("gaps"),
        col_compliance=best_map.get("compliance"),
        col_evidence=best_map.get("evidence"),
    )
    return layout


def read_items(path: str | Path, sheet: str | None = None) -> tuple[list[ControlItem], TemplateLayout]:
    """템플릿에서 점검항목 목록과 레이아웃을 읽는다."""
    wb = load_workbook(str(path), data_only=True)
    ws = wb[sheet] if sheet else wb.active
    layout = detect_layout(ws)

    items: list[ControlItem] = []
    for r in range(layout.data_start_row, ws.max_row + 1):
        def cell(col: int | None) -> str:
            if not col:
                return ""
            v = ws.cell(row=r, column=col).value
            return str(v).strip() if v is not None else ""

        code = cell(layout.col_code)
        domain = cell(layout.col_domain)
        title = cell(layout.col_title)
        requirement = cell(layout.col_requirement)

        # 완전 빈 행은 건너뛴다.
        if not any((code, domain, title, requirement)):
            continue

        items.append(
            ControlItem(
                row=r,
                code=code,
                domain=domain,
                title=title,
                requirement=requirement,
            )
        )
    return items, layout

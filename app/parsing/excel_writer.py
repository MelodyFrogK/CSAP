"""분석 결과를 원본 템플릿 엑셀에 써넣어 새 파일로 저장한다.

원본 서식을 보존하기 위해 템플릿을 그대로 로드해 결과 열만 채운다.
결과 열이 템플릿에 없으면 마지막 열 뒤에 새 열(현황/보완/충족도/근거)을 추가한다.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from ..models import ItemResult, TemplateLayout

_RESULT_HEADERS = {
    "col_status": "현황(자동작성)",
    "col_gaps": "보완사항(자동작성)",
    "col_compliance": "충족도",
    "col_evidence": "근거",
}

_HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")
_WRAP = Alignment(wrap_text=True, vertical="top")


def write_results(
    template_path: str | Path,
    layout: TemplateLayout,
    results: dict[int, ItemResult],
    output_path: str | Path,
    sheet: str | None = None,
) -> Path:
    wb = load_workbook(str(template_path))
    ws = wb[sheet] if sheet else wb[layout.sheet]

    # 누락된 결과 열은 끝에 새로 만든다.
    next_col = ws.max_column + 1
    for attr, header in _RESULT_HEADERS.items():
        if getattr(layout, attr) is None:
            setattr(layout, attr, next_col)
            hcell = ws.cell(row=layout.header_row, column=next_col, value=header)
            hcell.font = Font(bold=True)
            hcell.fill = _HEADER_FILL
            hcell.alignment = _WRAP
            ws.column_dimensions[hcell.column_letter].width = 45
            next_col += 1

    for row, res in results.items():
        _set(ws, row, layout.col_status, res.status)
        _set(ws, row, layout.col_gaps, res.gaps)
        _set(ws, row, layout.col_compliance, res.compliance)
        _set(ws, row, layout.col_evidence, res.evidence)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    return output_path


def _set(ws, row: int, col: int | None, value: str) -> None:
    if not col:
        return
    cell = ws.cell(row=row, column=col, value=value)
    cell.alignment = _WRAP

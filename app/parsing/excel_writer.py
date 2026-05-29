"""분석 결과를 원본 KISA 명세서에 써넣어 새 파일로 저장한다.

원본 서식을 보존하기 위해 템플릿을 그대로 로드한다. 결과는 템플릿에 이미 있는
운영여부/운영현황/관련문서/운영증적 열에 채우고, 없는 '보완사항' 열만 끝에 추가한다.
증적확인 담당자 열은 사람이 채워야 하므로 건드리지 않는다.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from ..models import ItemResult, SheetLayout

_IMPROVEMENT_HEADER = "보완사항(자동작성)"
_HEADER_FILL = PatternFill("solid", fgColor="FFF2CC")
_WRAP = Alignment(wrap_text=True, vertical="top")


def write_results(
    template_path: str | Path,
    layouts: dict[str, SheetLayout],
    results: list[ItemResult],
    output_path: str | Path,
) -> Path:
    wb = load_workbook(str(template_path))

    # 시트별로 '보완사항' 열을 (없으면) 추가한다.
    for sheet, layout in layouts.items():
        ws = wb[sheet]
        if layout.col_improvement is None:
            col = ws.max_column + 1
            layout.col_improvement = col
            hcell = ws.cell(row=layout.header_row, column=col, value=_IMPROVEMENT_HEADER)
            hcell.font = Font(bold=True)
            hcell.fill = _HEADER_FILL
            hcell.alignment = _WRAP
            ws.column_dimensions[hcell.column_letter].width = 50

    for res in results:
        layout = layouts.get(res.sheet)
        if not layout:
            continue
        ws = wb[res.sheet]
        _set(ws, res.row, layout.col_operation, res.operation)
        _set(ws, res.row, layout.col_status, res.status)
        _set(ws, res.row, layout.col_related_docs, res.related_docs)
        _set(ws, res.row, layout.col_evidence, res.evidence)
        _set(ws, res.row, layout.col_improvement, res.improvement)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))
    return output_path


def _set(ws, row: int, col: int | None, value: str) -> None:
    if not col or value == "":
        return
    cell = ws.cell(row=row, column=col, value=value)
    cell.alignment = _WRAP

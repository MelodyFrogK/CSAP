"""데모용 CSAP 명세서 샘플 템플릿(.xlsx)을 생성한다.

실제 KISA 양식 레이아웃(헤더 4행, 보호조치별 시트)을 본떠 만든다. 실제 명세서를
보유하면 웹 UI에서 업로드하거나 data/sample_csap_template.xlsx 를 교체하면 된다.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample_csap_template.xlsx"

# 실제 KISA SaaS 표준 명세서(17열) 레이아웃을 본뜬 헤더. C열은 세부통제 코드(헤더 없음).
HEADERS = [
    "분야", "통제항목", "", "세부 통제내용", "관련 법규", "점검항목",
    "점검항목 해설(2024. 6.)", "점검항목 해설(2024. 7.)",
    "운영여부", "운영 현황",
    "관련문서\n(정책, 지침 등 세부조항번호까지)",
    "운영 증적\n(자산, 파일 등)",
    "증적확인 담당자\n(소속, 이름, 연락처)",
    "점검결과", "점검결과 근거", "심사위원",
]

# (분야, 통제항목, 세부통제코드, 세부통제내용, [점검항목들])
BLOCKS = [
    ("1. 정보보호 정책 및 조직", "1.1 정보보호 정책", "1.1.1 정보보호 정책 수립",
     "정보보호 정책을 문서화하고 정보보호 최고책임자의 승인을 받아야 한다.",
     ["1) 클라우드 정보보호 정책을 수립하고 관련 지침·절차를 문서화하고 있는가?",
      "2) 정보보호 정책은 정보보호 최고책임자의 제·개정 승인을 받고 있는가?"]),
    ("1. 정보보호 정책 및 조직", "1.2 정보보호 조직", "1.2.1 조직 구성",
     "정보보호 전담조직을 구성하고 정보보호 최고책임자를 임명하여야 한다.",
     ["1) 별도의 정보보호 실무조직을 구성하고 최고책임자를 임명하고 있는가?"]),
    ("4. 접근통제", "4.1 접근통제 정책", "4.1.1 계정 관리",
     "사용자 계정의 생성·변경·삭제 절차를 수립하고 최소권한을 적용하여야 한다.",
     ["1) 사용자 계정 등록·변경·삭제 절차를 수립하여 운영하는가?",
      "2) 관리자 및 원격 접근에 다중인증(MFA)을 적용하고 있는가?"]),
]

SHEETS = {
    "1. 관리적 보호조치": BLOCKS,
    "3. 기술적 보호조치": [
        ("9. 가상화 보안", "9.1 가상화 인프라", "9.1.1 가상자원 관리",
         "가상자원의 생성·변경·회수 등에 대한 보안 절차를 수립하여야 한다.",
         ["1) 가상자원의 생성·변경·회수 절차를 수립하여 운영하는가?",
          "2) 가상자원 간 접근통제 및 격리를 적용하고 있는가?"]),
    ],
}


def _build_sheet(ws, blocks):
    title_fill = PatternFill("solid", fgColor="305496")
    bold_white = Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.cell(row=1, column=1, value="클라우드 보안인증 평가방법 및 점검표").font = Font(bold=True)
    ws.merge_cells(start_row=1, end_row=1, start_column=1, end_column=len(HEADERS))
    ws.cell(row=3, column=1, value="클라우드컴퓨팅서비스 보안인증기준")
    ws.cell(row=3, column=9, value="클라우드컴퓨팅서비스 보안운영 명세서")
    ws.cell(row=3, column=14, value="서면 및 현장 평가")

    for c, h in enumerate(HEADERS, start=1):
        cell = ws.cell(row=4, column=c, value=h)
        cell.font = bold_white
        cell.fill = title_fill
        cell.alignment = center
    ws.merge_cells(start_row=4, end_row=4, start_column=2, end_column=3)  # 통제항목 B4:C4

    widths = [16, 16, 18, 36, 28, 46, 44, 44, 10, 30, 24, 22, 18, 12, 30, 12]
    for c, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(c)].width = w

    r = 5
    for domain, control, sub, detail, checks in blocks:
        first = True
        for q in checks:
            if first:
                ws.cell(row=r, column=1, value=domain).alignment = wrap
                ws.cell(row=r, column=2, value=control).alignment = wrap
                ws.cell(row=r, column=3, value=sub).alignment = wrap
                ws.cell(row=r, column=4, value=detail).alignment = wrap
                ws.cell(row=r, column=5, value="• 관련 법규(예시)").alignment = wrap
                first = False
            ws.cell(row=r, column=6, value=q).alignment = wrap
            ws.cell(row=r, column=7, value="∎ 관련 해설(2024.6 예시).").alignment = wrap
            ws.cell(row=r, column=8, value="∎ 관련 해설(2024.7 예시).").alignment = wrap
            r += 1


def main() -> None:
    wb = Workbook()
    wb.remove(wb.active)
    for name, blocks in SHEETS.items():
        ws = wb.create_sheet(title=name)
        _build_sheet(ws, blocks)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT))
    total = sum(len(c[4]) for bs in SHEETS.values() for c in bs)
    print(f"샘플 템플릿 생성: {OUT}  (시트 {len(SHEETS)}개, 점검항목 {total}개)")


if __name__ == "__main__":
    main()

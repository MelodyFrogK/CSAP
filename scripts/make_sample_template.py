"""데모용 CSAP 명세서 샘플 템플릿(.xlsx)을 생성한다.

실제 KISA 양식을 보유 시 data/sample_csap_template.xlsx 를 교체하거나,
웹 UI에서 직접 업로드하면 된다. 열 헤더 문구만 유사하면 자동 인식된다.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample_csap_template.xlsx"

# (항목번호, 분야, 항목명, 점검내용/요구사항) — 대표적인 통제 분야를 본뜬 예시
SAMPLE_ITEMS = [
    ("1.1.1", "정보보호 정책", "정책 수립·승인",
     "정보보호 정책을 수립하고 경영진의 승인을 받아 문서화하고 있는가?"),
    ("1.2.1", "정보보호 조직", "조직 및 책임",
     "정보보호 책임자(CISO)를 지정하고 역할과 책임을 문서로 정의하고 있는가?"),
    ("2.1.1", "인적 보안", "보안 서약/교육",
     "임직원 대상 보안 서약 및 정기 정보보호 교육을 시행하고 기록을 유지하는가?"),
    ("3.1.1", "자산 관리", "자산 식별·분류",
     "정보자산을 식별하여 목록을 관리하고 중요도에 따라 분류하고 있는가?"),
    ("4.1.1", "접근 통제", "계정 관리",
     "사용자 계정의 생성·변경·삭제 절차를 수립하고 최소권한 원칙을 적용하는가?"),
    ("4.2.1", "접근 통제", "인증 강화",
     "관리자 및 원격 접근에 다중인증(MFA)을 적용하고 있는가?"),
    ("5.1.1", "암호화", "전송/저장 암호화",
     "중요정보의 전송 구간 및 저장 시 암호화를 적용하고 키를 안전하게 관리하는가?"),
    ("6.1.1", "운영 보안", "로그 관리",
     "주요 시스템의 접근/변경 로그를 수집·보관하고 정기적으로 검토하는가?"),
    ("7.1.1", "침해사고 대응", "대응 절차",
     "침해사고 대응 절차와 비상연락체계를 수립하고 모의훈련을 실시하는가?"),
    ("8.1.1", "물리 보안", "출입 통제",
     "전산실 등 주요 구역의 출입 통제 및 출입기록 관리를 수행하는가?"),
    ("9.1.1", "재해복구", "백업/복구",
     "정기 백업을 수행하고 복구 절차를 문서화하여 복구 테스트를 실시하는가?"),
    ("10.1.1", "변경 관리", "변경 절차",
     "시스템 변경에 대한 요청·승인·기록 절차를 수립하여 운영하는가?"),
]

HEADERS = ["항목번호", "통제분야", "통제항목", "점검내용"]


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "CSAP명세서"

    title_fill = PatternFill("solid", fgColor="305496")
    bold_white = Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")

    for c, h in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = bold_white
        cell.fill = title_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    widths = [12, 16, 20, 60]
    for c, w in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = w

    for r, item in enumerate(SAMPLE_ITEMS, start=2):
        for c, val in enumerate(item, start=1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.alignment = wrap

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT))
    print(f"샘플 템플릿 생성: {OUT}  (항목 {len(SAMPLE_ITEMS)}개)")


if __name__ == "__main__":
    main()

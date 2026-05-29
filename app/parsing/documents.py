"""기업 제출 문서(PDF/Word)에서 텍스트를 추출한다."""
from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}


class UnsupportedDocument(ValueError):
    pass


def extract_text(path: str | Path) -> str:
    """파일 확장자에 맞춰 텍스트를 추출한다."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in {".docx", ".doc"}:
        return _extract_docx(path)
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise UnsupportedDocument(
        f"지원하지 않는 형식입니다: {ext} (지원: {', '.join(sorted(SUPPORTED_EXTENSIONS))})"
    )


def _extract_pdf(path: Path) -> str:
    # pdfplumber 우선(표/레이아웃 보존이 나음), 실패 시 pypdf로 폴백.
    try:
        import pdfplumber

        pages: list[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        text = "\n".join(pages).strip()
        if text:
            return text
    except Exception:  # noqa: BLE001 - 폴백 시도
        pass

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((p.extract_text() or "") for p in reader.pages).strip()


def _extract_docx(path: Path) -> str:
    from docx import Document

    doc = Document(str(path))
    parts: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
    # 표 내용도 포함
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts).strip()

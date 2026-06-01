"""기업 제출 문서(PDF/Word/zip)에서 텍스트를 추출한다."""
from __future__ import annotations

import zipfile
from pathlib import Path

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md"}
ARCHIVE_EXTENSIONS = {".zip"}


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


def extract_zip(zip_path: str | Path, dest_dir: str | Path) -> list[Path]:
    """zip 압축을 풀고 지원하는 문서 파일 목록을 반환한다.

    내부 디렉터리 구조는 유지하면서 dest_dir 하위에 압축 해제한다.
    지원 확장자(.pdf/.docx/.doc/.txt/.md)가 아닌 파일은 무시한다.
    """
    zip_path = Path(zip_path)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            # 디렉터리 엔트리 건너뜀
            if member.filename.endswith("/"):
                continue
            # 경로 순회 공격 방지
            member_path = Path(member.filename)
            safe_name = Path(*member_path.parts) if member_path.parts else member_path
            target = dest_dir / safe_name
            if not str(target.resolve()).startswith(str(dest_dir.resolve())):
                continue

            ext = Path(member.filename).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            # __MACOSX 등 macOS 메타데이터 폴더 건너뜀
            if any(part.startswith("__") for part in member_path.parts):
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as dst:
                dst.write(src.read())
            extracted.append(target)

    return extracted


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

"""FastAPI 웹 서비스.

업로드(명세서 템플릿 + 기업 문서) → 백그라운드 처리 → 결과 엑셀 다운로드.
작업 상태는 메모리에 보관(단일 프로세스 데모 기준). 운영 시 외부 스토어로 교체.
"""
from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .config import OUTPUT_DIR, UPLOAD_DIR, get_settings
from .core import pipeline
from .llm import get_provider
from .parsing.documents import ARCHIVE_EXTENSIONS, SUPPORTED_EXTENSIONS, extract_zip

app = FastAPI(title="CSAP 명세서 자동 작성", version="0.1.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "web" / "templates"))


@dataclass
class Job:
    id: str
    status: str = "pending"  # pending | running | done | error
    total: int = 0
    done: int = 0
    current: str = ""
    message: str = ""
    output: str = ""
    errors: list[str] = field(default_factory=list)


JOBS: dict[str, Job] = {}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    s = get_settings()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "provider": s.llm_provider,
            "extensions": ", ".join(sorted(SUPPORTED_EXTENSIONS)),
        },
    )


@app.get("/api/health")
def health():
    s = get_settings()
    return {"status": "ok", "provider": s.llm_provider}


@app.post("/api/jobs")
async def create_job(
    background: BackgroundTasks,
    documents: list[UploadFile] = File(...),
    template: UploadFile | None = File(None),
):
    if not documents:
        raise HTTPException(400, "기업 문서를 1개 이상 업로드하세요.")

    job = Job(id=uuid.uuid4().hex[:12])
    JOBS[job.id] = job
    job_dir = UPLOAD_DIR / job.id
    job_dir.mkdir(parents=True, exist_ok=True)

    # 템플릿 저장(없으면 기본 샘플 사용)
    s = get_settings()
    if template is not None and template.filename:
        template_path = job_dir / f"template_{template.filename}"
        _save(template, template_path)
    else:
        template_path = Path(s.default_template)
        if not template_path.exists():
            raise HTTPException(
                400,
                "기본 템플릿이 없습니다. 명세서 엑셀을 업로드하거나 "
                "`python scripts/make_sample_template.py` 를 먼저 실행하세요.",
            )

    doc_paths: list[Path] = []
    for up in documents:
        if not up.filename:
            continue
        ext = Path(up.filename).suffix.lower()
        if ext in ARCHIVE_EXTENSIONS:
            # zip 압축 파일: 내부 지원 문서 추출
            dest = job_dir / up.filename
            _save(up, dest)
            extracted = extract_zip(dest, job_dir / (dest.stem + "_unzipped"))
            if not extracted:
                raise HTTPException(400, f"{up.filename} 안에 지원하는 문서(.pdf/.docx/.txt 등)가 없습니다.")
            doc_paths.extend(extracted)
        elif ext in SUPPORTED_EXTENSIONS:
            dest = job_dir / up.filename
            _save(up, dest)
            doc_paths.append(dest)
        else:
            raise HTTPException(400, f"지원하지 않는 형식: {up.filename}")

    if not doc_paths:
        raise HTTPException(400, "유효한 기업 문서가 없습니다.")

    output_path = OUTPUT_DIR / f"{job.id}_result.xlsx"
    background.add_task(_run_job, job, str(template_path), doc_paths, str(output_path))
    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "작업을 찾을 수 없습니다.")
    return JSONResponse(
        {
            "id": job.id,
            "status": job.status,
            "total": job.total,
            "done": job.done,
            "current": job.current,
            "message": job.message,
            "errors": job.errors[:20],
            "download": f"/api/jobs/{job.id}/download" if job.status == "done" else None,
        }
    )


@app.get("/api/jobs/{job_id}/download")
def download(job_id: str):
    job = JOBS.get(job_id)
    if not job or job.status != "done" or not job.output:
        raise HTTPException(404, "결과 파일이 아직 없습니다.")
    return FileResponse(
        job.output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="CSAP_명세서_작성결과.xlsx",
    )


def _run_job(job: Job, template_path: str, doc_paths: list[Path], output_path: str) -> None:
    job.status = "running"
    try:
        # 공급자 사전 점검(키 누락 등 조기 실패)
        get_provider()

        def progress(done: int, total: int, current: str) -> None:
            job.done, job.total, job.current = done, total, current

        result = pipeline.run(
            template_path, [str(p) for p in doc_paths], output_path, progress=progress
        )
        job.output = str(result.output_path)
        job.errors = result.errors
        job.status = "done"
        job.message = f"항목 {result.item_count}개 중 {result.processed}개 작성 완료."
    except Exception as exc:  # noqa: BLE001 - 작업 상태로 표면화
        job.status = "error"
        job.message = str(exc)


def _save(upload: UploadFile, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    upload.file.close()

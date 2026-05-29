"""전체 처리 파이프라인: 문서 추출 → 청크 → 항목별 LLM 작성 → 엑셀 출력."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from ..config import get_settings
from ..llm import get_provider
from ..llm.base import LLMError
from ..models import ControlItem, ItemResult
from ..parsing import documents, excel_writer, template
from . import prompts
from .retrieval import Chunk, split_into_chunks, top_chunks

log = logging.getLogger("csap.pipeline")

ProgressCb = Callable[[int, int, str], None]


@dataclass
class PipelineResult:
    output_path: Path
    item_count: int
    processed: int
    errors: list[str] = field(default_factory=list)


def build_chunks(doc_paths: Iterable[str | Path]) -> list[Chunk]:
    s = get_settings()
    chunks: list[Chunk] = []
    for p in doc_paths:
        p = Path(p)
        text = documents.extract_text(p)
        chunks.extend(split_into_chunks(text, p.name, s.chunk_size, s.chunk_overlap))
    return chunks


def _process_item(item: ControlItem, chunks: list[Chunk]) -> ItemResult:
    s = get_settings()
    provider = get_provider()
    relevant = top_chunks(item.context_text(), chunks, s.top_k)
    user = prompts.build_user_prompt(item, relevant)
    data = provider.complete_json(prompts.SYSTEM_PROMPT, user)
    return ItemResult(
        row=item.row,
        status=str(data.get("status", "")).strip(),
        gaps=str(data.get("gaps", "")).strip(),
        compliance=str(data.get("compliance", "")).strip(),
        evidence=str(data.get("evidence", "")).strip(),
    )


def run(
    template_path: str | Path,
    doc_paths: list[str | Path],
    output_path: str | Path,
    progress: ProgressCb | None = None,
) -> PipelineResult:
    s = get_settings()
    items, layout = template.read_items(template_path)
    chunks = build_chunks(doc_paths)
    log.info("항목 %d개, 청크 %d개", len(items), len(chunks))

    results: dict[int, ItemResult] = {}
    errors: list[str] = []
    done = 0

    def work(item: ControlItem) -> tuple[ControlItem, ItemResult | None, str | None]:
        try:
            return item, _process_item(item, chunks), None
        except LLMError as exc:
            return item, None, f"행 {item.row}({item.code}): {exc}"

    with ThreadPoolExecutor(max_workers=max(1, s.concurrency)) as pool:
        for item, res, err in pool.map(work, items):
            done += 1
            if res is not None:
                results[item.row] = res
            if err:
                errors.append(err)
                log.warning(err)
            if progress:
                progress(done, len(items), item.code or item.title)

    out = excel_writer.write_results(template_path, layout, results, output_path)
    return PipelineResult(
        output_path=out,
        item_count=len(items),
        processed=len(results),
        errors=errors,
    )

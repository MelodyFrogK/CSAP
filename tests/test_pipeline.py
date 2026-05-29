"""핵심 파이프라인 스모크 테스트 (echo 공급자, 키 불필요)."""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("CSAP_LLM_PROVIDER", "echo")

from app.core import pipeline  # noqa: E402
from app.core.retrieval import split_into_chunks, top_chunks  # noqa: E402
from app.llm.base import LLMProvider  # noqa: E402
from app.parsing import documents, template  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_TEMPLATE = ROOT / "data" / "sample_csap_template.xlsx"


def _ensure_template() -> Path:
    if not SAMPLE_TEMPLATE.exists():
        from scripts.make_sample_template import main as make

        make()
    return SAMPLE_TEMPLATE


def test_extract_json_variants():
    p = LLMProvider
    assert p._extract_json('{"a": 1}') == {"a": 1}
    assert p._extract_json('```json\n{"a": 2}\n```') == {"a": 2}
    assert p._extract_json('설명입니다.\n{"a": 3}\n끝.') == {"a": 3}


def test_chunking_and_retrieval():
    text = "접근 통제 정책. 사용자 계정은 최소권한으로 관리한다. " * 50
    chunks = split_into_chunks(text, "doc.txt", size=200, overlap=40)
    assert chunks
    hits = top_chunks("계정 관리 최소권한 접근 통제", chunks, k=3)
    assert hits


def test_template_detection():
    tpl = _ensure_template()
    items, layout = template.read_items(tpl)
    assert len(items) >= 10
    assert layout.col_code and layout.col_requirement
    assert items[0].code


def test_txt_extraction(tmp_path):
    f = tmp_path / "policy.txt"
    f.write_text("정보보호 정책을 수립하고 경영진 승인을 받았다.", encoding="utf-8")
    assert "정보보호" in documents.extract_text(f)


def test_full_pipeline_echo(tmp_path):
    tpl = _ensure_template()
    doc = tmp_path / "policy.txt"
    doc.write_text(
        "당사는 정보보호 정책을 수립하고 CISO를 지정하였다. "
        "다중인증(MFA)을 관리자 접근에 적용한다. 로그는 1년간 보관한다.",
        encoding="utf-8",
    )
    out = tmp_path / "result.xlsx"
    res = pipeline.run(str(tpl), [str(doc)], str(out))
    assert out.exists()
    assert res.item_count >= 10
    assert res.processed == res.item_count
    assert not res.errors

    # 결과 열이 실제로 채워졌는지 확인
    from openpyxl import load_workbook

    wb = load_workbook(str(out))
    ws = wb.active
    _, layout = template.read_items(tpl)
    # write_results가 결과 열을 추가했으므로 다시 감지
    items2, layout2 = template.read_items(out)
    assert layout2.col_status is not None

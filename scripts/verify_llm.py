"""실 LLM 출력 품질 검증 도구.

명세서 일부(대표 점검항목)에 대해 실제 LLM을 호출하고, 사람이 검토/공유하기 쉬운
마크다운 리포트(verify_report.md)와 원시 JSON(verify_report.json)을 생성한다.
전체 명세서를 다 돌리지 않고 표본만 호출하므로 비용/시간이 적게 든다.

사용법:
  export ANTHROPIC_API_KEY=sk-ant-...
  export CSAP_LLM_PROVIDER=anthropic        # 또는 openai
  python scripts/verify_llm.py --template "명세서.xlsx" --limit 10 회사문서.pdf [문서2 ...]

표본은 시트 전반에 고르게 + '근거 있음/없음'이 섞이도록 자동 선별한다.
생성된 verify_report.md 를 그대로 공유하면 프롬프트를 추가로 다듬을 수 있다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 저장소 루트를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.core import prompts  # noqa: E402
from app.core.retrieval import split_into_chunks, top_chunks  # noqa: E402
from app.llm import get_provider  # noqa: E402
from app.llm.base import LLMError  # noqa: E402
from app.parsing import documents, template  # noqa: E402


def select_sample(items, limit):
    """시트 전반에 고르게 표본을 뽑는다(시트별 라운드로빈)."""
    by_sheet: dict[str, list] = {}
    for it in items:
        by_sheet.setdefault(it.sheet, []).append(it)
    sample, i = [], 0
    while len(sample) < limit and any(i < len(v) for v in by_sheet.values()):
        for v in by_sheet.values():
            if i < len(v) and len(sample) < limit:
                sample.append(v[i])
        i += 1
    return sample


def main(argv=None) -> int:
    s = get_settings()
    ap = argparse.ArgumentParser(description="실 LLM 출력 품질 검증")
    ap.add_argument("documents", nargs="+", help="기업 제출 문서(PDF/Word/txt)")
    ap.add_argument("--template", default=s.default_template, help="명세서 엑셀")
    ap.add_argument("--limit", type=int, default=10, help="호출할 표본 점검항목 수")
    ap.add_argument("--out", default="verify_report.md", help="리포트 파일")
    args = ap.parse_args(argv)

    if not Path(args.template).exists():
        print(f"[오류] 템플릿 없음: {args.template}", file=sys.stderr)
        return 2

    try:
        provider = get_provider()
    except LLMError as exc:
        print(f"[오류] LLM 공급자 초기화 실패: {exc}", file=sys.stderr)
        print("      ANTHROPIC_API_KEY / OPENAI_API_KEY 와 CSAP_LLM_PROVIDER 를 확인하세요.", file=sys.stderr)
        return 2

    items, _ = template.read_template(args.template)
    chunks = []
    for d in args.documents:
        chunks.extend(split_into_chunks(documents.extract_text(d), Path(d).name, s.chunk_size, s.chunk_overlap))

    sample = select_sample(items, args.limit)
    print(f"공급자={provider.name} | 전체 {len(items)}개 중 표본 {len(sample)}개 호출")

    records = []
    md = [
        f"# LLM 출력 검증 리포트",
        "",
        f"- 공급자: **{provider.name}**",
        f"- 명세서: `{Path(args.template).name}`",
        f"- 입력 문서: {', '.join(Path(d).name for d in args.documents)}",
        f"- 전체 점검항목 {len(items)}개 중 표본 {len(sample)}개",
        "",
        "> 아래 내용을 그대로 공유하면 프롬프트를 추가로 다듬어 드립니다.",
        "",
    ]

    for n, it in enumerate(sample, 1):
        rel = top_chunks(it.context_text(), chunks, s.top_k)
        try:
            data = provider.complete_json(prompts.SYSTEM_PROMPT, prompts.build_user_prompt(it, rel))
            err = None
        except LLMError as exc:
            data, err = {}, str(exc)
        print(f"  [{n}/{len(sample)}] {it.sheet} {it.sub_control or it.check_item[:20]} -> "
              f"{data.get('operation', 'ERR') if not err else 'ERROR'}")

        records.append({"sheet": it.sheet, "row": it.row, "check_item": it.check_item,
                        "retrieved_docs": [c.doc for c in rel], "output": data, "error": err})

        md += [
            f"## {n}. [{it.sheet}] {it.sub_control or it.check_item[:30]}",
            f"- **점검항목**: {it.check_item}",
            f"- **검색된 발췌 출처**: {', '.join({c.doc for c in rel}) or '(없음)'}",
            "",
        ]
        if err:
            md += [f"> ⚠️ 호출 오류: {err}", ""]
            continue
        md += [
            f"| 항목 | 내용 |",
            f"|---|---|",
            f"| 운영여부 | {data.get('operation', '')} |",
            f"| 운영 현황 | {(data.get('status') or '(빈칸)').replace(chr(10), '<br>')} |",
            f"| 관련문서 | {data.get('related_docs') or '(빈칸)'} |",
            f"| 운영 증적 | {data.get('evidence') or '(빈칸)'} |",
            f"| 보완사항 | {(data.get('improvement') or '(빈칸)').replace(chr(10), '<br>')} |",
            "",
        ]

    Path(args.out).write_text("\n".join(md), encoding="utf-8")
    Path(args.out).with_suffix(".json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n리포트 저장: {args.out}  (+ {Path(args.out).with_suffix('.json').name})")
    print("→ 위 파일 내용을 공유해 주시면 프롬프트를 마지막으로 다듬겠습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

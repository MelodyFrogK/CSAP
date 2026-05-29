"""커맨드라인 실행기. 웹 없이 빠르게 검증/배치 처리할 때 사용.

예) python -m app.cli --template data/sample_csap_template.xlsx \
        --out out.xlsx docs/policy.pdf docs/manual.docx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import get_settings
from .core import pipeline


def main(argv: list[str] | None = None) -> int:
    s = get_settings()
    parser = argparse.ArgumentParser(description="CSAP 명세서 자동 작성 (CLI)")
    parser.add_argument("documents", nargs="+", help="기업 제출 문서(PDF/Word/txt)")
    parser.add_argument("--template", default=s.default_template, help="명세서 엑셀 템플릿")
    parser.add_argument("--out", default="csap_result.xlsx", help="출력 엑셀 경로")
    args = parser.parse_args(argv)

    if not Path(args.template).exists():
        print(f"[오류] 템플릿이 없습니다: {args.template}", file=sys.stderr)
        print("      python scripts/make_sample_template.py 로 샘플을 생성하세요.", file=sys.stderr)
        return 2

    print(f"공급자: {s.llm_provider} | 템플릿: {args.template}")

    def progress(done: int, total: int, current: str) -> None:
        print(f"\r  진행: {done}/{total}  {current[:40]:<40}", end="", flush=True)

    res = pipeline.run(args.template, args.documents, args.out, progress=progress)
    print()
    print(f"시트: {', '.join(res.sheets)}")
    print(f"완료: 점검항목 {res.item_count}개 중 {res.processed}개 작성 → {res.output_path}")
    if res.errors:
        print(f"경고 {len(res.errors)}건:")
        for e in res.errors[:10]:
            print("  -", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

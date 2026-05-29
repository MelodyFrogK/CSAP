"""제출 문서를 청크로 나누고, 항목별로 관련 청크를 고른다.

외부 임베딩 API 의존을 피하기 위해 한국어에 무난한 경량 어휘 점수
(문자 n-gram + 토큰 자카드 가중)를 사용한다. 추후 임베딩 기반으로 교체 가능.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    doc: str
    index: int
    text: str


_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
# 한국어 흔한 불용어/조사성 토큰(완벽하진 않지만 노이즈 감소용)
_STOP = {
    "그리고", "또는", "등", "및", "the", "and", "of", "to", "a", "in", "for",
    "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "로", "으로",
}


def split_into_chunks(text: str, doc_name: str, size: int, overlap: int) -> list[Chunk]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []
    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    idx = 0
    for start in range(0, len(text), step):
        piece = text[start : start + size].strip()
        if piece:
            chunks.append(Chunk(doc=doc_name, index=idx, text=piece))
            idx += 1
        if start + size >= len(text):
            break
    return chunks


def _tokens(text: str) -> set[str]:
    return {t for t in (m.group().lower() for m in _TOKEN_RE.finditer(text)) if t not in _STOP and len(t) > 1}


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    s = re.sub(r"\s+", "", text.lower())
    return {s[i : i + n] for i in range(len(s) - n + 1)} if len(s) >= n else {s}


def score(query: str, chunk_text: str) -> float:
    q_tok, c_tok = _tokens(query), _tokens(chunk_text)
    if not q_tok:
        return 0.0
    token_overlap = len(q_tok & c_tok) / len(q_tok)
    q_ng, c_ng = _char_ngrams(query), _char_ngrams(chunk_text)
    ngram = len(q_ng & c_ng) / len(q_ng) if q_ng else 0.0
    return 0.7 * token_overlap + 0.3 * ngram


def top_chunks(query: str, chunks: list[Chunk], k: int) -> list[Chunk]:
    scored = [(score(query, c.text), c) for c in chunks]
    scored = [sc for sc in scored if sc[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:k]]

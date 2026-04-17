from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import re


@dataclass(frozen=True)
class CsvHit:
    id: str
    title: str
    content: str
    source: str
    tags: list[str]
    score: float


def _tokenize(s: str) -> set[str]:
    s = s.lower()
    s = re.sub(r"[^a-zа-я0-9]+", " ", s, flags=re.IGNORECASE)
    return {t for t in s.split() if len(t) >= 3}


def search_csv(csv_path: Path, query: str, k: int = 4) -> list[CsvHit]:
    if not csv_path.exists():
        return []

    q = _tokenize(query)
    if not q:
        return []

    hits: list[CsvHit] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rid = (row.get("id") or "").strip()
            title = (row.get("title") or "").strip()
            content = (row.get("content") or "").strip()
            source = (row.get("source") or "knowledge_base.csv").strip()
            tags = [t for t in (x.strip() for x in (row.get("tags") or "").split(",")) if t]
            text = f"{title}\n{content}"
            toks = _tokenize(text)
            overlap = len(q & toks)
            if overlap <= 0:
                continue
            score = overlap / max(6, len(q))
            hits.append(CsvHit(id=rid, title=title or rid, content=text.strip(), source=source, tags=tags, score=score))

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:k]


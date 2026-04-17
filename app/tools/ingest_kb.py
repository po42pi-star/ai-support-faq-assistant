from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import os

from dotenv import load_dotenv

from app.config import load_settings
from app.llm import make_client
from app.rag import KBRecord, get_collection, upsert_kb


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "knowledge_base" / "knowledge_base.csv"


def load_csv(path: Path) -> list[KBRecord]:
    records: list[KBRecord] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rid = (row.get("id") or "").strip()
            title = (row.get("title") or "").strip()
            content = (row.get("content") or "").strip()
            source = (row.get("source") or "knowledge_base.csv").strip()
            tags = [t for t in (x.strip() for x in (row.get("tags") or "").split(",")) if t]
            if not rid or not content:
                continue
            records.append(KBRecord(id=rid, title=title or rid, content=content, source=source, tags=tags))
    return records


def main() -> None:
    load_dotenv()
    s = load_settings()

    if not CSV_PATH.exists():
        raise SystemExit(f"Missing CSV: {CSV_PATH}. Run: python -m app.tools.build_kb")

    client = make_client(api_key=s.openai_api_key, base_url=s.openai_base_url)
    try:
        collection = get_collection(s.chroma_path, s.chroma_collection)
    except Exception as e:
        raise SystemExit(
            "ChromaDB is not available in this environment. "
            "Install Microsoft C++ Build Tools (for chroma-hnswlib) or run the bot with RAG_MODE=csv."
        ) from e

    records = load_csv(CSV_PATH)
    if not records:
        raise SystemExit("No KB records found to ingest.")

    upsert_kb(
        collection=collection,
        openai_client=client,
        embedding_model=s.openai_embedding_model,
        records=records,
    )
    print(f"Ingested {len(records)} records into Chroma collection '{s.chroma_collection}'.")


if __name__ == "__main__":
    main()


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class KBRecord:
    id: str
    title: str
    content: str
    source: str
    tags: list[str]


def _embed(client: OpenAI, *, model: str, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def get_collection(chroma_path: Path, name: str):
    try:
        import chromadb  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "ChromaDB is not available. Install build tools for 'chroma-hnswlib' "
            "or set RAG_MODE=csv to use CSV fallback."
        ) from e
    chroma_path.mkdir(parents=True, exist_ok=True)
    c = chromadb.PersistentClient(path=str(chroma_path))
    return c.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})


def upsert_kb(
    *,
    collection,
    openai_client: OpenAI,
    embedding_model: str,
    records: list[KBRecord],
) -> None:
    ids = [r.id for r in records]
    docs = [f"{r.title}\n\n{r.content}".strip() for r in records]
    embeddings = _embed(openai_client, model=embedding_model, texts=docs)
    metadatas: list[dict[str, Any]] = [
        {"title": r.title, "source": r.source, "tags": ",".join(r.tags)} for r in records
    ]
    collection.upsert(ids=ids, documents=docs, embeddings=embeddings, metadatas=metadatas)


@dataclass(frozen=True)
class SearchHit:
    id: str
    title: str
    content: str
    source: str
    tags: list[str]
    distance: float | None


def search(
    *,
    collection,
    openai_client: OpenAI,
    embedding_model: str,
    query: str,
    k: int = 4,
) -> list[SearchHit]:
    q_emb = _embed(openai_client, model=embedding_model, texts=[query])[0]
    res = collection.query(query_embeddings=[q_emb], n_results=k, include=["documents", "metadatas", "distances"])
    hits: list[SearchHit] = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for i in range(len(ids)):
        meta = metas[i] or {}
        title = str(meta.get("title") or "")
        source = str(meta.get("source") or "")
        tags_s = str(meta.get("tags") or "")
        tags = [t for t in (x.strip() for x in tags_s.split(",")) if t]
        hits.append(
            SearchHit(
                id=str(ids[i]),
                title=title,
                content=str(docs[i]),
                source=source,
                tags=tags,
                distance=float(dists[i]) if dists and dists[i] is not None else None,
            )
        )
    return hits


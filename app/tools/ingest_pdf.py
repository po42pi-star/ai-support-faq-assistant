"""
Загрузка PDF базы знаний в ChromaDB.
Использование:
    python -m app.tools.ingest_pdf ./knowledge_base/manual.pdf
    python -m app.tools.ingest_pdf ./knowledge_base/ --all  # все PDF в папке
"""
from __future__ import annotations

from pathlib import Path
import sys
import os

# Добавляем vendor в path
ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from dotenv import load_dotenv

from app.config import load_settings
from app.llm import make_client
from app.rag import get_collection, KBRecord, upsert_kb
from app.tools.pdf_parser import load_and_chunk_pdf, check_dependencies, get_required_packages


def pdf_chunks_to_kb_records(
    chunks,
    source_name: str,
) -> list[KBRecord]:
    """Конвертирует чанки из PDF в формат KBRecord для ChromaDB."""
    records: list[KBRecord] = []
    for chunk in chunks:
        record_id = f"{source_name}_{chunk.chunk_index}"
        title = f"{source_name} (стр. ~{chunk.page + 1})"
        content = chunk.content
        tags = ["pdf", "chunked", f"page_{chunk.page + 1}"]
        records.append(KBRecord(
            id=record_id,
            title=title,
            content=content,
            source=source_name,
            tags=tags,
        ))
    return records


def ingest_pdf(pdf_path: Path, settings, client, collection) -> int:
    """Загружает один PDF файл в ChromaDB."""
    print(f"Processing: {pdf_path.name}")

    # Чанкирование
    chunks = load_and_chunk_pdf(pdf_path)
    print(f"  Created {len(chunks)} chunks")

    # Конвертация в KBRecord
    records = pdf_chunks_to_kb_records(chunks, pdf_path.name)

    # Индексация
    upsert_kb(
        collection=collection,
        openai_client=client,
        embedding_model=settings.openai_embedding_model,
        records=records,
    )
    print(f"  Indexed {len(records)} records")

    return len(records)


def main() -> None:
    load_dotenv()

    # Проверка зависимостей
    if not check_dependencies():
        print("ERROR: Required packages not installed")
        print(f"Install: pip install -r requirements-pdf.txt")
        print(f"Or: pip install {' '.join(get_required_packages())}")
        sys.exit(1)

    settings = load_settings()
    client = make_client(api_key=settings.openai_api_key, base_url=settings.openai_base_url)

    try:
        collection = get_collection(settings.chroma_path, settings.chroma_collection)
    except Exception as e:
        print(f"ERROR: Cannot connect to ChromaDB: {e}")
        sys.exit(1)

    # Разбор аргументов
    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python -m app.tools.ingest_pdf <path_to_pdf>")
        print("  python -m app.tools.ingest_pdf <folder> --all")
        sys.exit(1)

    total_indexed = 0

    if "--all" in args:
        # Обработать все PDF в папке
        folder = Path(args[0])
        if not folder.exists() or not folder.is_dir():
            print(f"ERROR: Not a directory: {folder}")
            sys.exit(1)

        pdf_files = list(folder.glob("*.pdf"))
        if not pdf_files:
            print(f"ERROR: No PDF files found in {folder}")
            sys.exit(1)

        print(f"Found {len(pdf_files)} PDF files\n")
        for pdf_file in pdf_files:
            count = ingest_pdf(pdf_file, settings, client, collection)
            total_indexed += count

    else:
        # Обработать один файл
        pdf_path = Path(args[0])
        if not pdf_path.exists():
            print(f"ERROR: File not found: {pdf_path}")
            sys.exit(1)

        total_indexed = ingest_pdf(pdf_path, settings, client, collection)

    print(f"\nTotal indexed: {total_indexed} chunks")


if __name__ == "__main__":
    main()

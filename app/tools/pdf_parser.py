"""
Парсер PDF и чанкирование для больших баз знаний.
Используется для загрузки больших PDF-документов в ChromaDB.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

# try/except для случая когда зависимости не установлены
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


@dataclass(frozen=True)
class ChunkedDocument:
    """Чанк документа с метаданными."""
    content: str
    page: int
    source: str
    chunk_index: int


def check_dependencies() -> bool:
    """Проверка наличия необходимых зависимостей."""
    if not LANGCHAIN_AVAILABLE:
        return False
    return True


def get_required_packages() -> list[str]:
    """Список пакетов для поддержки PDF."""
    return [
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "PyPDF2>=3.0.0",
        "tiktoken>=0.5.0",
    ]


def load_pdf(pdf_path: Path) -> list[str]:
    """
    Извлекает текст из PDF.
    Возвращает список страниц (текст каждой страницы).
    """
    if not LANGCHAIN_AVAILABLE:
        raise RuntimeError(
            "langchain not installed. Install: pip install -r requirements-pdf.txt"
        )

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    loader = PyPDFLoader(str(pdf_path))
    pages = loader.load()
    return [page.page_content for page in pages]


def chunk_text(
    pages: list[str],
    source_name: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[ChunkedDocument]:
    """
    Разбивает текст на чанки.
    
    Args:
        pages: Список страниц из PDF
        source_name: Имя файла-источника
        chunk_size: Максимальный размер чанка в символах
        chunk_overlap: Перекрытие между чанками
    
    Returns:
        Список чанков с метаданными
    """
    if not LANGCHAIN_AVAILABLE:
        raise RuntimeError("langchain not installed")

    # Объединяем все страницы
    full_text = "\n\n".join(pages)

    # Разбиваем на чанки
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    chunks = splitter.split_text(full_text)

    # Создаём объекты с метаданными
    result: list[ChunkedDocument] = []
    for i, chunk in enumerate(chunks):
        # Примерная оценка номера страницы
        estimated_page = min(i * chunk_size // 2000, len(pages) - 1)
        result.append(ChunkedDocument(
            content=chunk.strip(),
            page=estimated_page,
            source=source_name,
            chunk_index=i,
        ))

    return result


def load_and_chunk_pdf(
    pdf_path: Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[ChunkedDocument]:
    """
    Полный цикл: загрузка PDF + чанкирование.
    
    Args:
        pdf_path: Путь к PDF файлу
        chunk_size: Размер чанка
        chunk_overlap: Перекрытие
    
    Returns:
        Список чанков для индексации
    """
    pages = load_pdf(pdf_path)
    return chunk_text(
        pages=pages,
        source_name=pdf_path.name,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


# Пример использования
if __name__ == "__main__":
    import sys

    if not check_dependencies():
        print("ERROR: langchain not installed")
        print(f"Install: pip install {' '.join(get_required_packages())}")
        sys.exit(1)

    # Пример: python -m app.tools.pdf_parser ./knowledge_base/manual.pdf
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        chunks = load_and_chunk_pdf(pdf_path)
        print(f"Loaded {len(chunks)} chunks from {pdf_path.name}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i} (page ~{chunk.page}) ---")
            print(chunk.content[:200] + "...")

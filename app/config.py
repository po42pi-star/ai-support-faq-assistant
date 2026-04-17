from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str

    openai_api_key: str
    openai_base_url: str
    openai_model: str
    openai_embedding_model: str

    sqlite_path: Path
    rag_mode: str
    chroma_path: Path
    chroma_collection: str

    log_level: str
    tz: str


def _require(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        openai_api_key=_require("OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.proxyapi.ru/openai/v1"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        sqlite_path=Path(os.getenv("SQLITE_PATH", "./data/queries.sqlite")),
        rag_mode=os.getenv("RAG_MODE", "auto"),
        chroma_path=Path(os.getenv("CHROMA_PATH", "./data/chroma")),
        chroma_collection=os.getenv("CHROMA_COLLECTION", "support_kb"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        tz=os.getenv("TZ", "Europe/Moscow"),
    )

from __future__ import annotations

import logging
import csv
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))
from dotenv import load_dotenv

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import NetworkError, TimedOut
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.config import load_settings
from app.db import connect, init_db, insert_query, counts_by_field, fetch_recent_queries
from app.llm import PROMPT_VERSION, RAGSnippet, classify_query, draft_reply, make_client, summarize_analytics
from app.logging_setup import setup_logging
from app.prompts import load_system_prompt
from app.rag import get_collection, search as rag_search
from app.rag_csv import search_csv


logger = logging.getLogger("app.bot")


HELP_TEXT = (
    "Команды:\n"
    "/start — описание\n"
    "/help — помощь\n"
    "/ask вопрос — задать вопрос и получить ответ\n"
    "/info текст — сохранить вопрос без ответа\n"
    "/analytics — краткая сводка по обращениям\n"
    "/export_csv — выгрузка обращений в CSV\n\n"
    "Можно также просто отправить вопрос — бот ответит на основе базы знаний."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    m = update.effective_message
    if not m:
        return
    try:
        await m.reply_text(
            "🤖 ИИ-ассистент технической поддержки\n\n"
            "Приветствую! Я виртуальный помощник для ответов на ваши вопросы.\n\n"
            "📚 Что я умею:\n"
            "- Отвечать на вопросы из базы знаний\n"
            "- Помогать с проблемами доставки, оплаты, возвратов\n"
            "- Предлагать шаблоны решений\n"
            "- Передавать сложные случаи оператору\n\n"
            "⏱️ Среднее время ответа: меньше 30 секунд\n"
            "🕐 Работаю: 24/7 без выходных\n\n"
            + HELP_TEXT
            + "\n\nЧем могу помочь?",
            parse_mode=None
        )
    except (TimedOut, NetworkError) as e:
        logger.warning("Telegram send failed in /start: %s", e)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    m = update.effective_message
    if not m:
        return
    try:
        await m.reply_text(HELP_TEXT)
    except (TimedOut, NetworkError) as e:
        logger.warning("Telegram send failed in /help: %s", e)


def _get_text_arg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | None:
    if context.args:
        return " ".join(context.args).strip()
    m = update.effective_message
    if m and getattr(m, "text", None):
        t = m.text.strip()
        if t.startswith("/ask") or t.startswith("/info"):
            parts = t.split(maxsplit=1)
            if len(parts) == 2:
                return parts[1].strip()
            return None
        return t
    return None


def _update_meta(update: Update) -> dict:
    m = update.effective_message
    u = m.from_user if m else None
    return {
        "telegram_chat_id": int(m.chat_id) if m else None,
        "telegram_user_id": int(u.id) if u else None,
        "telegram_username": u.username if u else None,
        "message_id": int(m.message_id) if m else None,
    }


async def cmd_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = _get_text_arg(update, context)
    if not text:
        m = update.effective_message
        if m:
            await m.reply_text("Пришлите текст: /info вопрос")
        return

    st = context.application.bot_data["state"]
    conn = st["db_conn"]
    meta = _update_meta(update)
    insert_query(conn, raw_text=text, llm_prompt_version=PROMPT_VERSION, **meta)
    m = update.effective_message
    if m:
        try:
            await m.reply_text("Сохранено в базу.")
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram send failed in /info: %s", e)


async def cmd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = _get_text_arg(update, context)
    if not text:
        m = update.effective_message
        if m:
            await m.reply_text("Пришлите вопрос: /ask текст")
        return

    st = context.application.bot_data["state"]
    client = st["openai_client"]
    model = st["model"]
    embedding_model = st["embedding_model"]
    rag_mode = st["rag_mode"]
    collection = st.get("chroma_collection")
    kb_csv_path = st["kb_csv_path"]
    system_prompt = st["system_prompt"]
    conn = st["db_conn"]

    cls = classify_query(client, model=model, text=text)
    hits = []
    snippets: list[RAGSnippet] = []
    if rag_mode == "chroma" and collection is not None:
        hits = rag_search(
            collection=collection,
            openai_client=client,
            embedding_model=embedding_model,
            query=text,
            k=4,
        )
        snippets = [
            RAGSnippet(title=h.title or h.id, content=h.content, source=h.source or "kb", score=h.distance)
            for h in hits
        ]
    else:
        csv_hits = search_csv(kb_csv_path, text, k=4)
        snippets = [
            RAGSnippet(title=h.title or h.id, content=h.content, source=h.source or "kb_csv", score=h.score)
            for h in csv_hits
        ]
    reply = draft_reply(
        client,
        model=model,
        system_prompt=system_prompt,
        customer_text=text,
        classification=cls,
        rag_snippets=snippets,
    )

    meta = _update_meta(update)
    insert_query(
        conn,
        raw_text=text,
        category=cls.category,
        priority=cls.priority,
        intent=cls.intent,
        extracted_issues=cls.issues,
        suggested_reply=reply,
        rag_used=bool(snippets),
        rag_sources=(
            [{"id": h.id, "title": h.title, "source": h.source, "distance": h.distance} for h in hits]
            if hits
            else [{"title": s.title, "source": s.source, "score": s.score} for s in snippets]
        ),
        llm_model=model,
        llm_prompt_version=PROMPT_VERSION,
        **meta,
    )

    out = f"Ваш вопрос:\n{text}\n\nОтвет:\n{reply}"
    if snippets:
        out = f"{out}\n\n📚 Источники:\n" + "\n".join([f"- {s.title}" for s in snippets[:4]])

    m = update.effective_message
    if m:
        try:
            await m.reply_text(out)
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram send failed in /ask: %s", e)


async def cmd_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    st = context.application.bot_data["state"]
    conn = st["db_conn"]
    client = st["openai_client"]
    model = st["model"]

    recent = fetch_recent_queries(conn, limit=50)
    by_category = counts_by_field(conn, "category", limit=10)
    by_priority = counts_by_field(conn, "priority", limit=10)
    by_intent = counts_by_field(conn, "intent", limit=10)

    lines = []
    lines.append("Данные (последние 50 обращений):")
    lines.append("Категории: " + ", ".join([f"{k}={v}" for k, v in by_category]))
    lines.append("Приоритеты: " + ", ".join([f"{k}={v}" for k, v in by_priority]))
    lines.append("Интенты: " + ", ".join([f"{k}={v}" for k, v in by_intent]))
    lines.append("")
    lines.append("Примеры последних обращений:")
    for r in recent[:10]:
        t = r.raw_text.replace("\n", " ")
        if len(t) > 160:
            t = t[:157] + "..."
        cat = r.category or "unknown"
        intent = r.intent or "unknown"
        lines.append(f"- [{r.id}] ({cat}/{intent}) {t}")

    ctx = "\n".join(lines)
    summary = summarize_analytics(client, model=model, report_context=ctx)
    m = update.effective_message
    if m:
        try:
            await m.reply_text(summary)
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram send failed in /analytics: %s", e)


async def cmd_export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    st = context.application.bot_data["state"]
    conn = st["db_conn"]

    cur = conn.execute(
        """
        SELECT
          id,
          created_at,
          telegram_chat_id,
          telegram_user_id,
          telegram_username,
          message_id,
          category,
          priority,
          intent,
          raw_text,
          suggested_reply
        FROM queries
        ORDER BY id ASC
        """
    )
    rows = cur.fetchall()
    if not rows:
        m = update.effective_message
        if m:
            await m.reply_text("В базе пока нет обращений для экспорта.")
        return

    from pathlib import Path
    data_dir = Path("data")
    exports_dir = data_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = exports_dir / f"queries_export_{ts}.csv"

    fieldnames = [
        "id",
        "created_at",
        "telegram_chat_id",
        "telegram_user_id",
        "telegram_username",
        "message_id",
        "category",
        "priority",
        "intent",
        "raw_text",
        "suggested_reply",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "telegram_chat_id": r["telegram_chat_id"],
                    "telegram_user_id": r["telegram_user_id"],
                    "telegram_username": r["telegram_username"],
                    "message_id": r["message_id"],
                    "category": r["category"],
                    "priority": r["priority"],
                    "intent": r["intent"],
                    "raw_text": r["raw_text"],
                    "suggested_reply": r["suggested_reply"],
                }
            )

    m = update.effective_message
    if m:
        try:
            await m.reply_document(
                document=path.open("rb"),
                filename=path.name,
                caption="Экспорт обращений в CSV для отчётов.",
            )
        except (TimedOut, NetworkError) as e:
            logger.warning("Telegram send failed in /export_csv: %s", e)


async def on_any_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    m = update.effective_message
    if not m or not getattr(m, "text", None):
        return
    t = m.text.strip()

    if t.startswith("/start"):
        await cmd_start(update, context)
        return
    if t.startswith("/help"):
        await cmd_help(update, context)
        return
    if t.startswith("/analytics"):
        await cmd_analytics(update, context)
        return
    if t.startswith("/export_csv"):
        await cmd_export_csv(update, context)
        return
    if t.startswith("/info"):
        await cmd_save(update, context)
        return
    if t.startswith("/ask"):
        await cmd_reply(update, context)
        return

    await cmd_reply(update, context)


def main() -> None:
    load_dotenv()
    s = load_settings()
    setup_logging(s.log_level)

    openai_client = make_client(api_key=s.openai_api_key, base_url=s.openai_base_url)
    system_prompt = load_system_prompt()

    conn = connect(s.sqlite_path)
    init_db(conn)

    kb_csv_path = ROOT / "knowledge_base" / "knowledge_base.csv"

    rag_mode = s.rag_mode.lower()
    if rag_mode not in {"auto", "chroma", "csv"}:
        rag_mode = "auto"

    collection = None
    if rag_mode in {"auto", "chroma"}:
        try:
            collection = get_collection(s.chroma_path, s.chroma_collection)
            rag_mode = "chroma"
        except Exception:
            collection = None
            rag_mode = "csv"
    else:
        rag_mode = "csv"

    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = Application.builder().token(s.telegram_bot_token).request(request).build()
    app.bot_data["state"] = {
        "openai_client": openai_client,
        "model": s.openai_model,
        "embedding_model": s.openai_embedding_model,
        "system_prompt": system_prompt,
        "db_conn": conn,
        "rag_mode": rag_mode,
        "chroma_collection": collection,
        "kb_csv_path": kb_csv_path,
    }

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ask", cmd_reply))
    app.add_handler(CommandHandler("info", cmd_save))
    app.add_handler(CommandHandler("analytics", cmd_analytics))
    app.add_handler(CommandHandler("export_csv", cmd_export_csv))
    app.add_handler(MessageHandler(filters.TEXT, on_any_text))

    logger.info("Bot started. Polling updates...")
    app.run_polling(
        close_loop=False,
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()

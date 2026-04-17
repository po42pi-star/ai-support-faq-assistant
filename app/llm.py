from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field
import json


PROMPT_VERSION = "v2.0"


class QueryClassification(BaseModel):
    category: str = Field(description="delivery|payment|return|account|technical|promo|other")
    priority: str = Field(description="low|medium|high|critical")
    intent: str = Field(description="question|complaint|suggestion|problem")
    issues: list[str] = Field(default_factory=list, description="extracted issues / problems")


@dataclass(frozen=True)
class RAGSnippet:
    title: str
    content: str
    source: str
    score: float | None = None


def make_client(*, api_key: str, base_url: str) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url)


def classify_query(client: OpenAI, *, model: str, text: str) -> QueryClassification:
    """Классифицирует вопрос клиента для техподдержки."""
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты помощник для классификации вопросов техподдержки. "
                    "Верни строго JSON по схеме без лишнего текста."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Классифицируй вопрос клиента по категории, приоритету и интенту.\n\n"
                    f"Вопрос:\n{text}\n\n"
                    "Формат JSON:\n"
                    '{"category":"delivery|payment|return|account|technical|promo|other",'
                    '"priority":"low|medium|high|critical",'
                    '"intent":"question|complaint|suggestion|problem",'
                    '"issues":["..."]}'
                ),
            },
        ],
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    return QueryClassification.model_validate_json(content)


def draft_reply(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    customer_text: str,
    classification: QueryClassification,
    rag_snippets: list[RAGSnippet],
) -> str:
    snippets_text = ""
    if rag_snippets:
        parts: list[str] = []
        for i, s in enumerate(rag_snippets, start=1):
            parts.append(
                f"[{i}] {s.title} (source: {s.source})\n{s.content}".strip()
            )
        snippets_text = "\n\n".join(parts)

    resp = client.chat.completions.create(
        model=model,
        temperature=0.4,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Сформируй корректный ответ клиенту на русском, вежливо и по делу.\n"
                    "Учитывай классификацию и базу знаний. Не выдумывай факты.\n\n"
                    f"Вопрос клиента:\n{customer_text}\n\n"
                    f"Классификация (JSON):\n{json.dumps(classification.model_dump(), ensure_ascii=False)}\n\n"
                    + (f"Релевантные фрагменты базы знаний:\n{snippets_text}\n\n" if snippets_text else "")
                    + "Требования к ответу:\n"
                    "- 3–7 предложений\n"
                    "- без обещаний, которые нельзя выполнить\n"
                    "- если не хватает данных, задай 1 уточняющий вопрос\n"
                    "- укажи источник информации\n"
                ),
            },
        ],
    )
    return (resp.choices[0].message.content or "").strip()


def summarize_analytics(
    client: OpenAI,
    *,
    model: str,
    report_context: str,
) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты аналитик поддержки. Сформируй краткую сводку по данным. "
                    "Пиши структурировано, без воды."
                ),
            }, {"role": "user", "content": report_context},
        ],
    )
    return (resp.choices[0].message.content or "").strip()

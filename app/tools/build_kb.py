from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import os
import sys
import textwrap

# Пытаемся автоматически добавить локальную папку vendor в sys.path,
# чтобы работал сценарий с `pip install -r requirements.txt -t vendor`.
ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"
if VENDOR.exists() and str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


KB_DIR = ROOT / "knowledge_base"
CSV_PATH = KB_DIR / "knowledge_base.csv"
PDF_PATH = KB_DIR / "knowledge_base.pdf"


@dataclass(frozen=True)
class KBRow:
    id: str
    title: str
    content: str
    type: str
    tags: str
    source: str


def wrap_100(s: str) -> str:
    # Переносы каждые 100 символов (включая пробелы), чтобы одинаково читалось в CSV/PDF
    # и не превращалось в “простыню”.
    lines: list[str] = []
    for part in (s or "").splitlines() or [""]:
        if not part:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(part, width=100, break_long_words=True, break_on_hyphens=False))
    return "\n".join(lines).strip()


def build_rows() -> list[KBRow]:
    # MVP: базовые формулировки, готовые ответы, примеры сводок
    return [
        KBRow(
            id="faq_delivery_delay",
            title="Жалоба: задержка доставки",
            type="template_reply",
            tags="delivery,negative,complaint",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо, что сообщили. Понимаю, как неприятно ждать дольше обещанного. "
                "Подскажите, пожалуйста, номер заказа и дату оформления — проверим статус и вернёмся с решением. "
                "Если удобнее, укажите контакт для связи."
            ),
        ),
        KBRow(
            id="faq_damaged_item",
            title="Жалоба: товар повреждён/брак",
            type="template_reply",
            tags="quality,negative,complaint",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за отзыв и извините за неудобства. "
                "Подскажите, пожалуйста, номер заказа и приложите фото повреждения — так мы быстрее разберёмся. "
                "Мы проверим ситуацию и предложим варианты решения."
            ),
        ),
        KBRow(
            id="faq_double_charge",
            title="Критично: двойное списание",
            type="playbook",
            tags="payment,negative,urgent",
            source="mvp_seed",
            content=(
                "Если клиент сообщает о двойном списании: "
                "1) извиниться, 2) запросить номер заказа/время операции/последние 4 цифры карты (если допустимо), "
                "3) сообщить, что передаём в платежную команду, 4) указать, что проверка занимает время, без обещаний сроков."
            ),
        ),
        KBRow(
            id="faq_thanks_positive",
            title="Благодарность: позитивный отзыв",
            type="template_reply",
            tags="positive,thanks",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за тёплые слова! Очень рады, что вам понравилось. "
                "Если будет время — расскажите, что именно оказалось самым полезным, это помогает нам улучшаться."
            ),
        ),
        KBRow(
            id="idea_feature_request",
            title="Предложение: запрос новой функции",
            type="template_reply",
            tags="idea,feature_request,neutral",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за идею — звучит полезно. "
                "Уточните, пожалуйста, в каком сценарии вы чаще всего хотите использовать эту возможность, "
                "чтобы мы корректно передали запрос команде."
            ),
        ),
        KBRow(
            id="summary_example_topics",
            title="Пример сводки: топ тем и оценок",
            type="summary_example",
            tags="analytics,summary",
            source="mvp_seed",
            content=(
                "Сводка за неделю: 120 отзывов. Негатив 35%, нейтральные 40%, позитив 25%. "
                "Топ тем: доставка (42), качество (25), поддержка (18), оплата (12). "
                "Повторяющиеся проблемы: задержки доставки, повреждения при транспортировке, долгий ответ чата."
            ),
        ),
        KBRow(
            id="common_phrases_delivery",
            title="Частые формулировки: доставка",
            type="phrase_bank",
            tags="phrases,delivery",
            source="mvp_seed",
            content=(
                "“доставка опоздала”, “жду уже неделю”, “курьер не отвечает”, "
                "“не привезли в обещанный день”, “статус не обновляется”"
            ),
        ),
        KBRow(
            id="common_phrases_support",
            title="Частые формулировки: поддержка",
            type="phrase_bank",
            tags="phrases,support",
            source="mvp_seed",
            content=(
                "“никто не отвечает”, “оператор отвечает долго”, “в чате тишина”, "
                "“не могу дозвониться”, “обещали перезвонить”"
            ),
        ),
        KBRow(
            id="faq_promo_not_working",
            title="Жалоба: промокод не работает",
            type="template_reply",
            tags="promo,pricing,negative,complaint",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо, что сообщили. Давайте проверим промокод: подскажите, пожалуйста, сам код и что именно "
                "происходит (ошибка/не применяется скидка), а также условия заказа (сумма, товары). Мы уточним причину и "
                "вернёмся с решением."
            ),
        ),
        KBRow(
            id="faq_app_crash_payment",
            title="Жалоба: приложение вылетает при оплате",
            type="template_reply",
            tags="app,bug,payment,negative,urgent",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за сигнал и извините за неудобства. Уточните, пожалуйста, модель телефона, версию ОС и "
                "версию приложения, а также на каком шаге оплаты происходит сбой. Мы передадим информацию команде и "
                "поможем подобрать обходной вариант, если он доступен."
            ),
        ),
        KBRow(
            id="faq_return_policy",
            title="Вопрос/проблема: как оформить возврат",
            type="template_reply",
            tags="return,neutral,support",
            source="mvp_seed",
            content=(
                "Ответ: Подскажите, пожалуйста, номер заказа и причину возврата. Я подскажу следующий шаг и какие данные "
                "нужны для оформления. Если у вас есть фото/видео проблемы — это ускорит проверку."
            ),
        ),
        KBRow(
            id="faq_wrong_size_exchange",
            title="Жалоба: привезли не тот размер / нужна замена",
            type="template_reply",
            tags="exchange,delivery,negative,complaint",
            source="mvp_seed",
            content=(
                "Ответ: Извините за ситуацию. Подскажите, пожалуйста, номер заказа и какой размер пришёл / какой нужен. "
                "Мы проверим наличие и подскажем вариант обмена/коррекции заказа."
            ),
        ),
        KBRow(
            id="faq_too_many_notifications",
            title="Жалоба: слишком много уведомлений",
            type="template_reply",
            tags="notifications,ux,neutral,complaint",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за обратную связь. Уточните, пожалуйста, какие именно уведомления мешают и где вы их "
                "получаете (push/почта/смс). Мы подскажем настройки, а также передадим пожелание команде."
            ),
        ),
        KBRow(
            id="idea_change_address_after_order",
            title="Предложение: менять адрес доставки после оформления",
            type="template_reply",
            tags="idea,delivery,feature_request,neutral",
            source="mvp_seed",
            content=(
                "Ответ: Спасибо за идею. Уточните, пожалуйста, как часто вам нужно менять адрес и на каком этапе заказа "
                "это критично (сразу после оформления/в день доставки). Мы передадим кейс команде."
            ),
        ),
    ]


def write_csv(rows: list[KBRow]) -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["id", "title", "content", "type", "tags", "source"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    "id": r.id,
                    "title": r.title,
                    "content": wrap_100(r.content),
                    "type": r.type,
                    "tags": r.tags,
                    "source": r.source,
                }
            )


def write_pdf(rows: list[KBRow]) -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(PDF_PATH), pagesize=A4, title="Knowledge Base (MVP)")
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Knowledge Base (MVP)", styles["Title"]))
    story.append(Spacer(1, 12))
    for r in rows:
        story.append(Paragraph(r.title, styles["Heading2"]))
        story.append(Paragraph(f"<b>id:</b> {r.id}", styles["BodyText"]))
        story.append(Paragraph(f"<b>type:</b> {r.type} &nbsp;&nbsp; <b>tags:</b> {r.tags}", styles["BodyText"]))
        story.append(Paragraph(wrap_100(r.content).replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 10))
    doc.build(story)


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_pdf(rows)
    print(f"Wrote: {CSV_PATH}")
    print(f"Wrote: {PDF_PATH}")


if __name__ == "__main__":
    main()


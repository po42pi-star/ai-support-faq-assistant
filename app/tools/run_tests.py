"""
Автоматическое тестирование ИИ-ассистента.
Запускает 20 тестовых вопросов из test_dataset_20.md и сохраняет результаты.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

TEST_FILE = Path("docs/test_dataset_20.md")
OUTPUT_CSV = Path("test_results.csv")
OUTPUT_JSON = Path("test_results.json")


def load_test_queries() -> list[dict]:
    """Читает тестовые вопросы из test_dataset_20.md"""
    # Парсим простой формат Markdown
    queries = []
    current = {}
    
    with open(TEST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("**"):
                # Новый тест
                if current:
                    queries.append(current)
                current = {"number": line.replace("**", "").replace(".", "").strip()}
            elif line.startswith("Тип:"):
                current["type"] = line.replace("Тип:", "").strip()
            elif line.startswith("Тема:"):
                current["topic"] = line.replace("Тема:", "").strip()
            elif line.startswith("Текст:"):
                current["text"] = line.replace("Текст:", "").strip()
            elif line.startswith("Ожидаемый источник:"):
                current["expected_source"] = line.replace("Ожидаемый источник:", "").strip()
    
    if current:
        queries.append(current)
    
    return queries


def test_query(client: OpenAI, query: dict) -> dict:
    """Запускает один тестовый вопрос."""
    import time
    start = time.time()
    
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "Ты ИИ-ассистент техподдержки. Отвечай кратко и по делу."},
            {"role": "user", "content": query["text"]}
        ],
        temperature=0.4
    )
    
    duration = time.time() - start
    reply = response.choices[0].message.content
    
    return {
        "number": query.get("number", ""),
        "type": query.get("type", ""),
        "topic": query.get("topic", ""),
        "query": query["text"],
        "expected_source": query.get("expected_source", ""),
        "reply": reply,
        "duration_sec": round(duration, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


def main():
    print("Загрузка тестовых вопросов...")
    queries = load_test_queries()
    print(f"Найдено тестов: {len(queries)}")
    
    if not queries:
        print("Ошибка: не удалось прочитать тесты из test_dataset_20.md")
        print("Попробуйте проверить формат файла вручную.")
        return
    
    client = OpenAI(
        api_key=open(".env").read().split("OPENAI_API_KEY=")[1].split()[0] if Path(".env").exists() else "",
        base_url="https://api.proxyapi.ru/openai/v1"
    )
    
    results = []
    print("\nНачинаю тестирование...")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}/{len(queries)}: {query.get('text', '')[0:50]}...")
        result = test_query(client, query)
        results.append(result)
        
        # Показываем ответ
        print(f"   Ответ: {result['reply'][0:100]}...")
        print(f"   Время: {result['duration_sec']} сек")
    
    # Сохраняем результаты
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Тестирование завершено!")
    print(f"Результаты сохранены в:")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_JSON}")
    
    # Краткая статистика
    avg_time = sum(r["duration_sec"] for r in results) / len(results)
    print(f"\nСреднее время ответа: {avg_time:.2f} сек")
    print(f"Всего тестов: {len(results)}")


if __name__ == "__main__":
    main()

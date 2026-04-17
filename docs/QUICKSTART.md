# Быстрый старт: ИИ-ассистент техподдержки

## ⏱️ 5 минут до запуска

Это руководство поможет вам запустить ИИ-ассистента техподдержки за 5 минут.

---

## Шаг 1: Клонирование (30 сек)

```bash
git clone https://github.com/your-username/ai-support-faq-assistant.git
cd ai-support-faq-assistant
```

---

## Шаг 2: Установка зависимостей (2 мин)

```bash
# Создаём виртуальное окружение
python -m venv .venv

# Активируем
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Устанавливаем зависимости
pip install -r requirements.txt
```

---

## Шаг 3: Настройка (1 мин)

```bash
# Копируем шаблон .env
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Открываем для редактирования
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Вставьте ваш API-ключ:**
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

---

## Шаг 4: Подготовка базы знаний (1 мин)

```bash
# Генерируем базу знаний из шаблонов
python -m app.tools.build_kb

# Индексируем в ChromaDB (опционально)
python -m app.tools.ingest_kb
```

---

## Шаг 5: Запуск (30 сек)

### Вариант A: Telegram-бот

```bash
# Убедитесь, что TELEGRAM_BOT_TOKEN настроен в .env
python -m app.bot
```

### Вариант B: Консольный режим (для тестов)

```bash
python -m app.console
```

---

## ✅ Проверка работы

Отправьте боту сообщение:
```
Как оформить возврат?
```

**Ожидаемый ответ:**
```
Здравствуйте! Оформить возврат можно в течение 14 дней...

📚 Источник: FAQ «Как оформить возврат средств»
```

---

## 🚀 Следующие шаги

### 1. Настройте интеграцию

- **Веб-сайт:** Добавьте виджет (см. `docs/integration_guide.md`)
- **Telegram:** Настройте команды бота
- **API:** Получите API-ключ для интеграции

### 2. Обновите базу знаний

Откройте `knowledge_base/knowledge_base.csv` и добавьте ваши FAQ:

```csv
faq_101,Ваш вопрос,Ваш ответ...,faq,"ваши,теги",custom
```

Затем переиндексируйте:
```bash
python -m app.tools.ingest_kb
```

### 3. Настройте системный промпт

Отредактируйте `docs/system_prompt.md` под ваш бренд:
- Измените название компании
- Настройте тон общения
- Добавьте специфичные сценарии

---

## 🆘 Решение проблем

### Ошибка: "ChromaDB is not available"

**Решение:** Бот автоматически переключится на CSV-режим. Для использования ChromaDB:
```bash
pip install chromadb==0.6.3
```

### Ошибка: "Missing required env var: OPENAI_API_KEY"

**Решение:** Убедитесь, что `.env` файл существует и содержит ключ:
```bash
OPENAI_API_KEY=sk-...
```

### Ошибка: "ModuleNotFoundError"

**Решение:** Переустановите зависимости:
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 📞 Поддержка

- **Документация:** `docs/`
- **API Reference:** `docs/api_reference.md`
- **Integration Guide:** `docs/integration_guide.md`

---

**Время до запуска:** ~5 минут 🎉

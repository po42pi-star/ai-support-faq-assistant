# API Reference: ИИ-ассистент техподдержки

## 📖 О документе

Полная документация по REST API ИИ-ассистента техподдержки и FAQ.

**Базовый URL:** `https://api.company.com/v1`

---

## 🔐 Аутентификация

Все запросы к API требуют аутентификации через заголовок:

```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Получение API-ключа

1. Зарегистрируйтесь в личном кабинете
2. Перейдите в раздел "API Keys"
3. Нажмите "Создать ключ"
4. Скопируйте и сохраните ключ (показывается один раз)

---

## 📡 Эндпоинты

### POST /chat/message

Отправка сообщения и получение ответа от ИИ-ассистента.

**Параметры запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `session_id` | string | Да | Уникальный ID сессии |
| `message` | string | Да | Текст сообщения |
| `user_id` | string | Нет | ID пользователя для персонализации |
| `metadata` | object | Нет | Дополнительные данные (страница, user-agent) |

**Пример запроса:**
```json
{
  "session_id": "sess_abc123",
  "message": "Как оформить возврат?",
  "user_id": "user_456",
  "metadata": {
    "page_url": "https://site.com/returns",
    "user_agent": "Mozilla/5.0..."
  }
}
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "response_id": "resp_xyz789",
    "session_id": "sess_abc123",
    "message": "Здравствуйте! Оформить возврат можно в течение 14 дней...",
    "sources": [
      {
        "id": "faq_006",
        "title": "Как оформить возврат средств",
        "type": "faq",
        "relevance_score": 0.92,
        "url": "/kb/faq_006"
      }
    ],
    "suggested_actions": [
      {
        "label": "Оформить возврат",
        "action": "navigate",
        "url": "/returns/new"
      },
      {
        "label": "Политика возвратов",
        "action": "navigate",
        "url": "/policy/returns"
      }
    ],
    "escalation_available": true,
    "sentiment": "neutral",
    "topics": ["return", "policy"],
    "processing_time_ms": 234
  }
}
```

**Коды ошибок:**

| Код | Описание |
|-----|----------|
| 400 | Неверный формат запроса |
| 401 | Неверный API-ключ |
| 429 | Превышен лимит запросов |
| 500 | Внутренняя ошибка сервера |

---

### GET /chat/session/{session_id}/history

Получение истории диалога.

**Параметры пути:**
- `session_id` — ID сессии

**Параметры запроса:**

| Поле | Тип | Описание |
|------|-----|----------|
| `limit` | int | Максимум сообщений (по умолчанию 50) |
| `offset` | int | Смещение для пагинации |

**Пример запроса:**
```
GET /v1/chat/session/sess_abc123/history?limit=20&offset=0
Authorization: Bearer YOUR_API_KEY
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "user_id": "user_456",
    "created_at": "2026-04-17T10:00:00Z",
    "updated_at": "2026-04-17T10:30:00Z",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "Как оформить возврат?",
        "timestamp": "2026-04-17T10:00:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "Здравствуйте! Оформить возврат...",
        "sources": ["faq_006"],
        "timestamp": "2026-04-17T10:00:02Z"
      },
      {
        "id": "msg_003",
        "role": "user",
        "content": "А если прошло больше 14 дней?",
        "timestamp": "2026-04-17T10:05:00Z"
      },
      {
        "id": "msg_004",
        "role": "assistant",
        "content": "Если прошло больше 14 дней...",
        "sources": ["policy_001"],
        "timestamp": "2026-04-17T10:05:03Z"
      }
    ],
    "total_messages": 4
  }
}
```

---

### POST /chat/escalate

Передача диалога оператору (эскалация).

**Параметры запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `session_id` | string | Да | ID сессии |
| `reason` | string | Да | Причина эскалации |
| `priority` | string | Нет | Приоритет: low, medium, high, critical |
| `notes` | string | Нет | Дополнительные заметки |

**Пример запроса:**
```json
{
  "session_id": "sess_abc123",
  "reason": "Клиент требует оператора",
  "priority": "medium",
  "notes": "Проблема с возвратом, прошло 20 дней"
}
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "escalation_id": "esc_789",
    "session_id": "sess_abc123",
    "status": "pending",
    "priority": "medium",
    "assigned_to": null,
    "created_at": "2026-04-17T10:30:00Z",
    "estimated_response_time": "2026-04-17T14:30:00Z"
  }
}
```

---

### GET /analytics/summary

Получение сводной аналитики.

**Параметры запроса:**

| Поле | Тип | Описание |
|------|-----|----------|
| `from` | date | Дата начала периода (YYYY-MM-DD) |
| `to` | date | Дата конца периода (YYYY-MM-DD) |
| `group_by` | string | Группировка: day, week, month |

**Пример запроса:**
```
GET /v1/analytics/summary?from=2026-04-01&to=2026-04-17&group_by=day
Authorization: Bearer YOUR_API_KEY
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2026-04-01",
      "to": "2026-04-17"
    },
    "metrics": {
      "total_conversations": 1247,
      "resolved_by_ai": 986,
      "escalated": 261,
      "resolution_rate": 0.79,
      "avg_response_time_ms": 2300,
      "csat_score": 4.6
    },
    "by_day": [
      {
        "date": "2026-04-01",
        "conversations": 78,
        "escalations": 18,
        "csat": 4.5
      },
      ...
    ],
    "top_topics": [
      {"topic": "order_status", "count": 312},
      {"topic": "return", "count": 187},
      {"topic": "payment", "count": 156}
    ],
    "sentiment_distribution": {
      "positive": 349,
      "neutral": 648,
      "negative": 250
    }
  }
}
```

---

### POST /analytics/export

Экспорт данных аналитики.

**Параметры запроса:**

| Поле | Тип | Описание |
|------|-----|----------|
| `from` | date | Дата начала периода |
| `to` | date | Дата конца периода |
| `format` | string | Формат: csv, json, xlsx |
| `include_messages` | bool | Включать сообщения диалогов |

**Пример запроса:**
```json
{
  "from": "2026-04-01",
  "to": "2026-04-17",
  "format": "csv",
  "include_messages": true
}
```

**Ответ:** Файл для скачивания или URL для загрузки.

---

### GET /kb/articles

Получение списка статей базы знаний.

**Параметры запроса:**

| Поле | Тип | Описание |
|------|-----|----------|
| `type` | string | Фильтр по типу: faq, document, template |
| `tag` | string | Фильтр по тегу |
| `search` | string | Поиск по заголовку и содержанию |
| `limit` | int | Максимум результатов |
| `offset` | int | Смещение |

**Пример запроса:**
```
GET /v1/kb/articles?type=faq&tag=возврат&limit=10
Authorization: Bearer YOUR_API_KEY
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "articles": [
      {
        "id": "faq_006",
        "title": "Как оформить возврат средств",
        "type": "faq",
        "tags": ["возврат", "refund", "оплата"],
        "created_at": "2026-04-01T00:00:00Z",
        "updated_at": "2026-04-15T00:00:00Z"
      },
      ...
    ],
    "total": 15,
    "limit": 10,
    "offset": 0
  }
}
```

---

### GET /kb/articles/{id}

Получение конкретной статьи базы знаний.

**Пример запроса:**
```
GET /v1/kb/articles/faq_006
Authorization: Bearer YOUR_API_KEY
```

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "id": "faq_006",
    "title": "Как оформить возврат средств",
    "content": "Возврат возможен в течение 14 дней...",
    "type": "faq",
    "tags": ["возврат", "refund", "оплата"],
    "sources": [],
    "related_articles": ["faq_004", "policy_001"],
    "created_at": "2026-04-01T00:00:00Z",
    "updated_at": "2026-04-15T00:00:00Z"
  }
}
```

---

### POST /kb/articles

Создание новой статьи базы знаний.

**Параметры запроса:**

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | string | Да | Уникальный ID |
| `title` | string | Да | Заголовок |
| `content` | string | Да | Содержание |
| `type` | string | Да | Тип: faq, document, template, scenario |
| `tags` | array | Нет | Теги |

**Пример запроса:**
```json
{
  "id": "faq_021",
  "title": "Новый вопрос",
  "content": "Ответ на новый вопрос...",
  "type": "faq",
  "tags": ["тег1", "тег2"]
}
```

---

### PUT /kb/articles/{id}

Обновление существующей статьи.

**Пример запроса:**
```json
{
  "title": "Обновлённый заголовок",
  "content": "Обновлённое содержание...",
  "tags": ["тег1", "тег2", "тег3"]
}
```

---

### DELETE /kb/articles/{id}

Удаление статьи из базы знаний.

**Пример ответа:**
```json
{
  "success": true,
  "data": {
    "deleted_id": "faq_006",
    "deleted_at": "2026-04-17T12:00:00Z"
  }
}
```

---

## 🚨 Коды ошибок

### Стандартные HTTP коды

| Код | Описание |
|-----|----------|
| 200 | Успех |
| 201 | Создано |
| 400 | Неверный запрос |
| 401 | Неавторизовано |
| 403 | Доступ запрещён |
| 404 | Не найдено |
| 429 | Слишком много запросов |
| 500 | Внутренняя ошибка |

### Формат ошибок

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Поле 'message' является обязательным",
    "details": {
      "field": "message",
      "reason": "required"
    }
  }
}
```

---

## 📊 Лимиты

### Rate Limiting

| Тариф | Запросов/минуту | Запросов/день |
|-------|-----------------|---------------|
| Free | 60 | 1,000 |
| Basic | 100 | 10,000 |
| Pro | 300 | 100,000 |
| Enterprise | 1,000 | Безлимит |

**Заголовки ответа:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1647532800
```

---

## 🔗 Webhooks

### Настройка вебхуков

Вебхуки позволяют получать уведомления о событиях.

**События:**
- `conversation.started` — начался новый диалог
- `conversation.escalated` — эскалация на оператора
- `conversation.resolved` — диалог завершён
- `feedback.received` — получен отзыв

**Пример настройки:**
```json
{
  "url": "https://your-server.com/webhook",
  "events": ["conversation.escalated", "feedback.received"],
  "secret": "your_webhook_secret"
}
```

**Пример payload:**
```json
{
  "event": "conversation.escalated",
  "timestamp": "2026-04-17T10:30:00Z",
  "data": {
    "escalation_id": "esc_789",
    "session_id": "sess_abc123",
    "reason": "Клиент требует оператора",
    "priority": "high"
  }
}
```

---

## 🧪 Тестирование

### Песочница

Для тестирования используйте песочницу:

**Базовый URL:** `https://api-sandbox.company.com/v1`

**Тестовый API-ключ:** `sk_test_...`

### Примеры кода

**Python:**
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.company.com/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.post(
    f"{BASE_URL}/chat/message",
    headers=headers,
    json={
        "session_id": "test_session",
        "message": "Как оформить возврат?"
    }
)

print(response.json())
```

**JavaScript:**
```javascript
const API_KEY = "your_api_key";
const BASE_URL = "https://api.company.com/v1";

const response = await fetch(`${BASE_URL}/chat/message`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    session_id: "test_session",
    message: "Как оформить возврат?"
  })
});

const data = await response.json();
console.log(data);
```

---

## 📞 Поддержка

- **Email:** api@company.com
- **Документация:** https://api.company.com/docs
- **Статус API:** https://status.company.com

---

**Версия API:** 1.0  
**Дата обновления:** 2026-04-17

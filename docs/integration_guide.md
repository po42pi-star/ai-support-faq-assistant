# Руководство по интеграции ИИ-ассистента техподдержки

## 📖 О документе

Это руководство описывает способы интеграции ИИ-ассистента техподдержки и FAQ в различные платформы: сайты, мобильные приложения, корпоративные системы и мессенджеры.

---

## 🌐 Интеграция в сайт

### Вариант 1: Веб-виджет (чат-бот)

**Описание:** Готовый JavaScript-виджет для вставки на любой сайт.

**Код для вставки:**
```html
<!-- Виджет ИИ-поддержки -->
<script>
  (function(d, t) {
    var g = d.createElement(t), s = d.getElementsByTagName(t)[0];
    g.src = "https://widget.company.com/chat.js";
    g.setAttribute("data-token", "YOUR_WIDGET_TOKEN");
    g.setAttribute("data-position", "bottom-right");
    g.setAttribute("data-color", "#4A90D9");
    s.parentNode.insertBefore(g, s);
  }(document, "script"));
</script>
```

**Параметры настройки:**

| Параметр | Значения | Описание |
|----------|----------|----------|
| `data-token` | строка | Уникальный токен виджета |
| `data-position` | `bottom-right`, `bottom-left` | Позиция кнопки чата |
| `data-color` | hex-цвет | Цвет кнопки и элементов |
| `data-welcome` | строка | Приветственное сообщение |
| `data-language` | `ru`, `en` | Язык интерфейса |

**Пример кастомизации:**
```html
<script src="https://widget.company.com/chat.js"
  data-token="YOUR_TOKEN"
  data-position="bottom-right"
  data-color="#FF6B6B"
  data-welcome="Здравствуйте! Чем могу помочь?"
  data-language="ru">
</script>
```

**CSS-кастомизация (опционально):**
```css
:root {
  --chat-widget-primary: #4A90D9;
  --chat-widget-secondary: #F5F5F5;
  --chat-widget-text: #333333;
  --chat-widget-border-radius: 12px;
}
```

---

### Вариант 2: iframe-вставка

**Описание:** Встраивание полноценного интерфейса ассистента через iframe.

**Код:**
```html
<iframe 
  src="https://assistant.company.com/embed?token=YOUR_TOKEN"
  width="400"
  height="600"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
  title="ИИ-ассистент поддержки">
</iframe>
```

**Адаптивный вариант:**
```html
<div class="assistant-container">
  <iframe 
    src="https://assistant.company.com/embed?token=YOUR_TOKEN"
    style="width: 100%; height: 500px; border: none;">
  </iframe>
</div>

<style>
  .assistant-container {
    max-width: 500px;
    margin: 0 auto;
  }
  
  @media (max-width: 600px) {
    .assistant-container iframe {
      height: 400px;
    }
  }
</style>
```

---

### Вариант 3: REST API

**Описание:** Прямая интеграция через API для кастомных решений.

**Базовый URL:** `https://api.company.com/v1/assistant`

**Аутентификация:**
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Эндпоинты:**

#### POST /chat/message
Отправка сообщения и получение ответа.

**Запрос:**
```json
{
  "session_id": "unique-session-id",
  "message": "Как оформить возврат?",
  "user_id": "user-123",
  "metadata": {
    "page_url": "https://site.com/returns",
    "user_agent": "Mozilla/5.0..."
  }
}
```

**Ответ:**
```json
{
  "success": true,
  "data": {
    "response_id": "resp_abc123",
    "message": "Здравствуйте! Оформить возврат можно в течение 14 дней...",
    "sources": [
      {
        "id": "faq_006",
        "title": "Как оформить возврат средств",
        "relevance_score": 0.92
      }
    ],
    "suggested_actions": [
      {"label": "Оформить возврат", "url": "/returns/new"},
      {"label": "Политика возвратов", "url": "/policy/returns"}
    ],
    "escalation_available": true
  }
}
```

#### GET /chat/session/{session_id}/history
Получение истории диалога.

**Ответ:**
```json
{
  "success": true,
  "data": {
    "session_id": "unique-session-id",
    "messages": [
      {
        "role": "user",
        "content": "Как оформить возврат?",
        "timestamp": "2026-04-17T10:30:00Z"
      },
      {
        "role": "assistant",
        "content": "Здравствуйте! Оформить возврат...",
        "timestamp": "2026-04-17T10:30:02Z"
      }
    ]
  }
}
```

#### POST /chat/escalate
Передача диалога оператору.

**Запрос:**
```json
{
  "session_id": "unique-session-id",
  "reason": "Клиент требует оператора",
  "priority": "medium"
}
```

---

## 📱 Интеграция в мобильное приложение

### iOS (Swift)

**Установка через CocoaPods:**
```ruby
pod 'CompanyAssistant', '~> 1.0'
```

**Использование:**
```swift
import CompanyAssistant

// Инициализация
Assistant.shared.configure(apiKey: "YOUR_API_KEY")

// Показать чат
Assistant.shared.presentChat(from: self)

// Или кастомный интерфейс
let message = AssistantMessage(text: "Как оформить возврат?")
Assistant.shared.send(message) { response in
    print(response.text)
}
```

### Android (Kotlin)

**Установка через Gradle:**
```gradle
dependencies {
    implementation 'com.company:assistant-sdk:1.0.0'
}
```

**Использование:**
```kotlin
// Инициализация
Assistant.configure(apiKey = "YOUR_API_KEY")

// Показать чат
Assistant.showChat(this)

// Или кастомный интерфейс
val message = AssistantMessage(text = "Как оформить возврат?")
Assistant.send(message) { response ->
    println(response.text)
}
```

### React Native

**Установка:**
```bash
npm install @company/assistant-react-native
```

**Использование:**
```javascript
import { AssistantProvider, useAssistant } from '@company/assistant-react-native';

function App() {
  return (
    <AssistantProvider apiKey="YOUR_API_KEY">
      <YourComponent />
    </AssistantProvider>
  );
}

function YourComponent() {
  const { sendMessage, messages } = useAssistant();
  
  const handleSend = () => {
    sendMessage('Как оформить возврат?');
  };
  
  return (
    // Ваш UI
  );
}
```

---

## 💼 Интеграция в корпоративные системы

### CRM-системы

#### 1C-Битрикс

**Модуль интеграции:**
1. Скачайте модуль из Маркетплейса
2. Установите через админ-панель
3. Настройте API-ключ в настройках модуля

**Использование в чате Битрикс24:**
```php
// Обработчик входящих сообщений
CIMChat::RegisterCallback('assistant', function($message) {
    $response = Assistant::sendMessage($message);
    CIMChat::AddMessage($response);
});
```

#### Salesforce

**Пакет AppExchange:**
1. Установите пакет из AppExchange
2. Настройте подключение в Setup → External Services
3. Добавьте компонент на Lightning Page

**Apex пример:**
```apex
AssistantService assistant = new AssistantService('YOUR_API_KEY');
AssistantResponse response = assistant.sendMessage('Как оформить возврат?');
System.debug(response.getMessage());
```

#### amoCRM

**Настройка:**
1. Установите виджет из каталога интеграций
2. Подключите API-ключ
3. Настройте триггеры для автоматических ответов

**Вебхук для входящих:**
```json
{
  "url": "https://your-server.com/webhook/amocrm",
  "method": "POST",
  "events": ["message_received", "task_created"]
}
```

---

### Help Desk системы

#### Zendesk

**Приложение для Zendesk:**
1. Установите из Zendesk Marketplace
2. Настройте в Admin → Apps → Assistant
3. Включите автоответы для определённых тегов

**Триггеры:**
- При создании тикета с тегом `faq` → автоответ от ИИ
- При статусе `pending` более 24ч → эскалация
- При теге `resolved_by_ai` → закрытие через 2 часа

#### Jira Service Management

**Интеграция:**
1. Установите приложение из Atlassian Marketplace
2. Настройте в Project Settings → AI Assistant
3. Добавьте автоматизацию через Rules

**Automation rule:**
```
IF: Issue created
AND: Issue type = Question
THEN: Send to AI Assistant
AND: Add comment with response
```

---

## 💬 Интеграция в мессенджеры

### Telegram

**Готовый бот:** `@company_support_bot`

**Настройка для вашей компании:**
1. Создайте бота через @BotFather
2. Получите токен
3. Настройте вебхук:
```bash
curl -X POST "https://api.company.com/v1/telegram/webhook" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d "{\"bot_token\": \"YOUR_BOT_TOKEN\"}"
```

**Команды бота:**
- `/start` — приветствие
- `/help` — справка
- `/order <номер>` — статус заказа
- `/status` — статус обращений
- `/human` — запрос оператора

### WhatsApp Business API

**Настройка:**
1. Получите доступ к WhatsApp Business API
2. Настройте вебхук в Facebook Business Manager
3. Подключите к платформе ассистента

**Пример вебхука:**
```python
@app.route('/whatsapp/webhook', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    message = data['messages'][0]['text']['body']
    sender = data['messages'][0]['from']
    
    response = assistant.send(message)
    
    send_whatsapp_message(sender, response.text)
    return '', 200
```

### Viber Business Messages

**Настройка:**
1. Зарегистрируйте бизнес-аккаунт в Viber
2. Получите токен и URL вебхука
3. Настройте интеграцию

---

## 🔧 Настройка и кастомизация

### Конфигурация ассистента

**Файл конфигурации (JSON):**
```json
{
  "assistant": {
    "name": "Анна",
    "tone": "friendly",
    "language": "ru",
    "working_hours": {
      "enabled": true,
      "timezone": "Europe/Moscow",
      "schedule": {
        "monday": {"start": "09:00", "end": "18:00"},
        "tuesday": {"start": "09:00", "end": "18:00"},
        "wednesday": {"start": "09:00", "end": "18:00"},
        "thursday": {"start": "09:00", "end": "18:00"},
        "friday": {"start": "09:00", "end": "18:00"}
      },
      "after_hours_message": "Сейчас нерабочее время. Оставьте сообщение, и мы ответим утром."
    }
  },
  "escalation": {
    "enabled": true,
    "keywords": ["оператор", "менеджер", "позвоните", "жалоба"],
    "after_attempts": 2,
    "notify_email": "support@company.com"
  },
  "analytics": {
    "enabled": true,
    "track_satisfaction": true,
    "export_format": "json"
  }
}
```

### Кастомизация ответов

**Шаблоны приветствия:**
```json
{
  "greetings": [
    "Здравствуйте! Чем могу помочь?",
    "Добрый день! Задайте ваш вопрос.",
    "Приветствую! Я виртуальный помощник. Чем полезен?"
  ]
}
```

**Быстрые ответы (кнопки):**
```json
{
  "quick_replies": [
    {"label": "📦 Статус заказа", "payload": "order_status"},
    {"label": "↩️ Возврат", "payload": "return_policy"},
    {"label": "💳 Оплата", "payload": "payment_methods"},
    {"label": "📞 Связаться с поддержкой", "payload": "contact_support"}
  ]
}
```

---

## 📊 Аналитика и мониторинг

### Дашборд метрик

**Доступные метрики:**
- Количество диалогов
- Процент решённых вопросов (без эскалации)
- Среднее время ответа
- Удовлетворённость клиентов (CSAT)
- Топ вопросов
- Часы пиковой нагрузки

**API для получения метрик:**
```bash
GET /v1/analytics/summary?from=2026-04-01&to=2026-04-17
Authorization: Bearer YOUR_API_KEY
```

### Экспорт данных

**Форматы экспорта:**
- CSV
- JSON
- XLSX

**Автоматическая выгрузка:**
```json
{
  "export": {
    "enabled": true,
    "schedule": "0 0 * * 1",
    "format": "csv",
    "destination": "s3://bucket/exports/",
    "notify_email": "analytics@company.com"
  }
}
```

---

## 🔐 Безопасность

### Требования безопасности

1. **HTTPS** — все соединения только по HTTPS
2. **API Keys** — ротация ключей каждые 90 дней
3. **Rate Limiting** — 100 запросов/минуту на ключ
4. **Data Encryption** — шифрование данных в покое (AES-256)
5. **GDPR Compliance** — возможность экспорта и удаления данных пользователя

### Логирование

**Что логируется:**
- Входящие сообщения
- Исходящие ответы
- Источники из базы знаний
- Факты эскалации

**Что НЕ логируется:**
- Персональные данные (email, телефон)
- Платёжная информация
- Пароли и токены

---

## 📞 Поддержка интеграции

### Технические контакты

- **Email:** integration@company.com
- **Telegram:** @company_api_support
- **Документация:** https://api.company.com/docs

### SLA поддержки

| Приоритет | Время реакции | Время решения |
|-----------|---------------|---------------|
| Критичный | 1 час | 4 часа |
| Высокий | 4 часа | 24 часа |
| Средний | 24 часа | 72 часа |
| Низкий | 72 часа | 7 дней |

---

**Версия документа:** 1.0  
**Дата:** 2026-04-17

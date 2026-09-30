
# Документация по JSON-структуре событий

## Общая структура файла

```json
{
  "events": [...],
  "recurring": [...]
}
```

Ключи `events` и `recurring` — массивы. Отсутствие ключа трактуется как пустой массив.

---

## Обычное событие (`events`)

### Минимум
```json
{
  "id": "unique_id_1",
  "title": "Название события",
  "date": "2026-09-24",
  "start": "09:00"
}
```

### Полный набор полей
```json
{
  "id": "unique_id_1",
  "title": "Название события",
  "date": "2026-09-24",
  "start": "09:00",
  "duration": 60,
  "category": "event",
  "description": "Описание события",
  "status": "pending",
  "created_at": "2026-09-24T10:00:00",
  "updated_at": "2026-09-24T10:00:00",
  "completed_at": "2026-09-24T10:30:00"
}
```

| Поле | Тип | Обязательное | По умолчанию | Описание |
|------|-----|--------------|--------------|----------|
| id | string | да | — | Уникальный идентификатор |
| title | string | да | — | Название события |
| date | string | да | — | Дата в формате YYYY-MM-DD |
| start | string | да | — | Время начала HH:MM |
| duration | number | нет | 60 | Длительность в минутах |
| category | string | нет | `event` | Одно из: event, meeting, task, reminder, personal |
| description | string | нет | `""` | Описание |
| status | string | нет | `pending` | Одно из: pending, done, missed |
| created_at | string | нет | ISO now | Дата создания |
| updated_at | string | нет | — | Дата обновления |
| completed_at | string | нет | — | Дата завершения |

---

## Повторяющееся событие (`recurring`)

### Минимум
```json
{
  "id": "rec_1",
  "title": "Название",
  "start": "09:00",
  "start_date": "2026-09-24",
  "rule": { "freq": "daily" }
}
```

### Полный набор полей
```json
{
  "id": "rec_1",
  "title": "Еженедельный отчёт",
  "start": "09:00",
  "start_date": "2026-09-24",
  "duration": 60,
  "category": "task",
  "description": "Подготовка отчёта",
  "rule": {
    "freq": "weekly",
    "interval": 1,
    "until": "2026-12-31",
    "count": 10
  },
  "status": "pending",
  "done_dates": ["2026-09-24", "2026-10-01"],
  "skipped_dates": ["2026-10-08"],
  "created_at": "2026-09-24T10:00:00",
  "updated_at": "2026-09-24T10:00:00"
}
```

| Поле | Тип | Обязательное | По умолчанию | Описание |
|------|-----|--------------|--------------|----------|
| id | string | да | — | Уникальный идентификатор |
| title | string | да | — | Название |
| start | string | да | — | Время начала HH:MM |
| start_date | string | да | — | Первая дата повторения, YYYY-MM-DD |
| duration | number | нет | 60 | Длительность в минутах |
| category | string | нет | `event` | См. обычные события |
| description | string | нет | `""` | Описание |
| rule | object | да | — | Правило повторения |
| rule.freq | string | да | — | daily / weekly / monthly / yearly |
| rule.interval | number | нет | 1 | Интервал повторения (>= 1) |
| rule.until | string | нет | — | Дата окончания, YYYY-MM-DD |
| rule.count | number | нет | — | Количество повторений (зарезервировано) |
| status | string | нет | `pending` | pending / done / missed |
| done_dates | array | нет | `[]` | Даты выполнения |
| skipped_dates | array | нет | `[]` | Даты пропуска |
| created_at | string | нет | ISO now | Дата создания |
| updated_at | string | нет | — | Дата обновления |

**Важно:** повторяющиеся события без `start_date` пропускаются (в лог пишется предупреждение).

---

## Категории и статусы

- `category`: `event`, `meeting`, `task`, `reminder`, `personal` (по умолчанию — `event`).
- `status`: `pending`, `done`, `missed` (по умолчанию — `pending`).
- `rule.freq`: `daily`, `weekly`, `monthly`, `yearly`.

---

## Зарезервировано под экспорт в ICS

Экспорт в формат ICS запланирован. Соответствие полей схемы и VEVENT:

| Поле схемы | Свойство VEVENT | Примечание |
|------------|-----------------|------------|
| id | UID | Префикс `rec:` для повторяющихся отбрасывается |
| title | SUMMARY | |
| date + start | DTSTART | ISO 8601 |
| duration | DURATION | Минуты → PT{n}M |
| description | DESCRIPTION | |
| category | CATEGORIES | |
| status | STATUS | pending → TENTATIVE, done → CONFIRMED, missed → CANCELLED |
| rule | RRULE | FREQ, INTERVAL, UNTIL, COUNT |
| created_at | CREATED | |
| updated_at | LAST-MODIFIED, DTSTAMP | |
| completed_at | COMPLETED | |

Обязательные поля схемы (id, title, date, start) остаются без изменений — никаких новых обязательных полей для ICS не вводится.

---

## Пример полного файла

```json
{
  "events": [
    {
      "id": "event_1",
      "title": "Важная встреча",
      "date": "2026-09-25",
      "start": "14:00",
      "duration": 90,
      "category": "meeting",
      "description": "Обсуждение проекта",
      "status": "pending"
    }
  ],
  "recurring": [
    {
      "id": "rec_1",
      "title": "Еженедельный отчёт",
      "start": "09:00",
      "start_date": "2026-09-24",
      "duration": 60,
      "category": "task",
      "description": "Подготовка отчёта",
      "rule": { "freq": "weekly", "interval": 1 },
      "status": "pending",
      "done_dates": [],
      "skipped_dates": []
    }
  ]
}
```
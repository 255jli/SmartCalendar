# Документация по JSON-структуре событий

## Общая структура JSON-файла

```json
{
  "events": [...],
  "recurring": [...]
}
```

## Структура обычного события (events)

### Минимальное событие
```json
{
  "id": "unique_id_1",
  "title": "Название события",
  "date": "2026-09-24",
  "start": "09:00"
}
```

### Максимальное событие
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
  "completed_at": "2026-09-24T10:00:00"
}
```

### Поля события

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| id | string | Да | Уникальный идентификатор события |
| title | string | Да | Название события |
| date | string | Да | Дата события в формате YYYY-MM-DD |
| start | string | Да | Время начала в формате HH:MM |
| duration | number | Нет | Длительность события в минутах (по умолчанию 60) |
| category | string | Нет | Категория события (event, meeting, task, reminder, personal) |
| description | string | Нет | Описание события |
| status | string | Нет | Статус события (pending, done, missed) |
| created_at | string | Нет | Дата создания в формате ISO |
| updated_at | string | Нет | Дата обновления в формате ISO |
| completed_at | string | Нет | Дата завершения в формате ISO |

## Структура повторяющегося события (recurring)

### Минимальное повторяющееся событие
```json
{
  "id": "rec_unique_id_1",
  "title": "Название повторяющегося события",
  "start": "09:00",
  "rule": {
    "freq": "daily"
  }
}
```

### Максимальное повторяющееся событие
```json
{
  "id": "rec_unique_id_1",
  "title": "Название повторяющегося события",
  "start": "09:00",
  "duration": 60,
  "category": "event",
  "description": "Описание повторяющегося события",
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

### Поля повторяющегося события

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| id | string | Да | Уникальный идентификатор события |
| title | string | Да | Название события |
| start | string | Да | Время начала в формате HH:MM |
| duration | number | Нет | Длительность события в минутах (по умолчанию 60) |
| category | string | Нет | Категория события (event, meeting, task, reminder, personal) |
| description | string | Нет | Описание события |
| rule | object | Да | Правило повторения |
| rule.freq | string | Да | Частота повторения (daily, weekly, monthly, yearly) |
| rule.interval | number | Нет | Интервал повторения (по умолчанию 1) |
| rule.until | string | Нет | Дата окончания повторений в формате YYYY-MM-DD |
| rule.count | number | Нет | Количество повторений |
| status | string | Нет | Статус события (pending, done, missed) |
| done_dates | array | Нет | Массив дат, когда событие было выполнено |
| skipped_dates | array | Нет | Массив дат, когда событие было пропущено |
| created_at | string | Нет | Дата создания в формате ISO |
| updated_at | string | Нет | Дата обновления в формате ISO |

## Пример полного JSON-файла

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
      "description": "Обсуждение проекта с командой",
      "status": "pending"
    }
  ],
  "recurring": [
    {
      "id": "rec_1",
      "title": "Еженедельный отчет",
      "start": "09:00",
      "duration": 60,
      "category": "task",
      "description": "Подготовка еженедельного отчета",
      "rule": {
        "freq": "weekly",
        "interval": 1
      },
      "status": "pending",
      "done_dates": [],
      "skipped_dates": []
    }
  ]
}
```

## Требования к полям

- `id`: должен быть уникальным в пределах файла
- `date`: формат YYYY-MM-DD, дата должна быть валидной
- `start`: формат HH:MM, время должно быть валидным
- `duration`: положительное число, в минутах
- `category`: одно из значений: event, meeting, task, reminder, personal
- `status`: одно из значений: pending, done, missed
- `rule.freq`: одно из значений: daily, weekly, monthly, yearly
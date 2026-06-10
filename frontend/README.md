# Командус Frontend Dashboard — зона Ивана

Frontend для роли **Иван — JavaScript / Dashboard / UI**. Проект сделан по документу `Командус.docx`: Иван отвечает не за Telegram bot, ASR, LLM или backend, а за понятный dashboard, который усиливает live-demo.

## Полностью закрытые пункты Ивана

### Зона 1. Dashboard layout

- Создан frontend project.
- Настроен Vite + React + TypeScript.
- Настроен Tailwind CSS.
- Сделан общий layout: sidebar, topbar, content area.
- Сделана navigation.
- Сделан demo-friendly UI.
- Страницы: `Tasks`, `AI Suggestions`, `Meetings`, `Analytics`, `Profile`.

### Зона 2. Mini-kanban

- Колонки: `Backlog`, `Todo`, `In Progress`, `Review`, `Done`.
- Карточка задачи показывает:
  - title;
  - assignee;
  - deadline;
  - priority;
  - source;
  - confidence;
  - external link;
  - status;
  - created by AI;
  - source excerpt;
  - kanban provider.
- Из dashboard можно менять статус через `PATCH /tasks/{task_id}/status`.
- Из dashboard можно переносить дедлайн через `POST /tasks/{task_id}/reschedule`.

### Зона 3. AI Suggestions

- Показываются `TaskCandidates` со статусом `pending`.
- Реализованы действия:
  - confirm;
  - reject;
  - edit locally;
  - open source message.
- После confirm/reject React Query инвалидирует задачи и suggestions.

### Зона 4. Meeting Summary page

- Есть загрузка аудио встречи через `POST /meetings/upload`.
- Есть просмотр summary по id через `GET /meetings/{id}/summary`.
- Страница показывает:
  - short summary;
  - decisions;
  - action items;
  - risks;
  - open questions;
  - created tasks / created candidates;
  - transcript quality.
- Добавлен `Knowledge Base preview` как P1/P2 demo-block, потому что документ предлагает сохранять summary встречи как knowledge item.

### Зона 5. Analytics

- Выведены MVP-метрики:
  - AI created tasks;
  - confirmed automatically;
  - waiting confirmation;
  - rejected suggestions;
  - voice messages processed;
  - meetings summarized;
  - average confidence.
- Дополнительно поддержаны velocity/quality-поля:
  - done this week;
  - overdue percent;
  - team velocity;
  - AI quality.
- Добавлен leaderboard как P1/P2 demo-block для achievements/gamification.

### Зона 6. Demo polish

- Есть empty states.
- Есть loading skeletons / loaders.
- Карточки читаемые и минималистичные.
- Есть source badges.
- Есть confidence badges.
- Быстрый доступ к нужным страницам через sidebar.
- Есть backup mock data через `VITE_USE_MOCKS=true`.
- Добавлены roadmap cards для P2-возможностей: Knowledge Base, Government mode, Skill recommendations.

## Дополнительные пункты Ивана из backlog дополнительных возможностей

- `Team Analytics` — страница `/analytics`.
- `My Profile` — страница `/profile`.
- `Achievements` — блок в `/profile` и leaderboard в `/analytics`.
- `Knowledge Base preview` — блок в `/meetings`.
- `Roadmap cards` — блок в `/analytics`.
- P2-фичи используют mock data и не ломают core MVP.

## Запуск

```bash
npm install
cp .env.example .env
npm run dev
```

Открой:

```txt
http://localhost:5173
```

## Подключение к backend

В `.env` укажи URL backend:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

Если backend еще не готов, включи демо-режим:

```env
VITE_USE_MOCKS=true
```

## Используемые backend endpoints

```txt
GET    /tasks
PATCH  /tasks/{task_id}/status
POST   /tasks/{task_id}/reschedule

GET    /task-candidates
POST   /tasks/candidates/{candidate_id}/confirm
POST   /tasks/candidates/{candidate_id}/reject

POST   /meetings/upload
GET    /meetings/{id}/summary

GET    /analytics/team
GET    /analytics/leaderboard

GET    /profile/me
GET    /tasks/my
GET    /users/{id}/digest
GET    /notes/my
POST   /notes
PATCH  /notes/{id}
DELETE /notes/{id}
GET    /users/{id}/achievements
GET    /users/{id}/recommendations

GET    /knowledge
```

`/analytics/leaderboard` и `/knowledge` нужны для demo/P1-P2 блоков. При `VITE_USE_MOCKS=true` они работают без backend.

## Ожидаемые форматы ответов

Backend может возвращать либо массив, либо объект `{ "items": [...] }` для списков. Frontend поддерживает оба варианта.

Для `GET /analytics/team` поддерживается плоский формат:

```json
{
  "ai_created_tasks": 12,
  "auto_confirmed": 8,
  "waiting_confirmation": 3,
  "rejected_suggestions": 1,
  "voice_messages_processed": 4,
  "meetings_summarized": 1,
  "average_confidence": 0.87
}
```

Также поддерживаются вложенные поля:

```json
{
  "team_velocity": {
    "done_this_week": 18,
    "avg_lead_time_hours": 14.5,
    "overdue_percent": 12
  },
  "ai_quality": {
    "average_confidence": 0.87,
    "auto_created": 8,
    "rejected_suggestions": 1
  }
}
```

## Структура

```txt
kyss-front-ivan/
├── public/
│   └── logo.svg
├── src/
│   ├── app/
│   ├── pages/
│   ├── widgets/
│   │   ├── Layout/
│   │   ├── Kanban/
│   │   ├── Suggestions/
│   │   ├── Meetings/
│   │   ├── Analytics/
│   │   └── Profile/
│   ├── entities/
│   │   ├── task/
│   │   ├── candidate/
│   │   ├── meeting/
│   │   ├── analytics/
│   │   ├── user/
│   │   └── knowledge/
│   └── shared/
│       ├── api/
│       ├── config/
│       ├── lib/
│       └── ui/
├── .env.example
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Проверка

```bash
npm run build
```

Сборка должна проходить без TypeScript-ошибок.

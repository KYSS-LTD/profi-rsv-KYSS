# Командус — Telegram Mini App + PWA frontend

Готовый frontend-пакет для ветки `develop-danila`: Vite + React + TypeScript + Tailwind, адаптированный под Telegram Mini App и обычную PWA.

## Что внутри

- mobile-first dashboard для Telegram WebView;
- PWA manifest, installable icons и service worker;
- Telegram Web App SDK через официальный скрипт `https://telegram.org/js/telegram-web-app.js`;
- Telegram themeParams → CSS variables;
- Telegram initData отправляется в backend в заголовке `X-Telegram-Init-Data`;
- safe-area для iOS/Telegram;
- haptic feedback для ключевых действий;
- fallback mock mode для demo без backend;
- страницы: Overview, Tasks, AI Suggestions, Meetings, Analytics, Profile.

## Запуск локально

```bash
npm install
cp .env.example .env
npm run dev
```

Открой `http://localhost:5173`.

## Подключение backend

В `.env`:

```bash
VITE_API_BASE_URL=/api
VITE_DEV_API_TARGET=http://localhost:8000
VITE_USE_MOCKS=false
VITE_TELEGRAM_AUTH_HEADER=X-Telegram-Init-Data
```

В dev-режиме Vite проксирует `/api` на `VITE_DEV_API_TARGET`.

## Endpoints, которые использует frontend

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
```

## Telegram Mini App production checklist

1. Собери frontend:

```bash
npm run build
```

2. Размести `dist` на HTTPS-домене.
3. В BotFather укажи HTTPS URL как Web App URL.
4. На backend валидируй Telegram `initData` по hash и bot token.
5. Для production поставь `VITE_USE_MOCKS=false`.

## Docker

```bash
docker build -t komandus-frontend .
docker run -p 3000:80 komandus-frontend
```

Nginx конфиг уже включает SPA fallback и proxy `/api` на `backend:8000`.

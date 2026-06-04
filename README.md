<p align="center">
  <img src="assets/banner.png" alt="Vkatun banner" />
</p>

# profi-rsv-KYSS

## 👨‍💻 KYSS

## 👥 Команда:
- [Маслов Даниил](https://t.me/Danyayokich) ([GitHub](https://github.com/danyayok)) - Капитан команды (Team Lead), Backend Developer
- [Васильев Артём](https://t.me/avslyv) ([GitHub](https://github.com/avslyv)) - Tech Lead, Product Owner
- [Ржевский Иван](https://t.me/jeanrezerford) ([GitHub](https://github.com/BigDuckteams)) - Frontend Developer
- [Подколзин Алексей](https://t.me/fillllka) ([GitHub](https://github.com/Fosh1er)) - ML Engineer
- [Юденков Павел](https://t.me/kitkeyll) ([GitHub](https://github.com/kitkey)) - LLM Engineer

## 💡 Тема
AI-проджект-менеджер: умный бот-ассистент для командной работы

Наименование решения - «Командус».

Описание: Бот-помощник, который берёт на себя роль project-менеджера. Работает в фоне, сам следит за чатами и встречами, ведёт задачи и напоминает.

## 📚 Документация
### Дополительная документация
- [Git Flow](git-flow.md)
## 🚀 Запуск проекта

Проект собран как единый стек: backend отдает REST API с префиксом `/api`, frontend по умолчанию обращается к этому префиксу, а в Docker production-сборка проксирует запросы через nginx.

### Локальная разработка

1. Скопируйте переменные окружения при необходимости:
   ```bash
   cp .env.example .env
   ```
2. Запустите backend:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
3. Запустите frontend в отдельном терминале:
   ```bash
   cd frontend
   npm ci
   npm run dev
   ```
4. Откройте интерфейс: http://localhost:5173

Vite проксирует `/api` на `http://localhost:8000`, поэтому для обычной разработки не нужно прописывать абсолютный адрес backend. Если backend запущен на другом адресе, задайте `VITE_DEV_API_TARGET` для dev-сервера или `VITE_API_BASE_URL` для сборки.

### Запуск одним Docker Compose стеком

Сначала убедитесь в наличии необходимых файлов (package-lock.json)
А потом:
```bash
docker compose up --build
```

Перед первым запуском желательно пересоздать package-lock.json прописав:

```bash
cd frontend
rm package-lock.json
npm install
```

После запуска доступны:

- frontend: http://localhost:3000
- backend API: http://localhost:8000/api
- healthcheck: http://localhost:8000/api/health
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Важные переменные окружения

| Переменная | Назначение | Значение по умолчанию |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Базовый URL frontend-клиента | `/api` |
| `VITE_DEV_API_TARGET` | Цель Vite proxy для локальной разработки | `http://localhost:8000` |
| `CORS_ORIGINS` | Разрешённые origins для backend | `http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000` |
| `POSTGRES_*` | Подключение к PostgreSQL | см. `.env.example` |
| `CELERY_*` | Подключение Celery к Redis | см. `.env.example` |

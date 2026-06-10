from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

TASKS: list[dict[str, Any]] = [
    {
        "id": "task_1",
        "team_id": "team_1",
        "title": "Подключить Telegram webhook",
        "description": "Принять update, сохранить message и отправить job в очередь.",
        "assignee": "Даниил",
        "assignee_id": "user_daniil",
        "deadline": "2026-06-03T18:00:00+03:00",
        "status": "in_progress",
        "priority": "high",
        "source": "telegram_text",
        "confidence": 0.93,
        "created_by_ai": True,
        "kanban_provider": "external",
        "external_kanban_id": "card_task_1",
        "external_kanban_url": "https://kanban.example/card/task_1",
        "source_message_excerpt": "Даниил, подключи webhook сегодня к вечеру.",
        "status_changed_count": 2,
        "created_at": "2026-06-03T09:20:00+03:00",
        "updated_at": "2026-06-03T13:00:00+03:00",
    },
    {
        "id": "task_2",
        "team_id": "team_1",
        "title": "Собрать макет панели",
        "description": "Навигация, страницы и интерфейс, удобный для демонстрации.",
        "assignee": "Иван",
        "assignee_id": "user_ivan",
        "deadline": "2026-06-03T20:00:00+03:00",
        "status": "review",
        "priority": "high",
        "source": "telegram_text",
        "confidence": 0.89,
        "created_by_ai": True,
        "kanban_provider": "internal",
        "source_message_excerpt": "Иван, подготовь UI доски сегодня вечером.",
        "status_changed_count": 4,
        "created_at": "2026-06-03T10:00:00+03:00",
        "updated_at": "2026-06-03T15:15:00+03:00",
    },
    {
        "id": "task_3",
        "team_id": "team_1",
        "title": "Проверить ASR для голосовых",
        "description": "Прогнать тестовую голосовую фразу и сохранить качество транскрипта.",
        "assignee": "Алексей",
        "assignee_id": "user_alexey",
        "deadline": "2026-06-04T12:00:00+03:00",
        "status": "todo",
        "priority": "medium",
        "source": "telegram_voice",
        "confidence": 0.78,
        "created_by_ai": True,
        "kanban_provider": "internal",
        "source_message_excerpt": "Голосовое: надо проверить распознавание голосовых.",
        "status_changed_count": 1,
        "created_at": "2026-06-03T11:30:00+03:00",
        "updated_at": "2026-06-03T11:30:00+03:00",
    },
    {
        "id": "task_4",
        "team_id": "team_1",
        "title": "Собрать prompt для summary встречи",
        "description": "Вернуть краткое summary, решения, действия после встречи, риски и открытые вопросы.",
        "assignee": "Павел",
        "assignee_id": "user_pavel",
        "deadline": "2026-06-04T18:00:00+03:00",
        "status": "backlog",
        "priority": "medium",
        "source": "meeting_audio",
        "confidence": 0.84,
        "created_by_ai": True,
        "kanban_provider": "external",
        "external_kanban_id": "card_task_4",
        "external_kanban_url": "https://kanban.example/card/task_4",
        "source_message_excerpt": "На встрече договорились подготовить prompt для summary.",
        "status_changed_count": 0,
        "created_at": "2026-06-03T12:45:00+03:00",
        "updated_at": "2026-06-03T12:45:00+03:00",
    },
    {
        "id": "task_5",
        "team_id": "team_1",
        "title": "Закрыть полировку демонстрации",
        "description": "Проверить загрузку, пустые состояния, ссылки и финальный сценарий.",
        "assignee": "Иван",
        "assignee_id": "user_ivan",
        "deadline": "2026-06-04T21:00:00+03:00",
        "status": "done",
        "priority": "critical",
        "source": "telegram_text",
        "confidence": 0.96,
        "created_by_ai": True,
        "kanban_provider": "internal",
        "source_message_excerpt": "К вечеру надо собрать демо.",
        "status_changed_count": 5,
        "created_at": "2026-06-03T13:10:00+03:00",
        "updated_at": "2026-06-03T19:30:00+03:00",
        "closed_at": "2026-06-03T19:30:00+03:00",
    },
]

TASK_CANDIDATES: list[dict[str, Any]] = [
    {
        "id": "candidate_1",
        "team_id": "team_1",
        "title": "Сделать кнопку переноса дедлайна",
        "description": "Добавить действие в карточке задачи и отправлять POST /tasks/{id}/reschedule.",
        "assignee_raw": "Иван",
        "assignee_id": "user_ivan",
        "deadline_raw": "сегодня вечером",
        "deadline": "2026-06-03T20:00:00+03:00",
        "priority": "medium",
        "confidence": 0.73,
        "status": "pending",
        "source": "telegram_text",
        "missing_fields": [],
        "source_excerpt": "Иван, еще сделай перенос дедлайна через dashboard.",
        "source_message_url": "https://t.me/c/123456/1001",
    },
    {
        "id": "candidate_2",
        "team_id": "team_1",
        "meeting_id": "meeting_1",
        "title": "Проверить качество распознавания встречи",
        "description": "Нужно качество транскрипта и пример очистки текста до/после.",
        "assignee_raw": "Алексей",
        "assignee_id": "user_alexey",
        "deadline_raw": "завтра",
        "priority": "high",
        "confidence": 0.68,
        "status": "pending",
        "source": "meeting_audio",
        "missing_fields": ["deadline"],
        "source_excerpt": "На созвоне решили проверить качество ASR для meeting audio.",
        "source_message_url": "https://t.me/c/123456/1002",
    },
]

MEETING = {
    "id": "meeting_1",
    "title": "Ежедневная встреча: MVP Командус",
    "date": "2026-06-03",
    "summary": "Команда согласовала основной сценарий: сообщение в Telegram → извлечение задачи AI → кандидат задачи → подтверждение → карточка в канбане → напоминание → dashboard.",
    "decisions": [
        "Для фронтенда используем React + Vite + Tailwind.",
        "Панель остается удобной для демонстрации и не превращается в сложный таск-трекер.",
        "Backend отдает задачи, кандидатов, аналитику, профиль и summary встреч через REST API.",
    ],
    "action_items": [
        {"title": "Закрыть мини-канбан", "assignee": "Иван", "deadline": "сегодня", "task_id": "task_2"},
        {"title": "Подготовить pipeline извлечения задач", "assignee": "Павел", "deadline": "завтра"},
        {"title": "Проверить качество распознавания речи", "assignee": "Алексей", "deadline": "завтра", "task_id": "task_3"},
    ],
    "risks": ["Нужна стабильная связка frontend и backend для запуска одним стеком.", "Внешняя канбан-доска может быть недоступна."],
    "open_questions": ["Какие события синхронизировать во внешнюю доску первыми?", "Нужен ли отдельный режим для поручений?"],
    "created_task_candidates": TASK_CANDIDATES,
    "created_tasks": [{"id": task["id"], "title": task["title"], "assignee": task.get("assignee"), "deadline": task.get("deadline"), "status": task.get("status")} for task in TASKS[:3]],
    "transcript_quality": 0.91,
}

KNOWLEDGE = [
    {"id": "knowledge_1", "title": "Решение по канбан-адаптеру", "content": "Основная логика не зависит от конкретной доски: внешняя доска подключается через адаптер, внутренняя остается запасным вариантом.", "source_type": "meeting", "source_id": "meeting_1", "tags": ["канбан", "адаптер"], "created_at": "2026-06-03T12:00:00+03:00"},
    {"id": "knowledge_2", "title": "Зона ответственности Ивана", "content": "Иван закрывает макет dashboard, мини-канбан, AI-предложения, summary встреч, аналитику, профиль и полировку демонстрации.", "source_type": "note", "tags": ["фронтенд", "dashboard"], "created_at": "2026-06-03T13:00:00+03:00"},
    {"id": "knowledge_3", "title": "Запуск стека", "content": "Для локальной разработки фронтенд обращается к /api через Vite proxy, в Docker трафик проксируется nginx к backend-сервису.", "source_type": "note", "tags": ["devops", "api"], "created_at": "2026-06-03T14:00:00+03:00"},
]

PROFILE = {"id": "user_ivan", "name": "Иван", "telegram_username": "@ivan_frontend", "role": "JavaScript / панель / UI", "team": "Командус", "timezone": "Europe/Moscow", "xp": 420, "level": "Драйвер команды", "skills": ["React", "Vite", "Tailwind", "UX панели", "API Integration"]}
NOTES = [{"id": "note_1", "user_id": "user_ivan", "title": "Фокус frontend", "content": "Не делать backend-логику во фронте. Только UI, API-запросы и демо-состояния.", "source": "manual"}, {"id": "note_2", "user_id": "user_ivan", "title": "Решение со встречи", "content": "Итоги встречи показывают решения, действия после встречи, риски и открытые вопросы.", "source": "meeting"}]
ACHIEVEMENTS = [{"id": "ach_1", "code": "kanban_cleaner", "title": "Чистый канбан", "description": "Закрыл все задачи перед защитой.", "icon": "sparkles", "unlocked_at": "2026-06-03T19:30:00+03:00"}, {"id": "ach_2", "code": "ai_buddy", "title": "AI-помощник", "description": "Подтвердил 10 корректных AI-предложений.", "icon": "bot"}]
RECOMMENDATIONS = [{"id": "rec_1", "title": "UX панели patterns", "description": "Усилить навыки по построению операционных dashboard и пустых состояний.", "recommendation_type": "skill", "source": "история задач"}, {"id": "rec_2", "title": "Продвинутый React Query", "description": "Повторить инвалидацию, оптимистичные обновления и состояния ошибок для API-интеграций.", "recommendation_type": "practice", "source": "анализ профиля"}]


def copy_data(data: Any) -> Any:
    return deepcopy(data)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

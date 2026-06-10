# LLM Engine — «Командус»

AI reasoning layer AI-проджект-менеджера. Принимает текст сообщения (из Telegram-чата или
транскрипта голоса/встречи) и возвращает **структуру**: есть ли в сообщении задачи, какие,
кому, к какому сроку, с какой уверенностью и какое действие рекомендуется. Сам ничего не
исполняет — только понимает и возвращает JSON.

---

## Содержание
1. [Границы ответственности](#границы-ответственности)
2. [Быстрый старт](#быстрый-старт)
3. [Контракт](#контракт)
4. [Граф и роутинг](#граф-и-роутинг)
5. [Ноды: подробный функционал](#ноды-подробный-функционал)
6. [Состояние графа](#состояние-графа)
7. [Схемы данных](#схемы-данных)
8. [Confidence и action](#confidence-и-action)
9. [Промпты](#промпты)
10. [Провайдер LLM](#провайдер-llm)
11. [Ростер команды](#ростер-команды)
12. [Интеграция с бэкендом](#интеграция-с-бэкендом)
13. [Тестирование](#тестирование)
14. [Как расширять](#как-расширять)
15. [Карта файлов](#карта-файлов)
16. [Roadmap](#roadmap)

---

## Границы ответственности

Соответствует контракту §16.1 ТЗ. Pipeline **делает**: определяет intent, извлекает
задачи, нормализует данные, считает confidence, возвращает JSON.

Pipeline **не делает**: не создаёт Task в БД, не ходит в Kanban API, не пишет в Telegram,
не принимает и не исполняет финальных бизнес-решений (только **рекомендует** `action`).
Всё это — зона бэкенда (`TaskDecisionEngine`, `KanbanAdapter`).

---

## Быстрый старт

```bash
pip install -r llm_engine/requirements.txt   # openai, jinja2, langgraph, pydantic, tzdata
export OPENROUTER_API_KEY=...                 # ключ OpenRouter (или LLM_PROVIDER=local для Ollama)
```

```python
import asyncio
from llm_engine import LLMPipelineService

svc = LLMPipelineService(model="gpt-4o-mini")
result = asyncio.run(svc.extract_tasks("Павел, сделай pipeline до завтра 18:00"))
print(result)
```

Лёгкие модули (`schemas`, `roster`) импортируются без openai/langgraph — `__init__`
подгружает `LLMPipelineService` лениво.

---

## Контракт

```python
result: dict = await llm_service.extract_tasks(text, context=None)
```

### Вход
| Параметр | Тип | Описание |
|---|---|---|
| `text` | `str` | Текст сообщения или транскрипта. |
| `context` | `dict \| ExtractionContext \| None` | Контекст от бэкенда. Если не передан — собирается дефолт. |

`context` (все поля опциональны):
| Поле | Тип | Дефолт | Назначение |
|---|---|---|---|
| `now` | `datetime` | текущее время в `timezone` | Точка отсчёта для дедлайнов. |
| `timezone` | `str` | `"Europe/Moscow"` | Таймзона. |
| `sender` | `str \| None` | `None` | Кто прислал (помогает intent и self-assignment). |
| `source_type` | `SourceType` | `telegram_text` | Источник (текст/голос/встреча). |
| `source_quality` | `float` | `1.0` | Качество источника (для голоса = quality транскрипта). |
| `team_members` | `list[TeamMember]` | заглушка-ростер | Команда для резолва ответственного. |
| `open_tasks` | `list[OpenTask]` | `[]` | Открытые задачи для дедупликации. |

### Выход (`dict`)
```json
{
  "has_task": true,
  "source_type": "telegram_text",
  "raw_reasoning_summary": "task_assignment",
  "tasks": [
    {
      "title": "Сделать pipeline",
      "description": null,
      "assignee_raw": "Павел",
      "assignee_id": "user_pavel",
      "assignee_confidence": 0.97,
      "deadline_raw": "завтра 18:00",
      "deadline": "2026-06-05T18:00:00+03:00",
      "priority": "medium",
      "extraction_confidence": 0.9,
      "is_duplicate": false,
      "existing_task_id": null,
      "duplicate_confidence": 0.0,
      "confidence": 0.91,
      "action": "auto_create",
      "needs_confirmation": false
    }
  ]
}
```

| Поле задачи | Кто пишет | Описание |
|---|---|---|
| `title`, `description` | нода 2 | Текст задачи. |
| `assignee_raw`, `deadline_raw` | нода 2 | Сырые формулировки из текста (для показа человеку). |
| `deadline` | нода 2 (+нода 3 guard) | ISO 8601 или `null`. |
| `priority` | нода 2 | low/medium/high/critical. |
| `extraction_confidence` | нода 2 | Уверенность, что это реальная задача. |
| `assignee_id`, `assignee_confidence` | нода 4 | Резолв ответственного в id команды. |
| `is_duplicate`, `existing_task_id`, `duplicate_confidence` | нода 5 | Признак дубля. |
| `confidence` | нода 6 | Итоговая взвешенная уверенность. |
| `action`, `needs_confirmation` | нода 7 | Рекомендация бэкенду (не исполнение). |

---

## Граф и роутинг

LangGraph поверх общего Pydantic-состояния `GraphState`.

```
   extract_tasks(text, context)
              |
              v
        +-----------+
        |  intent   |  (LLM)  классификация сообщения -> intent.has_action_item
        +-----------+
              |
        has_action_item ?
         /            \
      false            true
        |                |
        v                v
      [END]        +-----------+
   has_task=false  |  extract  |  (LLM)  0..N задач + deadline(ISO) + extraction_confidence
                   +-----------+
                         |
                         v
                   +-----------+
                   | deadline  |  (py)   страховка: дата в прошлом -> null
                   +-----------+
                         |
                         v
                   +-----------+
                   | assignee  |  (LLM)  assignee_raw -> assignee_id (Literal[ростер])
                   +-----------+
                         |
                         v
                   +-----------+
                   |  dedup    |  (py)   title vs open_tasks -> is_duplicate
                   +-----------+
                         |
                         v
                   +-----------+
                   | confidence|  (py)   взвешенная формула -> confidence
                   +-----------+
                         |
                         v
                   +-----------+
                   |  action   |  (py)   пороги -> action + needs_confirmation
                   +-----------+
                         |
                         v
                       [END] -> TaskExtractionResult
```

**Правила роутинга:**
- **Entry point:** `intent`.
- **Условное ребро (единственное):** после `intent` функция `_after_intent(state)` возвращает
  `"extract"`, если `intent.has_action_item is True`, иначе `"end"` (-> `END`). Так шум,
  вопросы, обсуждения и статус-апдейты не доходят до дорогого экстрактора.
- **Линейная цепочка:** `extract -> deadline -> assignee -> dedup -> confidence -> action -> END`.
- **Дубликаты — это флаг, а не ветка графа.** `dedup` ставит `is_duplicate` в задачу, а `action`
  читает его и выдаёт `update_existing`. Отдельного ребра под дубль нет — так проще и
  предсказуемее.
- Если `intent.has_action_item = false`, до `extract` дело не доходит, `tasks` пустой,
  на выходе `has_task = false`.

---

## Ноды: подробный функционал

### 1. IntentClassifierNode (LLM)
- **Зачем:** дешёвый привратник. Классифицирует сообщение в один из 6 типов и ставит
  `has_action_item`, по которому роутер пускает дальше или завершает.
- **Читает:** `state.text`, `state.context.sender`.
- **Пишет:** `state.intent` (`IntentResult`).
- **Типы:** `task_assignment`, `task_proposal` (-> has_action_item=true);
  `status_update`, `question`, `discussion`, `noise` (-> false).
- **Промпт:** `prompts/intent_classify.j2`. **Схема:** `IntentResult`.
- **Граничные случаи:** отчёт «сделал/готово» -> `status_update` (не новая задача);
  один лейбл на сообщение (дробит не он, а нода 2).

### 2. TaskExtractorNode (LLM)
- **Зачем:** тяжёлая нода. Достаёт из сообщения 0..N задач, сразу нормализует дедлайн в ISO.
- **Читает:** `state.text`, `state.context.sender`, `state.context.now` (+ день недели).
- **Пишет:** `state.tasks` (`list[ExtractedTask]`).
- **Дедлайн:** LLM пишет `deadline` в ISO от «сейчас». СТРОГО: нет срока / размытый /
  не уверен -> `deadline = null` (не угадывает). `deadline_raw` сохраняется как в тексте.
- **Промпт:** `prompts/task_extract.j2`. **Схема:** `ExtractedTaskList` (из `RawExtractedTask`),
  затем маппится в `ExtractedTask`.
- **Граничные случаи:** несколько исполнителей -> несколько задач; «я сделаю» ->
  `assignee_raw = sender`; не уверен, что задача -> пустой список.

### 3. DeadlineNormalizerNode (Python)
- **Зачем:** тонкая страховка детерминированности. LLM считает дату, но если она оказалась в
  прошлом — не доверяем.
- **Читает:** `state.tasks`, `state.context.now`.
- **Пишет:** зануляет `task.deadline`, если он раньше `now`.
- Без LLM. Полный резолвер относительных дат в коде намеренно НЕ делаем — это работа LLM
  в ноде 2.

### 4. AssigneeResolverNode (LLM, constrained)
- **Зачем:** сопоставить `assignee_raw` («Паша», «фронт», «ML») с конкретным сотрудником.
- **Читает:** `state.tasks[].assignee_raw`, `state.context.team_members`.
- **Пишет:** `task.assignee_id`, `task.assignee_confidence`.
- **Ключевая фишка:** модель ответа собирается динамически (`create_model`) с полем
  `assignee_id: Literal[id'ы ростера + "unknown"]`. При strict structured output модель
  **физически не может вернуть несуществующего человека**. `"unknown"` -> оставляем `None`.
- **Батч:** все ответственные сообщения резолвятся одним вызовом. Модель кешируется
  (`lru_cache`) по набору id.
- **Промпт:** `prompts/assignee_resolve.j2` (ростер + правила по уменьшительным/ролям).
- **Пропуск:** если у задач нет `assignee_raw` или ростер пуст — нода ничего не делает.

### 5. DeduplicationNode (Python)
- **Зачем:** не плодить дубли задач.
- **Читает:** `state.tasks[].title/assignee_id`, `state.context.open_tasks`.
- **Пишет:** `is_duplicate`, `existing_task_id`, `duplicate_confidence`.
- **Алгоритм:** `difflib.SequenceMatcher` по `title` >= `threshold` (0.85) И совпадающий
  (или неизвестный) `assignee_id` -> дубль.

### 6. ConfidenceNode (Python)
- **Зачем:** свести частные уверенности в итоговую (§9.8).
- **Читает:** `intent.confidence`, `task.extraction_confidence`, `assignee_confidence`,
  наличие `deadline`, `context.source_quality`.
- **Пишет:** `task.confidence`.
- **Формула:** `intent*0.30 + extraction*0.30 + assignee*0.20 + deadline*0.10 + source_quality*0.10`.
  Нет дедлайна -> вклад 0.6 (нейтрально, не штраф).

### 7. ActionDecisionNode (Python)
- **Зачем:** перевести `confidence` и флаги в **рекомендацию** действия. Не исполняет (§16.1).
- **Читает:** `task.confidence`, `task.is_duplicate`.
- **Пишет:** `task.action` (`ActionRecommendation`), `task.needs_confirmation`.
- **Пороги:** см. [таблицу](#confidence-и-action).

---

## Состояние графа

`GraphState` (Pydantic, течёт через все ноды):
| Поле | Тип | Кто заполняет |
|---|---|---|
| `text` | `str` | вход |
| `context` | `ExtractionContext` | вход |
| `intent` | `IntentResult \| None` | нода 1 |
| `tasks` | `list[ExtractedTask]` | нода 2, обогащают 3–7 |

Каждая нода возвращает частичный апдейт (`dict`), LangGraph мёрджит его в состояние.

---

## Схемы данных

Все в `schemas.py` (плюс динамическая модель резолва ассайни в `nodes/assignee.py`).

**Enum'ы:** `MessageType` (6 типов), `Priority` (low/medium/high/critical),
`SourceType` (telegram_text/telegram_voice/meeting_audio),
`ActionRecommendation` (skip/clarify/confirm/auto_create/update_existing).

**Модели:**
- `IntentResult` — выход ноды 1.
- `RawExtractedTask` — сырой выход LLM ноды 2.
- `ExtractedTaskList` — обёртка списка для structured output ноды 2.
- `ExtractedTask` — обогащаемая модель задачи в состоянии (наследует `RawExtractedTask`).
- `TeamMember`, `OpenTask` — элементы контекста.
- `ExtractionContext` — весь контекст от бэкенда.
- `GraphState` — состояние графа.
- `TaskExtractionResult` — финальный выход (сериализуется в JSON фасадом).

---

## Confidence и action

**Confidence (нода 6):**
```
confidence = intent_confidence    * 0.30
           + extraction_confidence * 0.30
           + assignee_confidence   * 0.20
           + deadline_confidence   * 0.10   (1.0 если дедлайн есть, иначе 0.6)
           + source_quality        * 0.10
```

**Action (нода 7), приоритет сверху вниз:**
| Условие | action | needs_confirmation |
|---|---|---|
| `is_duplicate` | `update_existing` | true |
| `confidence >= 0.85` | `auto_create` | false |
| `0.55 <= confidence < 0.85` | `confirm` | true |
| `confidence < 0.55` | `skip` | false |

Пороги настраиваются: `ActionDecisionNode(auto=0.85, confirm_floor=0.55)`.

---

## Промпты

В `prompts/`, грузятся `PromptManager`'ом через Jinja (`render(name, **ctx)`).

| Файл | Нода | Назначение |
|---|---|---|
| `intent_classify.j2` | 1 | Классификация намерения. |
| `task_extract.j2` | 2 | Извлечение задач + дедлайн в ISO. |
| `assignee_resolve.j2` | 4 | Резолв ответственного по ростеру. |

Формат: `## Роль / ## Задача / ## Входные данные / ## Правила / ## Примеры`. Меняешь
поведение — правишь `.j2`, код не трогаешь.

---

## Провайдер LLM

`provider.py` -> `LLMProvider` в стиле LLMProcessing Алексея: свой клиент на **openai SDK**,
режим `api` -> **OpenRouter** (`https://openrouter.ai/api/v1`), режим `local` -> Ollama
(OpenAI-совместимый endpoint), поддержка прокси. Без litellm.

```python
async def structured(self, prompt, schema) -> BaseModel   # нативный parse() -> Pydantic
async def complete(self, system, user) -> str             # сырой текст, как у Алексея
```
`structured` использует нативный structured output (`response_format=Pydantic`) — это и даёт
гарантию `Literal[ростер]` / `Literal[task_ids]` в нодах assignee и dedup. `complete` оставлен
для паритета с пайплайном Алексея.

Конфиг через env: `LLM_PROVIDER` (api/local), `LLM_MODEL` (формат OpenRouter `provider/model`),
`OPENROUTER_API_KEY`, `OPENROUTER_BASE_URL`, `OLLAMA_BASE_URL`, `HTTP_PROXY`.
`temperature=0` для воспроизводимости.

---

## Ростер команды

`roster.py` — **заглушка** (`DEFAULT_TEAM`, 5 человек хакатона). Реальный ростер должен
приходить от бэкенда в `context.team_members`:
- из `User`-таблицы per team (правильный путь, зона Даниила), либо
- собираться ботом (отправители сообщений / `getChatAdministrators`).

`service._build_context` подставляет заглушку только если `team_members` не передан. Меняешь
источник — трогаешь `roster.py` / контекст, ноды остаются как есть.

---

## Интеграция с бэкендом

Тонкий ре-экспорт, чтобы `TaskDecisionEngine` не менялся:
```python
# app/services/llm_service.py
from llm_engine import LLMPipelineService
llm_service = LLMPipelineService()
```
`TaskDecisionEngine` зовёт `await llm_service.extract_tasks(text)` — сигнатура совместима
(`context` опционален).

Чтобы заработали `assignee_id`, дедуп и таблица `action`, бэкенду нужно:
1. передавать `context` с реальными `team_members` и `open_tasks`;
2. ветвить исполнение по `action`/`confidence` (сейчас он всегда создаёт pending-кандидата).

Это зона Даниила.

---

## Тестирование

- Лёгкие модули (`schemas`, `roster`, билдер `Literal`-модели) тестируются без LLM:
  ```bash
  python -c "from llm_engine.roster import default_team; print(default_team())"
  ```
- Полный прогон требует ключ и `pip install -r requirements.txt`.
- План: набор из 20+ фраз (см. §13.5 ТЗ) с ожидаемыми intent/задачами — гонять как
  регрессию при правке промптов.

---

## Как расширять

**Добавить ноду:**
1. Файл в `nodes/`, класс-`dataclass` с `async def __call__(self, state) -> dict`.
2. Экспорт в `nodes/__init__.py`.
3. `add_node` + ребро в `graph.py:build()`.

**Добавить промпт:** положить `.j2` в `prompts/`, звать `prompts.render("имя", **ctx)`.

**Сменить модель/провайдера:** `LLMPipelineService(model="ollama/qwen2.5")` или через env.

---

## Карта файлов

```
llm_engine/
├── __init__.py            ленивый экспорт LLMPipelineService
├── service.py             фасад extract_tasks + сборка контекста
├── graph.py               сборка и компиляция LangGraph
├── provider.py            LLMProvider (openai SDK + Ollama, structured output)
├── prompt_manager.py      Jinja-загрузчик промптов
├── schemas.py             все Pydantic-модели и enum'ы
├── roster.py              ЗАГЛУШКА ростера команды
├── prompts/
│   ├── intent_classify.j2
│   ├── task_extract.j2
│   └── assignee_resolve.j2
└── nodes/
    ├── intent.py          1. классификация (LLM)
    ├── extract.py         2. извлечение задач + дедлайн (LLM)
    ├── deadline.py        3. страховка прошлого (py)
    ├── assignee.py        4. резолв ответственного (LLM, Literal[ростер])
    ├── dedup.py           5. дедупликация (py)
    ├── confidence.py      6. итоговая уверенность (py)
    └── action.py          7. рекомендация действия (py)
```

---

## Roadmap

В MVP **не входит** (но архитектура готова): meeting summary (P1, отдельная нода+промпт под
транскрипт от Алексея), распознавание status-update в обновление статуса (P1), knowledge
Q&A / recommendations (P2). Голос отдельного кода не требует — транскрипт идёт в тот же
`extract_tasks` с `source_type=telegram_voice|meeting_audio`.

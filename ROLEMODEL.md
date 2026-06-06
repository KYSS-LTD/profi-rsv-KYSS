# Role Model: пять системных ролей и scopes

Этот документ описывает, как в проекте устроена модель ролей, почему она именно такая и как с ней эффективно работать при развитии Organizational Operating System.

## Коротко

В системе существует ровно пять системных ролей:

1. `OWNER` — владелец организации.
2. `ADMIN` — системный администратор.
3. `MANAGER` — руководитель людей.
4. `EMPLOYEE` — исполнитель.
5. `OBSERVER` — наблюдатель с read-only доступом.

Новые роли вида `HR_MANAGER`, `SALES_MANAGER`, `REGIONAL_MANAGER`, `DEPARTMENT_ADMIN`, `TEAM_LEAD`, `PRODUCT_MANAGER` и похожие добавлять нельзя.

Бизнес-смысл не должен жить в системной роли. Для бизнес-смысла используются отдельные сущности:

- должность (`Position`): CEO, CTO, HR Specialist, Team Lead, Developer;
- орг-единица (`OrganizationalUnit`): Division, Department, Team, Region, Office;
- зона ответственности (`ResponsibilityArea`): Hiring, CRM, Security, Customer Success;
- дерево подчинения (`Employee.manager_id`): кто кому подчиняется;
- делегации (`Delegation`): временная передача полномочий;
- scopes (`PermissionScope`): точная область технического доступа.

## Зачем нужна такая модель

Главная цель — разделить человеческую организационную картину и технические права доступа.

Пользователь должен понимать:

- кто его руководитель;
- кем он руководит;
- за что он отвечает;
- где перегрузка;
- что требует внимания;
- кто может согласовать или заменить человека.

Пользователь не должен разбираться в технических деталях вроде внутренних permission names, структуры БД или механики RBAC.

Поэтому роли отвечают только за технический уровень полномочий, а не за бизнес-контекст.

## Почему нельзя создавать специальные роли

Плохой путь:

```text
SALES_MANAGER
HR_MANAGER
REGIONAL_MANAGER
SENIOR_MANAGER
DEPARTMENT_ADMIN
TEAM_LEAD
PRODUCT_MANAGER
```

Такая модель быстро ломается, потому что каждая новая бизнес-ситуация порождает новую роль. Через несколько месяцев система превращается в набор исключений:

- роли начинают означать одновременно должность, доступ и место в иерархии;
- непонятно, кто чей руководитель;
- сложно мигрировать данные;
- сложно объяснить права пользователям;
- появляются конфликтующие роли;
- нельзя масштабироваться до 5000+ сотрудников без хаоса.

Правильный путь:

```text
Role: MANAGER
Position: Head of Sales
OrganizationalUnit: Sales / Europe
ResponsibilityArea: CRM
PermissionScopes: users, tasks, analytics
ReportsTo: COO via manager_id
```

Такой формат масштабируется, потому что каждая сущность отвечает только за один смысл.

## Разделение доменов

### System Role

Системная роль отвечает за технический уровень полномочий.

Примеры вопросов, на которые отвечает роль:

- может ли пользователь администрировать систему;
- может ли пользователь управлять пользователями;
- может ли пользователь назначать задачи;
- является ли пользователь read-only наблюдателем.

Роль не отвечает на вопросы:

- кто чей руководитель;
- кто владеет CRM;
- кто Head of Sales;
- кто отвечает за Hiring;
- кто входит в отдел Marketing.

### Permission Scope

Scope уточняет область технических прав.

Пример:

```text
Role: ADMIN
Scopes: users, departments
```

Такой пользователь может администрировать пользователей и отделы, но не должен автоматически получать доступ к финансам или billing.

Поддерживаемые scopes:

- `users`;
- `tasks`;
- `analytics`;
- `departments`;
- `integrations`;
- `finance`;
- `billing`;
- `settings`.

Scopes нужны, чтобы не создавать специальные роли вроде `FINANCE_ADMIN` или `INTEGRATION_ADMIN`.

### Hierarchy

Иерархия строится только через `manager_id`.

`manager_id` — единственный источник истины для reporting chain.

Нельзя выводить иерархию из:

- названия роли;
- должности;
- отдела;
- команды;
- названия орг-единицы.

Пример:

```text
Employee A.manager_id = Team Lead B
Team Lead B.manager_id = Sales Director
Sales Director.manager_id = CEO
```

Именно это дерево используется для:

- видимости менеджера;
- эскалаций;
- согласований;
- аналитики по команде;
- подсчета workload по ветке.

### Position

Должность описывает бизнес-титул человека.

Примеры:

- CEO;
- CTO;
- COO;
- Head of Sales;
- Team Lead;
- Developer;
- Designer;
- HR Specialist.

Должность не дает права доступа и не расширяет видимость.

Если пользователь имеет должность `Head of Sales`, это не значит, что он автоматически системный `MANAGER`. Управленческая видимость должна идти через `manager_id`, а технические права — через role/scopes.

### Responsibility Area

Зона ответственности описывает владение предметной областью.

Примеры:

- Hiring;
- CRM;
- Security;
- Production;
- Warehouse;
- Customer Success.

Зона ответственности нужна, чтобы система и AI могли быстро ответить:

- кто владеет hiring;
- кто отвечает за CRM;
- кто backup owner по security;
- кому передать задачу, если она относится к warehouse.

Зона ответственности не является ролью, отделом или иерархией.

### Delegation

Делегация — временная передача полномочий.

Она должна иметь:

- delegator;
- delegate;
- scope;
- start date;
- end date;
- status.

Делегация не меняет постоянную иерархию и не заменяет successor planning.

Пример:

```text
Delegator: Head of Sales
Delegate: Senior Account Manager
Scope: approvals, escalations, CRM tasks
Start: 2026-07-01
End: 2026-07-14
```

После окончания срока делегация не должна оставаться активной.

## Описание пяти ролей

### OWNER

`OWNER` — владелец организации.

Используется для:

- управления подпиской;
- управления billing;
- удаления организации;
- назначения admin users;
- полного доступа к данным организации.

Рекомендация: 1–3 пользователя на организацию.

Не используйте `OWNER` для обычных руководителей отделов.

### ADMIN

`ADMIN` — системный администратор.

Используется для:

- управления пользователями;
- управления оргструктурой;
- настройки интеграций;
- настройки permissions/scopes;
- системного обслуживания.

`ADMIN` не означает, что человек является руководителем в бизнес-иерархии.

Если администратор также управляет людьми, это должно быть отражено через `manager_id`, а не через роль.

### MANAGER

`MANAGER` — руководитель людей.

Используется для:

- просмотра своей ветки подчиненных;
- назначения работы в своей ветке;
- получения эскалаций;
- просмотра аналитики команды;
- согласований по reporting chain.

`MANAGER` не должен видеть sibling branches, если это не разрешено делегацией или отдельным backend-правилом.

Важно: `MANAGER` — это не `Head of Sales` и не `Team Lead`. `Head of Sales` и `Team Lead` — это должности.

### EMPLOYEE

`EMPLOYEE` — обычный исполнитель.

Используется для:

- выполнения задач;
- участия в workflow;
- просмотра своего профиля и собственной работы;
- получения уведомлений по своим задачам.

`EMPLOYEE` не имеет управленческой видимости.

### OBSERVER

`OBSERVER` — read-only роль.

Используется для:

- просмотра организации;
- просмотра аналитики;
- просмотра отчетов;
- аудита без права изменения данных.

`OBSERVER` не должен выполнять mutation operations.

## Как выбирать роль пользователю

Используйте следующий алгоритм:

1. Пользователь владеет юридической/платежной стороной организации?
   - Да → `OWNER`.
2. Пользователь администрирует систему, пользователей, интеграции или настройки?
   - Да → `ADMIN` + нужные scopes.
3. Пользователь управляет людьми в reporting tree?
   - Да → `MANAGER` + корректный `manager_id` у подчиненных.
4. Пользователь только выполняет работу?
   - Да → `EMPLOYEE`.
5. Пользователь должен только смотреть отчеты и аналитику?
   - Да → `OBSERVER`.

Если хочется создать новую роль, почти всегда нужно вместо этого создать или изменить:

- Position;
- ResponsibilityArea;
- OrganizationalUnit;
- PermissionScope;
- Delegation;
- RelationshipType.

## Примеры правильного моделирования

### Head of Sales

```text
Role: MANAGER
Position: Head of Sales
OrganizationalUnit: Sales
manager_id: COO
ResponsibilityArea: CRM
Scopes: users, tasks, analytics
```

Не нужно создавать роль `SALES_MANAGER`.

### HR Specialist, который владеет hiring

```text
Role: EMPLOYEE
Position: HR Specialist
ResponsibilityArea: Hiring
manager_id: Head of People
Scopes: tasks
```

Не нужно создавать роль `HR_MANAGER`, если человек не руководит людьми.

### Интеграционный администратор

```text
Role: ADMIN
Position: IT Administrator
Scopes: integrations, settings
manager_id: CTO или IT Lead
```

Не нужно создавать роль `INTEGRATION_ADMIN`.

### Финансовый наблюдатель

```text
Role: OBSERVER
Position: Finance Controller
Scopes: analytics, finance
manager_id: CFO
```

Не нужно создавать роль `FINANCE_VIEWER`.

### Временная замена руководителя

```text
Permanent role: MANAGER
Position: Head of Operations
Delegation:
  delegate: Operations Coordinator
  scope: approvals, escalations
  start_date: 2026-08-01
  end_date: 2026-08-20
```

Не нужно менять роль заместителя на `MANAGER`, если он временно согласует задачи только по делегации.

## Как это связано с AI

AI должен получать структурированный организационный контекст:

- hierarchy через `manager_id`;
- role/scopes для технических полномочий;
- positions для бизнес-титулов;
- organizational units для группировок;
- responsibility areas для ownership;
- delegations для временных полномочий;
- successors для replacement planning;
- workload и tasks для operational picture.

AI не должен угадывать иерархию по названию роли или должности.

Правильный вопрос к данным:

```text
Кто manager этого employee_id?
```

Неправильный вопрос:

```text
Есть ли в названии роли слово Manager?
```

## Правила для разработки

### Do

- Используйте только пять системных ролей.
- Используйте `normalize_role()` при чтении legacy данных.
- Проверяйте permissions на backend, а не только в UI.
- Стройте видимость manager users через `manager_id` subtree.
- Используйте scopes для ограничения областей доступа.
- Добавляйте business meaning через Position, ResponsibilityArea и OrganizationalUnit.
- Логируйте изменения ролей, иерархии, делегаций, responsibility areas и approvals.

### Don't

- Не добавляйте новые system roles.
- Не кодируйте department или position внутри role name.
- Не выводите hierarchy из role name.
- Не считайте frontend restrictions безопасностью.
- Не давайте permissions через Position.
- Не давайте visibility через Department.
- Не оставляйте expired delegations активными.

## Migration и legacy роли

Исторические роли мапятся в новую модель:

| Legacy role | New role |
| --- | --- |
| `SUPER_ADMIN` | `OWNER` |
| `ORG_OWNER` | `OWNER` |
| `PRODUCT_MANAGER` | `ADMIN` |
| `DEPARTMENT_MANAGER` | `MANAGER` |
| `TEAM_LEAD` | `MANAGER` |
| `VIEWER` | `OBSERVER` |
| `EMPLOYEE` | `EMPLOYEE` |

Цель маппинга — сохранить работоспособность существующих организаций и убрать размножение ролей.

## Быстрая памятка

Если нужно ответить на вопрос:

- "Какие технические права у пользователя?" → смотрим `role` + `permission_scopes`.
- "Кто руководитель пользователя?" → смотрим `manager_id`.
- "Какая у пользователя должность?" → смотрим `position_id` / `position`.
- "К какой части организации он относится?" → смотрим `organizational_unit_id`, `department_id`, `team_id`.
- "За что он отвечает?" → смотрим `ResponsibilityArea`.
- "Кто временно заменяет человека?" → смотрим active `Delegation`.
- "Кто постоянный преемник?" → смотрим `Successor`.

## Главный принцип

Роль — это технический уровень доступа.

Иерархия — это `manager_id`.

Должность — это бизнес-титул.

Responsibility Area — это ownership.

Delegation — это временная власть.

Scopes — это точная область permissions.

Эти понятия нельзя смешивать.

## Organization modes

Командус поддерживает два режима организации.

### SIMPLE mode

`SIMPLE` — режим для компаний примерно до 30 сотрудников.

В этом режиме интерфейс и правила намеренно проще:

- отделы и команды не обязательны;
- делегации и сложная оргструктура скрываются из основного сценария;
- `MANAGER` может видеть всю компанию и выполнять базовое управление сотрудниками;
- Telegram и YouGile можно подключить без полной организационной декомпозиции.

SIMPLE mode нужен, чтобы малые компании не сталкивались с enterprise-сложностью в первый день.

### HIERARCHY mode

`HIERARCHY` — режим для компаний с несколькими уровнями управления.

В этом режиме включаются:

- Departments;
- Teams;
- manager tree;
- Responsibility Areas;
- Delegations;
- source mapping для Telegram chats/topics;
- строгая manager visibility по `manager_id`.

Переход из SIMPLE в HIERARCHY должен выполняться через мастер настройки структуры, а не через скрытый флаг в базе.

## Telegram identity и activation

Менеджер никогда не вводит `telegram_id`, потому что сотрудник его не знает, а Telegram Bot API не позволяет получить user id по username.

Правильный поток:

1. Менеджер создает сотрудника и указывает `telegram_username`, например `@ivan_petrov`.
2. Сотрудник пишет боту `/start`.
3. Бот получает `telegram_id`, `username`, `first_name`, `last_name`.
4. Командус сопоставляет `username` с сохраненным `telegram_username`.
5. После совпадения сохраняется `telegram_id`, а статус становится `CONNECTED`.
6. Сотруднику отправляется activation link.

Постоянные пароли не отправляются. Сотрудник активирует аккаунт по одноразовому token и сам задает пароль.

## Telegram TaskSource

Рабочие чаты и supergroup topics моделируются через `TaskSource`.

Типы источников:

- `TELEGRAM_CHAT` — весь обычный Telegram chat;
- `TELEGRAM_TOPIC` — конкретный topic внутри supergroup.

Каждый источник можно привязать к `Department` или `Team`.

Пример:

```text
Backend topic → Backend team
DevOps topic → DevOps team
Sales chat → Sales department
```

AI-анализ задач обязан учитывать source context: отдел, команду, сотрудников этой команды и зоны ответственности.

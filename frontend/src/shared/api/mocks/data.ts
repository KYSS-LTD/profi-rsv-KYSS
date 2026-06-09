// ДЕМО-ДАННЫЕ для показа интерфейса без бэкенда.
// Связный набор по теме СМК/аудитов (та же предметная область, что и транскрипции созвонов).
// Коллекции мутабельны — мок-роутер меняет их при POST/PATCH, чтобы демо ощущалось «живым».
// Всё включается одним флагом в ./enabled.ts. Чтобы убрать моки — см. README в этой папке.

import { TaskCandidate } from '../../../entities/candidate/types';
import { KnowledgeItem } from '../../../entities/knowledge/types';
import { MeetingSummary } from '../../../entities/meeting/types';
import {
  BoardIntegration,
  CurrentUser,
  DashboardAnalytics,
  Department,
  Employee,
  KomandusTask,
  OrganizationChat,
  Team,
} from '../../../entities/saas/types';
import { Task as LegacyTask } from '../../../entities/task/types';
import { Achievement, Note, Recommendation, UserDigest, UserProfile } from '../../../entities/user/types';
import { OrgMapResponse } from '../orgOS';
import { HierarchyWizardResponse, OrganizationModeResponse, TaskSource } from '../orgV2';
import { LeaderboardItem, TeamAnalytics } from '../../../entities/analytics/types';

export const ORG_ID = 'org_komandus';
const NOW = '2026-06-10T09:00:00Z';

// ─── Сотрудники ────────────────────────────────────────────────────────────
export const employees: Employee[] = [
  { id: 'emp_olga', organization_id: ORG_ID, user_id: 'usr_olga', manager_id: null, full_name: 'Иванова Ольга', email: 'admin@komandus.ru', role: 'OWNER', department_id: 'dep_smk', team_id: 'team_smk_core', position: 'Руководитель СМК', telegram_username: 'olga_smk', telegram_status: 'CONNECTED', telegram_id: 100000001, telegram_connected_at: '2026-03-01T10:00:00Z', is_active: true },
  { id: 'emp_elena', organization_id: ORG_ID, user_id: 'usr_elena', manager_id: 'emp_olga', full_name: 'Сидорова Елена', email: 'sidorova@komandus.ru', role: 'MANAGER', department_id: 'dep_audit', team_id: 'team_audit_1', position: 'Руководитель отдела аудита', telegram_username: 'elena_audit', telegram_status: 'CONNECTED', telegram_id: 100000002, telegram_connected_at: '2026-03-02T10:00:00Z', is_active: true },
  { id: 'emp_dasha_s', organization_id: ORG_ID, user_id: 'usr_dasha_s', manager_id: 'emp_olga', full_name: 'Смирнова Дарья', email: 'smirnova@komandus.ru', role: 'EMPLOYEE', department_id: 'dep_smk', team_id: 'team_smk_core', position: 'Специалист СМК', telegram_username: 'dasha_smk', telegram_status: 'CONNECTED', telegram_id: 100000003, is_active: true },
  { id: 'emp_dasha_k', organization_id: ORG_ID, user_id: 'usr_dasha_k', manager_id: 'emp_elena', full_name: 'Кудинова Дарья', email: 'kudinova@komandus.ru', role: 'EMPLOYEE', department_id: 'dep_audit', team_id: 'team_audit_1', position: 'Внутренний аудитор', telegram_username: 'dasha_audit', telegram_status: 'CONNECTED', telegram_id: 100000004, is_active: true },
  { id: 'emp_nastya', organization_id: ORG_ID, user_id: 'usr_nastya', manager_id: 'emp_olga', full_name: 'Петрова Анастасия', email: 'petrova@komandus.ru', role: 'EMPLOYEE', department_id: 'dep_office', team_id: null, position: 'Делопроизводитель', telegram_username: 'nastya_doc', telegram_status: 'CONNECTED', telegram_id: 100000005, is_active: true },
  { id: 'emp_oksana', organization_id: ORG_ID, user_id: 'usr_oksana', manager_id: 'emp_olga', full_name: 'Ефарова Оксана', email: 'efarova@komandus.ru', role: 'EMPLOYEE', department_id: 'dep_smk', team_id: 'team_smk_core', position: 'Бизнес-аналитик', telegram_username: 'oksana_ba', telegram_status: 'PENDING', is_active: true },
  { id: 'emp_tatiana', organization_id: ORG_ID, user_id: 'usr_tatiana', manager_id: 'emp_elena', full_name: 'Гочнева Татьяна', email: 'gochneva@komandus.ru', role: 'EMPLOYEE', department_id: 'dep_audit', team_id: 'team_audit_ext', position: 'Специалист по аудиту', telegram_username: 'tatiana_audit', telegram_status: 'CONNECTED', telegram_id: 100000007, is_active: true },
  { id: 'emp_andrey', organization_id: ORG_ID, user_id: 'usr_andrey', manager_id: 'emp_olga', full_name: 'Жуковский Андрей', email: 'zhukovsky@komandus.ru', role: 'MANAGER', department_id: 'dep_audit', team_id: 'team_audit_ext', position: 'Руководитель направления продаж', telegram_username: 'andrey_sales', telegram_status: 'NOT_FOUND', is_active: true },
];

// ─── Текущий пользователь (admin@komandus.ru · OWNER) ────────────────────────
export const currentUser: CurrentUser = {
  id: 'usr_olga',
  organization_id: ORG_ID,
  email: 'admin@komandus.ru',
  full_name: 'Иванова Ольга',
  role: 'OWNER',
  department_id: 'dep_smk',
  team_id: 'team_smk_core',
  must_change_password: false,
  permissions: ['org:manage', 'tasks:write', 'employees:manage', 'boards:manage'],
  permission_scopes: ['org:all'],
};

// ─── Отделы ──────────────────────────────────────────────────────────────────
export const departments: Department[] = [
  { id: 'dep_smk', organization_id: ORG_ID, name: 'Служба качества (СМК)', description: 'Система менеджмента качества, анализ со стороны руководства', employee_count: 3, task_count: 5, overdue_count: 1, efficiency: 86, created_at: '2026-01-10T10:00:00Z', updated_at: NOW },
  { id: 'dep_audit', organization_id: ORG_ID, name: 'Отдел внутреннего аудита', description: 'Аудиты 1 стороны, внешние аудиты, ПКМ', employee_count: 4, task_count: 6, overdue_count: 1, efficiency: 79, created_at: '2026-01-10T10:00:00Z', updated_at: NOW },
  { id: 'dep_office', organization_id: ORG_ID, name: 'Делопроизводство', description: 'Приказы, ознакомления, документооборот', employee_count: 1, task_count: 1, overdue_count: 0, efficiency: 92, created_at: '2026-01-10T10:00:00Z', updated_at: NOW },
];

// ─── Команды ──────────────────────────────────────────────────────────────────
export const teams: Team[] = [
  { id: 'team_smk_core', organization_id: ORG_ID, department_id: 'dep_smk', name: 'Анализ со стороны руководства', description: 'Сбор входных данных и подготовка отчёта', created_at: '2026-01-12T10:00:00Z', updated_at: NOW },
  { id: 'team_audit_1', organization_id: ORG_ID, department_id: 'dep_audit', name: 'Аудиты 1 стороны', description: 'Внутренние аудиты подразделений', created_at: '2026-01-12T10:00:00Z', updated_at: NOW },
  { id: 'team_audit_ext', organization_id: ORG_ID, department_id: 'dep_audit', name: 'Внешние аудиты', description: 'Сертификационные и надзорные аудиты', created_at: '2026-01-12T10:00:00Z', updated_at: NOW },
];

// ─── Telegram-чаты ────────────────────────────────────────────────────────────
export const chats: OrganizationChat[] = [
  { id: 'chat_smk', organization_id: ORG_ID, department_id: 'dep_smk', team_id: 'team_smk_core', telegram_chat_id: -1001234567001, title: 'СМК — планёрки', chat_type: 'supergroup', members_count: 8, is_active: true, ai_enabled: true, bot_is_admin: true, connected_at: '2026-03-01T10:00:00Z' },
  { id: 'chat_audit', organization_id: ORG_ID, department_id: 'dep_audit', team_id: 'team_audit_1', telegram_chat_id: -1001234567002, title: 'Аудит 1 стороны', chat_type: 'supergroup', members_count: 5, is_active: true, ai_enabled: true, bot_is_admin: true, connected_at: '2026-03-03T10:00:00Z' },
  { id: 'chat_office', organization_id: ORG_ID, department_id: 'dep_office', team_id: null, telegram_chat_id: -1001234567003, title: 'Делопроизводство', chat_type: 'group', members_count: 4, is_active: true, ai_enabled: false, bot_is_admin: false, connected_at: '2026-03-05T10:00:00Z' },
];

// ─── Задачи Командуса (Kanban + AI Inbox) ──────────────────────────────────────
const M = 'gpt-4o-mini';
export const tasks: KomandusTask[] = [
  { id: 'tsk_01', organization_id: ORG_ID, employee_id: 'emp_dasha_k', department_id: 'dep_audit', organization_chat_id: 'chat_audit', title: 'Сформировать чек-листы для внутреннего аудита МП Югра', description: 'Подготовить чек-листы и занести в Чекофис.', status: 'PENDING_CONFIRMATION', due_at: '2026-04-15T15:00:00Z', llm_confidence: 0.92, llm_model: M, source_chat_id: -1001234567002, ai_summary: 'Кудинова формирует чек-листы для внутреннего аудита МП Югра, срок 15 апреля.', source_excerpt: '...сформировать чек-листы для внутреннего аудита МП Югра срок 15 апреля ответственную кудинова.', created_at: '2026-04-13T10:05:00Z', updated_at: '2026-04-13T10:05:00Z' },
  { id: 'tsk_02', organization_id: ORG_ID, employee_id: 'emp_dasha_k', department_id: 'dep_audit', organization_chat_id: 'chat_audit', title: 'Сформировать программу аудита 1 стороны', description: 'Программа аудита 1 стороны, срок 17 апреля.', status: 'PENDING_CONFIRMATION', due_at: '2026-04-17T15:00:00Z', llm_confidence: 0.88, llm_model: M, source_chat_id: -1001234567002, ai_summary: 'Программа аудита 1 стороны, ответственная Кудинова, срок 17 апреля.', source_excerpt: '...сформировать программу аудита 1 стороны ответственно кудинова срок 17 апреля.', created_at: '2026-04-13T10:06:00Z', updated_at: '2026-04-13T10:06:00Z' },
  { id: 'tsk_03', organization_id: ORG_ID, employee_id: 'emp_dasha_s', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Доработать файл «Цели и риски»', description: 'Доработать вдвоём со Смирновой и Ефаровой.', status: 'DETECTED', due_at: '2026-04-17T15:00:00Z', llm_confidence: 0.79, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Доработать файл цели и риски, срок до 17 числа, ответственные Смирнова и Ефарова.', source_excerpt: '...под протокол тоже задачка доработать файл цели и риски. Срок эта неделя, то есть до 17 числа.', created_at: '2026-04-13T10:07:00Z', updated_at: '2026-04-13T10:07:00Z' },
  { id: 'tsk_04', organization_id: ORG_ID, employee_id: 'emp_dasha_s', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Подготовить шаблон типового слайда для анализа', description: 'Три слайда на каждого владельца процесса.', status: 'TO_DO', due_at: null, llm_confidence: 0.9, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Смирнова готовит шаблон типового слайда для анализа со стороны руководства.', source_excerpt: 'Даша Смирнова у нас подготовила шаблон типового слайда, мы с вами его обсуждали.', created_at: '2026-04-09T11:30:00Z', updated_at: '2026-04-13T10:08:00Z' },
  { id: 'tsk_05', organization_id: ORG_ID, employee_id: 'emp_olga', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Запросить входные данные анализа со стороны руководства', description: 'Разослать форму запроса владельцам процессов.', status: 'IN_PROGRESS', due_at: '2026-04-17T15:00:00Z', llm_confidence: 0.83, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Начать запрос входных данных по анализу со стороны руководства.', source_excerpt: '...параллельно мы начинаем деятельность по запросу этих входных данных по анализу со стороны руководства.', created_at: '2026-04-13T10:09:00Z', updated_at: '2026-04-14T09:00:00Z' },
  { id: 'tsk_06', organization_id: ORG_ID, employee_id: 'emp_olga', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Подготовить процент загрузки документов', description: 'Подготовить отчёт по проценту загрузки документов к совещанию.', status: 'IN_PROGRESS', due_at: '2026-04-14T12:00:00Z', llm_confidence: 0.86, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Подготовить процент загрузки документов как у исполнителя.', source_excerpt: '...подключить на это совещание по поводу процента загрузки документов.', created_at: '2026-04-13T10:10:00Z', updated_at: '2026-04-14T09:30:00Z' },
  { id: 'tsk_07', organization_id: ORG_ID, employee_id: 'emp_tatiana', department_id: 'dep_audit', organization_chat_id: 'chat_audit', title: 'Подготовить отчёт и ПКМ по аудиту 1 стороны', description: 'Отчёт и план корректирующих мероприятий.', status: 'REVIEW', due_at: '2026-04-17T15:00:00Z', llm_confidence: 0.91, llm_model: M, source_chat_id: -1001234567002, ai_summary: 'Гочнева Татьяна готовит отчёт и ПКМ по аудиту 1 стороны, срок 17 апреля.', source_excerpt: 'гочнева Татьяна 17 апреля срок подготовка отчёта и ПКМ по аудиту 1 стороны.', created_at: '2026-04-13T10:11:00Z', updated_at: '2026-04-16T14:00:00Z' },
  { id: 'tsk_08', organization_id: ORG_ID, employee_id: 'emp_oksana', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Провести рабочую встречу по бизнес-процессу А3', description: 'Постановка целей и оценка рисков на 2026 год.', status: 'REVIEW', due_at: '2026-04-13T12:00:00Z', llm_confidence: 0.84, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Рабочая встреча по бизнес-процессу А3, оценка рисков и цели на 2026 год.', source_excerpt: '...провести рабочую встречу по бизнес процессу а 3 по постановке цели и оценке рисков на 26 год. Срок 13 апреля.', created_at: '2026-04-13T10:12:00Z', updated_at: '2026-04-13T15:00:00Z' },
  { id: 'tsk_09', organization_id: ORG_ID, employee_id: 'emp_olga', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Утвердить решение об аудитах на год и приказы об аудитах 1 стороны', description: 'Решение и приказы утверждены.', status: 'DONE', due_at: '2026-04-06T15:00:00Z', llm_confidence: 0.95, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Решение об аудитах на год и приказы об аудитах 1 стороны выполнены.', source_excerpt: 'Решение об аудитах на год и приказы об аудитах 1 страны выполнены.', accepted_at: '2026-04-06T10:00:00Z', completed_at: '2026-04-08T16:00:00Z', created_at: '2026-04-06T09:00:00Z', updated_at: '2026-04-08T16:00:00Z' },
  { id: 'tsk_10', organization_id: ORG_ID, employee_id: 'emp_elena', department_id: 'dep_audit', organization_chat_id: 'chat_audit', title: 'Определить состав команды аудиторов', description: 'Команда аудиторов на аудит 1 стороны определена.', status: 'DONE', due_at: '2026-04-10T15:00:00Z', llm_confidence: 0.9, llm_model: M, source_chat_id: -1001234567002, ai_summary: 'Сидорова определилась с командой аудиторов.', source_excerpt: 'Я определилась с командой аудиторов и на этой неделе программа и чеклисты.', accepted_at: '2026-04-09T10:00:00Z', completed_at: '2026-04-10T12:00:00Z', created_at: '2026-04-09T09:00:00Z', updated_at: '2026-04-10T12:00:00Z' },
  { id: 'tsk_11', organization_id: ORG_ID, employee_id: 'emp_olga', department_id: 'dep_smk', organization_chat_id: 'chat_smk', title: 'Запросить результаты выполнения показателей, утверждённых в руководстве', description: 'Плановое и фактическое значение за отчётный период.', status: 'DONE', due_at: '2026-04-12T15:00:00Z', llm_confidence: 0.82, llm_model: M, source_chat_id: -1001234567001, ai_summary: 'Запросить результаты выполнения утверждённых показателей.', source_excerpt: '...запрашиваем предоставить результаты выполнения показателей, которые утверждены в руководстве.', accepted_at: '2026-04-10T10:00:00Z', completed_at: '2026-04-12T11:00:00Z', created_at: '2026-04-10T09:00:00Z', updated_at: '2026-04-12T11:00:00Z' },
  { id: 'tsk_12', organization_id: ORG_ID, employee_id: 'emp_nastya', department_id: 'dep_office', organization_chat_id: 'chat_office', title: 'Подготовить листы ознакомления по приказам', description: 'Делопроизводство после отпуска: ознакомления и решения.', status: 'TO_DO', due_at: '2026-04-18T15:00:00Z', llm_confidence: 0.77, llm_model: M, source_chat_id: -1001234567003, ai_summary: 'Петрова разгребает приказы и готовит листы ознакомления.', source_excerpt: 'Я разгребаю по приказам ознакомления и решения приходили, делаю листы.', created_at: '2026-04-13T10:13:00Z', updated_at: '2026-04-13T10:13:00Z' },
];

// ─── Аналитика (Dashboard + Аналитика v2) ──────────────────────────────────────
export const dashboard: DashboardAnalytics = {
  total_tasks: 12,
  in_work: 2,
  completed: 3,
  overdue: 2,
  average_completion_time: 18,
  average_response_time: 4,
  ai_accuracy: 95,
  ai_tasks: 11,
  acceptance_percent: 88,
  rejection_percent: 12,
  pie_statuses: { 'Обнаружено': 1, 'На подтверждении': 2, 'К выполнению': 2, 'В работе': 2, 'На проверке': 2, 'Завершено': 3 },
  top_employees: [
    { employee_id: 'emp_dasha_k', employee_name: 'Кудинова Дарья', tasks: 4 },
    { employee_id: 'emp_olga', employee_name: 'Иванова Ольга', tasks: 4 },
    { employee_id: 'emp_dasha_s', employee_name: 'Смирнова Дарья', tasks: 2 },
    { employee_id: 'emp_tatiana', employee_name: 'Гочнева Татьяна', tasks: 1 },
    { employee_id: 'emp_oksana', employee_name: 'Ефарова Оксана', tasks: 1 },
  ],
  departments: [
    { department_id: 'dep_audit', department_name: 'Отдел внутреннего аудита', tasks: 6 },
    { department_id: 'dep_smk', department_name: 'Служба качества (СМК)', tasks: 5 },
    { department_id: 'dep_office', department_name: 'Делопроизводство', tasks: 1 },
  ],
  closed_by_day: [
    { date: '2026-06-04', completed: 1 },
    { date: '2026-06-05', completed: 3 },
    { date: '2026-06-06', completed: 2 },
    { date: '2026-06-07', completed: 0 },
    { date: '2026-06-08', completed: 4 },
    { date: '2026-06-09', completed: 2 },
    { date: '2026-06-10', completed: 1 },
  ],
  burnup: [
    { date: '2026-06-04', completed_total: 18 },
    { date: '2026-06-05', completed_total: 21 },
    { date: '2026-06-06', completed_total: 23 },
    { date: '2026-06-07', completed_total: 23 },
    { date: '2026-06-08', completed_total: 27 },
    { date: '2026-06-09', completed_total: 29 },
    { date: '2026-06-10', completed_total: 30 },
  ],
  attention: [
    { type: 'overdue', title: 'Просроченные задачи', count: 2 },
    { type: 'pending', title: 'Ждут подтверждения AI', count: 2 },
    { type: 'unassigned', title: 'Без исполнителя', count: 0 },
  ],
  activity: [
    { at: '2026-06-10T08:40:00Z', text: 'AI выделил 2 новые задачи из чата «СМК — планёрки».' },
    { at: '2026-06-10T08:05:00Z', text: 'Гочнева Татьяна отправила «Отчёт и ПКМ по аудиту 1 стороны» на проверку.' },
    { at: '2026-06-09T17:20:00Z', text: 'Иванова Ольга завершила задачу «Запросить результаты показателей».' },
    { at: '2026-06-09T11:10:00Z', text: 'Кудинова Дарья приняла задачу «Сформировать чек-листы аудита».' },
  ],
};

// ─── Карта организации ──────────────────────────────────────────────────────────
const workload = (active: number, overdue: number, blocked: number, completed: number, score: number) => ({ active_tasks: active, overdue_tasks: overdue, blocked_tasks: blocked, completed_tasks: completed, workload_score: score });

export const orgMap: OrgMapResponse = {
  nodes: [
    {
      id: 'emp_olga', user_id: 'usr_olga', full_name: 'Иванова Ольга', position: 'Руководитель СМК', role: 'OWNER', manager_id: null,
      direct_reports: 5, indirect_reports: 7, responsibilities: ['Система менеджмента качества', 'Анализ со стороны руководства'], active_delegations: 2,
      workload: workload(4, 1, 0, 12, 72), requires_attention: false,
      children: [
        {
          id: 'emp_elena', user_id: 'usr_elena', full_name: 'Сидорова Елена', position: 'Руководитель отдела аудита', role: 'MANAGER', manager_id: 'emp_olga',
          direct_reports: 2, indirect_reports: 2, responsibilities: ['Внутренние аудиты', 'Внешние аудиты'], active_delegations: 1,
          workload: workload(3, 1, 1, 8, 84), requires_attention: true,
          children: [
            { id: 'emp_dasha_k', user_id: 'usr_dasha_k', full_name: 'Кудинова Дарья', position: 'Внутренний аудитор', role: 'EMPLOYEE', manager_id: 'emp_elena', direct_reports: 0, indirect_reports: 0, responsibilities: ['Чек-листы аудита', 'Программа аудита'], active_delegations: 0, workload: workload(4, 0, 0, 6, 68), requires_attention: false, children: [] },
            { id: 'emp_tatiana', user_id: 'usr_tatiana', full_name: 'Гочнева Татьяна', position: 'Специалист по аудиту', role: 'EMPLOYEE', manager_id: 'emp_elena', direct_reports: 0, indirect_reports: 0, responsibilities: ['Отчёты по аудиту', 'ПКМ'], active_delegations: 0, workload: workload(2, 1, 0, 5, 81), requires_attention: true, children: [] },
          ],
        },
        { id: 'emp_dasha_s', user_id: 'usr_dasha_s', full_name: 'Смирнова Дарья', position: 'Специалист СМК', role: 'EMPLOYEE', manager_id: 'emp_olga', direct_reports: 0, indirect_reports: 0, responsibilities: ['Шаблоны слайдов', 'Цели и риски'], active_delegations: 0, workload: workload(2, 0, 0, 4, 55), requires_attention: false, children: [] },
        { id: 'emp_oksana', user_id: 'usr_oksana', full_name: 'Ефарова Оксана', position: 'Бизнес-аналитик', role: 'EMPLOYEE', manager_id: 'emp_olga', direct_reports: 0, indirect_reports: 0, responsibilities: ['Бизнес-процессы', 'Оценка рисков'], active_delegations: 0, workload: workload(1, 0, 0, 3, 40), requires_attention: false, children: [] },
        { id: 'emp_nastya', user_id: 'usr_nastya', full_name: 'Петрова Анастасия', position: 'Делопроизводитель', role: 'EMPLOYEE', manager_id: 'emp_olga', direct_reports: 0, indirect_reports: 0, responsibilities: ['Приказы', 'Ознакомления'], active_delegations: 0, workload: workload(1, 0, 0, 7, 35), requires_attention: false, children: [] },
        { id: 'emp_andrey', user_id: 'usr_andrey', full_name: 'Жуковский Андрей', position: 'Руководитель направления продаж', role: 'MANAGER', manager_id: 'emp_olga', direct_reports: 0, indirect_reports: 0, responsibilities: ['Внешние клиенты', 'Согласование аудитов'], active_delegations: 1, workload: workload(2, 0, 1, 2, 60), requires_attention: false, children: [] },
      ],
    },
  ],
  attention: [
    { type: 'overload', title: 'Перегрузка: Сидорова Елена', count: 1, severity: 'warning', explanation: 'Нагрузка 84% — близко к пределу из-за параллельных аудитов.' },
    { type: 'overdue', title: 'Просрочка: Гочнева Татьяна', count: 1, severity: 'critical', explanation: 'Отчёт по аудиту 1 стороны просрочен на 2 дня.' },
  ],
  health: { score: 82, causes: ['Один сотрудник перегружен (>80%)', '2 задачи просрочены', 'Все руководители назначены, делегации настроены'] },
  role_model: ['OWNER', 'ADMIN', 'MANAGER', 'EMPLOYEE', 'OBSERVER'],
  permission_scopes: ['org:read', 'tasks:write', 'audit:manage', 'employees:read'],
};

// ─── Режим организации и источники задач (Setup Wizard) ─────────────────────────
export const orgMode: OrganizationModeResponse = {
  mode: 'HIERARCHY',
  hierarchy_setup_state: { step: 5, departments_ready: true, teams_ready: true, managers_ready: true, employees_distributed: true, telegram_sources_ready: true },
};

export const hierarchyWizard: HierarchyWizardResponse = {
  mode: 'HIERARCHY',
  hierarchy_setup_state: { step: 5, departments_ready: true, teams_ready: true, managers_ready: true, employees_distributed: true, telegram_sources_ready: true },
  can_confirm: true,
  checklist: ['Отделы созданы', 'Команды распределены', 'Руководители назначены', 'Сотрудники распределены', 'Telegram-источники подключены'],
};

export const taskSources: TaskSource[] = [
  { id: 'src_smk', organization_id: ORG_ID, source_type: 'TELEGRAM_CHAT', telegram_chat_id: -1001234567001, telegram_topic_id: null, title: 'СМК — планёрки', department_id: 'dep_smk', team_id: 'team_smk_core', is_active: true, ai_enabled: true, created_at: '2026-03-01T10:00:00Z', updated_at: NOW },
  { id: 'src_audit', organization_id: ORG_ID, source_type: 'TELEGRAM_CHAT', telegram_chat_id: -1001234567002, telegram_topic_id: null, title: 'Аудит 1 стороны', department_id: 'dep_audit', team_id: 'team_audit_1', is_active: true, ai_enabled: true, created_at: '2026-03-03T10:00:00Z', updated_at: NOW },
];

// ─── Интеграции (Доски) ──────────────────────────────────────────────────────────
export const boardIntegration: BoardIntegration = {
  id: 'board_yougile', organization_id: ORG_ID, provider: 'yougile', name: 'YouGile — СМК и аудиты', external_project_id: 'prj_demo', external_board_id: 'brd_demo', department_id: 'dep_audit', team_id: null, is_active: true, metadata_json: { columns: 4, members: 8 },
};

// ─── Кандидаты задач (Suggestions) ──────────────────────────────────────────────
export const candidates: TaskCandidate[] = [
  { id: 'cand_01', team_id: 'team_smk_core', meeting_id: 'm1', title: 'Доработать файл «Цели и риски»', description: 'Доработать вдвоём, срок до 17 апреля', assignee_raw: 'Смирнова, Ефарова', deadline_raw: '17.04.2026', deadline: '2026-04-17T15:00:00Z', priority: 'high', confidence: 0.79, status: 'pending', source: 'meeting_audio', missing_fields: ['assignee_id'], source_excerpt: '...доработать файл цели и риски. Срок эта неделя, то есть до 17 числа.', created_at: '2026-04-13T10:07:00Z' },
  { id: 'cand_02', team_id: 'team_audit_1', meeting_id: 'm1', title: 'Сформировать программу аудита 1 стороны', description: 'Программа аудита 1 стороны', assignee_raw: 'Кудинова', deadline_raw: '17.04.2026', deadline: '2026-04-17T15:00:00Z', priority: 'medium', confidence: 0.88, status: 'pending', source: 'meeting_audio', source_excerpt: '...сформировать программу аудита 1 стороны ответственно кудинова срок 17 апреля.', created_at: '2026-04-13T10:06:00Z' },
];

// ─── Профиль и личные данные ──────────────────────────────────────────────────────
export const profile: UserProfile = {
  id: 'usr_olga', name: 'Иванова Ольга', telegram_username: 'olga_smk', role: 'OWNER', team: 'Анализ со стороны руководства', timezone: 'Europe/Moscow',
  notification_preferences: ['deadlines', 'ai_suggestions'], xp: 1840, level: 'Эксперт СМК', skills: ['Аудит', 'СМК', 'Управление рисками', 'Анализ данных'],
};

export const profileTasks: LegacyTask[] = [
  { id: 'tsk_05', team_id: 'team_smk_core', title: 'Запросить входные данные анализа со стороны руководства', status: 'in_progress', priority: 'high', source: 'meeting_audio', deadline: '2026-04-17T15:00:00Z', assignee: 'Иванова Ольга', created_by_ai: true, confidence: 0.83 },
  { id: 'tsk_06', team_id: 'team_smk_core', title: 'Подготовить процент загрузки документов', status: 'in_progress', priority: 'medium', source: 'meeting_audio', deadline: '2026-04-14T12:00:00Z', assignee: 'Иванова Ольга', created_by_ai: true, confidence: 0.86 },
  { id: 'tsk_11', team_id: 'team_smk_core', title: 'Запросить результаты выполнения показателей', status: 'done', priority: 'medium', source: 'meeting_audio', deadline: '2026-04-12T15:00:00Z', assignee: 'Иванова Ольга', created_by_ai: true, confidence: 0.82 },
];

export const userDigest: UserDigest = {
  user_id: 'usr_olga', date: '2026-06-10',
  tasks_today: [profileTasks[0]],
  overdue_tasks: [profileTasks[1]],
  upcoming_deadlines: [profileTasks[0]],
};

export const notes: Note[] = [
  { id: 'note_01', user_id: 'usr_olga', title: 'Итоги планёрки по СМК', content: 'Запустить анализ со стороны руководства, разослать форму запроса владельцам процессов до 17 апреля.', source: 'meeting', meeting_id: 'm1', created_at: '2026-04-13T11:00:00Z' },
  { id: 'note_02', user_id: 'usr_olga', title: 'Карта процессов', content: 'В мае вынести показатели процессов из руководства в карту процессов по каждому юрлицу.', source: 'manual', created_at: '2026-04-13T12:00:00Z' },
];

export const achievements: Achievement[] = [
  { id: 'ach_01', code: 'audit_master', title: 'Аудитор года', description: 'Завершено 10+ аудитов без повторных несоответствий.', icon: '🏆', unlocked_at: '2026-05-20T10:00:00Z' },
  { id: 'ach_02', code: 'ai_adopter', title: 'AI-первопроходец', description: 'Подтверждено 50 задач, выделенных AI.', icon: '🤖', unlocked_at: '2026-06-01T10:00:00Z' },
];

export const recommendations: Recommendation[] = [
  { id: 'rec_01', title: 'Курс: Внутренний аудит ISO 9001:2015', description: 'Углубить компетенции по программе и чек-листам аудита.', recommendation_type: 'course', source: 'AI-анализ задач' },
  { id: 'rec_02', title: 'Практика: матрица рисков процессов', description: 'Повторяющиеся задачи по рискам — стоит формализовать матрицу.', recommendation_type: 'practice', source: 'AI-анализ задач' },
];

// ─── Командная аналитика и лидерборд (legacy) ────────────────────────────────────
export const teamAnalytics: TeamAnalytics = {
  ai_created_tasks: 11, auto_confirmed: 7, waiting_confirmation: 2, rejected_suggestions: 1, voice_messages_processed: 14, meetings_summarized: 4, average_confidence: 0.86, overdue_tasks: 2, done_tasks: 3,
  team_velocity: { done_this_week: 8, avg_lead_time_hours: 18, overdue_percent: 12 },
  ai_quality: { average_confidence: 0.86, auto_created: 7, rejected_suggestions: 1 },
};

export const leaderboard: LeaderboardItem[] = [
  { user_id: 'usr_olga', name: 'Иванова Ольга', xp: 1840, level: 'Эксперт СМК', done_tasks: 12 },
  { user_id: 'usr_dasha_k', name: 'Кудинова Дарья', xp: 1320, level: 'Аудитор', done_tasks: 9 },
  { user_id: 'usr_nastya', name: 'Петрова Анастасия', xp: 980, level: 'Специалист', done_tasks: 7 },
];

// ─── База знаний и summary встречи (legacy) ──────────────────────────────────────
export const knowledge: KnowledgeItem[] = [
  { id: 'kn_01', title: 'Планёрка по СМК — итоги недели', content: 'Решения: запустить анализ со стороны руководства. Действия: разослать форму запроса до 17 апреля.', source_type: 'meeting', source_id: 'm1', tags: ['СМК', 'планёрка'], created_at: '2026-04-13T11:00:00Z' },
  { id: 'kn_02', title: 'Чек-листы внутреннего аудита', content: 'Состав команды аудиторов определён, чек-листы — до 15 апреля, программа — до 17 апреля.', source_type: 'meeting', source_id: 'm3', tags: ['аудит'], created_at: '2026-04-15T12:00:00Z' },
];

export const meetingSummary: MeetingSummary = {
  id: 'm1', title: 'Планёрка по СМК: план на неделю', date: '2026-04-13',
  summary: 'Команда СМК синхронизировала план на неделю: аудит 1 стороны (чек-листы и программа), анализ со стороны руководства, доработка целей и рисков.',
  decisions: ['Запустить анализ со стороны руководства', 'Чек-листы аудита — до 15 апреля', 'Программа аудита — до 17 апреля'],
  action_items: [
    { title: 'Сформировать чек-листы для внутреннего аудита МП Югра', assignee: 'Кудинова Дарья', deadline: '2026-04-15' },
    { title: 'Подготовить отчёт и ПКМ по аудиту 1 стороны', assignee: 'Гочнева Татьяна', deadline: '2026-04-17' },
  ],
  risks: ['Сжатые сроки аудита (27–30 апреля)', 'Возможны повторные несоответствия по ПКМ'],
  open_questions: ['Нужна ли удалённая помощь по чек-листам?'],
  transcript_quality: 0.95,
};

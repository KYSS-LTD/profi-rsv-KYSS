// МОК-РОУТЕР: сопоставляет (метод, путь) с демо-данными из ./data.ts.
// Подключается единственной точкой в src/shared/api/client.ts.
// GET — читает данные, POST/PATCH/DELETE — мутируют коллекции в памяти,
// чтобы демо ощущалось «живым» в рамках сессии (без персистентности).

import { getAccessToken, setAccessToken } from '../../auth/token';
import { KomandusTask, TaskStatusV2 } from '../../../entities/saas/types';
import { MOCKS_ENABLED } from './enabled';
import * as db from './data';

export const DEMO_TOKEN = 'mock-demo-token';

/** Сеет демо-токен, чтобы пользователь сразу был «залогинен» как Иванова Ольга. */
export function bootstrapMocks() {
  if (!MOCKS_ENABLED) return;
  if (!getAccessToken()) setAccessToken(DEMO_TOKEN);
}

type MockResult = { matched: boolean; data?: unknown };

let seq = 1000;
const nextId = (prefix: string) => `${prefix}_${++seq}`;
const tokenResponse = { access_token: DEMO_TOKEN, token_type: 'bearer', must_change_password: false };

function parseBody(body: BodyInit | null | undefined): Record<string, any> {
  if (typeof body === 'string') {
    try {
      return JSON.parse(body);
    } catch {
      return {};
    }
  }
  return {};
}

function find<T extends { id: string }>(list: T[], id: string) {
  return list.find((item) => item.id === id);
}

type Route = {
  method: string;
  pattern: RegExp;
  handler: (params: string[], body: Record<string, any>, query: URLSearchParams) => unknown;
};

const routes: Route[] = [
  // ── Auth / setup ──────────────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/auth\/me$/, handler: () => db.currentUser },
  { method: 'GET', pattern: /^\/v2\/setup\/status$/, handler: () => ({ initialized: true }) },
  { method: 'POST', pattern: /^\/v2\/auth\/login$/, handler: () => tokenResponse },
  { method: 'POST', pattern: /^\/v2\/setup$/, handler: () => tokenResponse },
  { method: 'POST', pattern: /^\/v2\/auth\/magic-login$/, handler: () => tokenResponse },
  { method: 'POST', pattern: /^\/v2\/auth\/impersonate$/, handler: () => tokenResponse },
  { method: 'POST', pattern: /^\/v2\/auth\/refresh$/, handler: () => tokenResponse },
  { method: 'POST', pattern: /^\/v2\/auth\/logout$/, handler: () => ({ status: 'ok' }) },
  { method: 'POST', pattern: /^\/v2\/auth\/change-password$/, handler: () => ({ status: 'ok' }) },

  // ── Аналитика ───────────────────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/analytics\/dashboard$/, handler: () => db.dashboard },
  { method: 'GET', pattern: /^\/v2\/analytics\/employee\/([^/]+)$/, handler: () => ({ active_tasks: 4, completed_tasks: 8, overdue_tasks: 1, average_completion_time: 16, ai_accuracy: 95 }) },
  { method: 'POST', pattern: /^\/v2\/analytics\/assistant$/, handler: (_p, body) => ({ answer: `По данным Командуса: ${String(body.question ?? 'запрос').trim()} — в работе 2 задачи, просрочено 2, AI-точность 95%.`, facts: ['Всего задач: 12', 'Завершено: 3', 'Ждут подтверждения: 2'] }) },

  // ── Карта организации ─────────────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/org-os\/map$/, handler: () => db.orgMap },

  // ── Задачи Командуса ──────────────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/tasks$/, handler: () => db.tasks },
  { method: 'POST', pattern: /^\/v2\/tasks$/, handler: (_p, body) => {
      const now = new Date().toISOString();
      const task: KomandusTask = {
        id: nextId('tsk'), organization_id: db.ORG_ID, employee_id: body.employee_id ?? null, department_id: body.department_id ?? null, team_id: body.team_id ?? null,
        organization_chat_id: null, title: body.title ?? 'Новая задача', description: body.description ?? null, status: 'TO_DO', due_at: body.due_at ?? null,
        llm_model: null, ai_summary: null, source_excerpt: null, created_at: now, updated_at: now,
      };
      db.tasks.push(task);
      return task;
    } },
  { method: 'PATCH', pattern: /^\/v2\/tasks\/([^/]+)\/status$/, handler: ([id], body) => {
      const task = find(db.tasks, id);
      if (task) { task.status = body.status as TaskStatusV2; task.updated_at = new Date().toISOString(); if (task.status === 'DONE') task.completed_at = task.updated_at; }
      return task ?? {};
    } },
  { method: 'POST', pattern: /^\/v2\/tasks\/([^/]+)\/confirm$/, handler: ([id], body) => {
      const task = find(db.tasks, id);
      if (task) { task.status = body.approved ? 'ACCEPTED' : 'REJECTED'; task.updated_at = new Date().toISOString(); if (!body.approved) task.rejected_at = task.updated_at; else task.accepted_at = task.updated_at; }
      return task ?? {};
    } },
  { method: 'PATCH', pattern: /^\/v2\/tasks\/([^/]+)$/, handler: ([id], body) => {
      const task = find(db.tasks, id);
      if (task) {
        if (body.title !== undefined) task.title = body.title;
        if (body.description !== undefined) task.description = body.description;
        if (body.employee_id !== undefined) task.employee_id = body.employee_id;
        if (body.due_at !== undefined) task.due_at = body.due_at;
        task.updated_at = new Date().toISOString();
      }
      return task ?? {};
    } },

  // ── Сотрудники ────────────────────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/employees$/, handler: () => db.employees },
  { method: 'POST', pattern: /^\/v2\/employees$/, handler: (_p, body) => {
      const employee = {
        id: nextId('emp'), organization_id: db.ORG_ID, user_id: nextId('usr'), manager_id: null,
        full_name: body.full_name ?? 'Новый сотрудник', email: body.email ?? null, role: body.role ?? 'EMPLOYEE',
        department_id: body.department_id ?? null, team_id: body.team_id ?? null, position: body.position ?? null,
        telegram_username: body.telegram_username ?? null, telegram_status: 'PENDING' as const, is_active: true,
        generated_password: 'demo-' + (seq), invitation_text: 'Перейдите по ссылке и напишите боту /start.',
      };
      db.employees.push(employee);
      return employee;
    } },
  { method: 'PATCH', pattern: /^\/v2\/employees\/([^/]+)$/, handler: ([id], body) => {
      const employee = find(db.employees, id);
      if (employee) Object.assign(employee, body);
      return employee ?? {};
    } },
  { method: 'POST', pattern: /^\/v2\/employees\/([^/]+)\/deactivate$/, handler: ([id]) => { const e = find(db.employees, id); if (e) { e.is_active = false; e.deactivated_at = new Date().toISOString(); } return e ?? {}; } },
  { method: 'POST', pattern: /^\/v2\/employees\/([^/]+)\/activate$/, handler: ([id]) => { const e = find(db.employees, id); if (e) { e.is_active = true; e.deactivated_at = null; } return e ?? {}; } },
  { method: 'POST', pattern: /^\/v2\/employees\/([^/]+)\/restore$/, handler: ([id]) => { const e = find(db.employees, id); if (e) { e.is_active = true; e.deactivated_at = null; } return e ?? {}; } },
  { method: 'DELETE', pattern: /^\/v2\/employees\/([^/]+)$/, handler: ([id]) => { const i = db.employees.findIndex((e) => e.id === id); if (i >= 0) db.employees.splice(i, 1); return { status: 'ok' }; } },

  // ── Оргструктура / интеграции ───────────────────────────────────────────────────
  { method: 'GET', pattern: /^\/v2\/org\/departments$/, handler: () => db.departments },
  { method: 'POST', pattern: /^\/v2\/org\/departments$/, handler: (_p, body) => {
      const now = new Date().toISOString();
      const dep = { id: nextId('dep'), organization_id: db.ORG_ID, name: body.name ?? 'Новый отдел', description: body.description ?? null, employee_count: 0, task_count: 0, overdue_count: 0, efficiency: 100, created_at: now, updated_at: now };
      db.departments.push(dep);
      return dep;
    } },
  { method: 'GET', pattern: /^\/v2\/org\/teams$/, handler: (_p, _b, query) => {
      const depId = query.get('department_id');
      return depId ? db.teams.filter((t) => t.department_id === depId) : db.teams;
    } },
  { method: 'POST', pattern: /^\/v2\/org\/teams$/, handler: (_p, body) => {
      const now = new Date().toISOString();
      const team = { id: nextId('team'), organization_id: db.ORG_ID, department_id: body.department_id, name: body.name ?? 'Новая команда', description: body.description ?? null, created_at: now, updated_at: now };
      db.teams.push(team);
      return team;
    } },
  { method: 'GET', pattern: /^\/v2\/org\/chats$/, handler: () => db.chats },
  { method: 'PATCH', pattern: /^\/v2\/org\/chats\/([^/]+)$/, handler: ([id], body) => {
      const chat = find(db.chats, id);
      if (chat) { if (body.ai_enabled !== undefined) chat.ai_enabled = body.ai_enabled; if (body.department_id !== undefined) chat.department_id = body.department_id; }
      return chat ?? {};
    } },
  { method: 'POST', pattern: /^\/v2\/org\/telegram\/connect-code$/, handler: () => ({ code: 'KMD-' + nextId('c').toUpperCase(), command: '/connect KMD-DEMO', expires_at: null, instruction: ['Добавьте бота @KomandusBot в чат', 'Отправьте команду /connect с кодом', 'Назначьте бота администратором'] }) },
  { method: 'GET', pattern: /^\/v2\/org\/mode$/, handler: () => db.orgMode },
  { method: 'GET', pattern: /^\/v2\/org\/task-sources$/, handler: () => db.taskSources },
  { method: 'POST', pattern: /^\/v2\/org\/hierarchy-wizard\/start$/, handler: () => db.hierarchyWizard },
  { method: 'PATCH', pattern: /^\/v2\/org\/hierarchy-wizard$/, handler: (_p, body) => ({ ...db.hierarchyWizard, hierarchy_setup_state: { ...db.hierarchyWizard.hierarchy_setup_state, ...body } }) },
  { method: 'POST', pattern: /^\/v2\/org\/hierarchy-wizard\/confirm$/, handler: () => db.hierarchyWizard },

  // ── Доски (YouGile) ───────────────────────────────────────────────────────────
  { method: 'POST', pattern: /^\/v2\/boards\/yougile\/verify$/, handler: () => db.boardIntegration },
  { method: 'POST', pattern: /^\/v2\/boards\/([^/]+)\/columns$/, handler: () => ({ status: 'ok' }) },
  { method: 'POST', pattern: /^\/v2\/boards\/([^/]+)\/employees$/, handler: () => ({ status: 'ok' }) },

  // ── Legacy: кандидаты, профиль, заметки, аналитика, знания, встречи ─────────────
  { method: 'GET', pattern: /^\/task-candidates$/, handler: () => db.candidates.filter((c) => c.status === 'pending') },
  { method: 'POST', pattern: /^\/task-candidates\/([^/]+)\/confirm$/, handler: ([id]) => { const c = find(db.candidates, id); if (c) c.status = 'created'; return { task_id: nextId('tsk'), status: 'created' }; } },
  { method: 'POST', pattern: /^\/task-candidates\/([^/]+)\/reject$/, handler: ([id]) => { const c = find(db.candidates, id); if (c) c.status = 'rejected'; return { status: 'rejected' }; } },
  { method: 'GET', pattern: /^\/profile\/me$/, handler: () => db.profile },
  { method: 'GET', pattern: /^\/profile\/me\/tasks$/, handler: () => db.profileTasks },
  { method: 'GET', pattern: /^\/users\/([^/]+)\/digest$/, handler: () => db.userDigest },
  { method: 'GET', pattern: /^\/users\/([^/]+)\/achievements$/, handler: () => db.achievements },
  { method: 'GET', pattern: /^\/users\/([^/]+)\/recommendations$/, handler: () => db.recommendations },
  { method: 'GET', pattern: /^\/notes\/my$/, handler: () => db.notes },
  { method: 'POST', pattern: /^\/notes$/, handler: (_p, body) => { const note = { id: nextId('note'), user_id: 'usr_olga', title: body.title ?? '', content: body.content ?? '', source: body.source ?? 'manual', created_at: new Date().toISOString() }; db.notes.unshift(note); return note; } },
  { method: 'PATCH', pattern: /^\/notes\/([^/]+)$/, handler: ([id], body) => { const n = find(db.notes, id); if (n) Object.assign(n, body); return n ?? {}; } },
  { method: 'DELETE', pattern: /^\/notes\/([^/]+)$/, handler: ([id]) => { const i = db.notes.findIndex((n) => n.id === id); if (i >= 0) db.notes.splice(i, 1); return { status: 'ok', note_id: id }; } },
  { method: 'GET', pattern: /^\/analytics\/team$/, handler: () => db.teamAnalytics },
  { method: 'GET', pattern: /^\/analytics\/leaderboard$/, handler: () => db.leaderboard },
  { method: 'GET', pattern: /^\/knowledge$/, handler: () => db.knowledge },
  { method: 'GET', pattern: /^\/meetings\/([^/]+)\/summary$/, handler: () => db.meetingSummary },
  { method: 'POST', pattern: /^\/meetings\/upload$/, handler: () => ({ meeting_id: nextId('m'), status: 'summarized' }) },
  { method: 'GET', pattern: /^\/tasks$/, handler: () => db.profileTasks },
  { method: 'GET', pattern: /^\/tasks\/my$/, handler: () => db.profileTasks },
];

const delay = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

export async function resolveMock(method: string, rawPath: string, body: BodyInit | null | undefined): Promise<MockResult> {
  if (!MOCKS_ENABLED) return { matched: false };

  const [pathOnly, queryString = ''] = rawPath.split('?');
  const query = new URLSearchParams(queryString);

  for (const route of routes) {
    if (route.method !== method) continue;
    const match = pathOnly.match(route.pattern);
    if (!match) continue;
    const data = route.handler(match.slice(1), parseBody(body), query);
    await delay(method === 'GET' ? 220 : 140);
    return { matched: true, data };
  }

  // Неизвестный путь — отдаём отладочную подсказку, но не валим UI.
  if (import.meta.env.DEV) console.warn(`[mocks] нет обработчика для ${method} ${pathOnly}`);
  return { matched: false };
}

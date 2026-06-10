import { Department, OrganizationChat, Team } from '../../entities/saas/types';
import { apiClient } from './client';

export type DepartmentPayload = { name: string; description?: string | null };
export type TeamPayload = { department_id: string; name: string; description?: string | null };

export function getDepartments() {
  return apiClient<Department[]>('/v2/org/departments');
}

export function createDepartment(payload: DepartmentPayload) {
  return apiClient<Department>('/v2/org/departments', { method: 'POST', body: JSON.stringify(payload) });
}

export function getTeams(departmentId?: string) {
  return apiClient<Team[]>(`/v2/org/teams${departmentId ? `?department_id=${departmentId}` : ''}`);
}

export function createTeam(payload: TeamPayload) {
  return apiClient<Team>('/v2/org/teams', { method: 'POST', body: JSON.stringify(payload) });
}

export function getOrganizationChats() {
  return apiClient<OrganizationChat[]>('/v2/org/chats');
}

export function createTelegramConnectCode(department_id?: string | null, team_id?: string | null) {
  return apiClient<{ code: string; command: string; expires_at?: string | null; instruction: string[] }>('/v2/org/telegram/connect-code', { method: 'POST', body: JSON.stringify({ department_id, team_id }) });
}

export function updateOrganizationChat(id: string, payload: { ai_enabled: boolean; department_id?: string | null }) {
  return apiClient<OrganizationChat>(`/v2/org/chats/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}


export type TaskSource = {
  id: string;
  organization_id: string;
  source_type: 'TELEGRAM_CHAT' | 'TELEGRAM_TOPIC' | string;
  telegram_chat_id: number;
  telegram_topic_id?: number | null;
  title: string;
  department_id?: string | null;
  team_id?: string | null;
  is_active: boolean;
  ai_enabled: boolean;
  created_at: string;
  updated_at: string;
};

export type OrganizationModeResponse = { mode: 'SIMPLE' | 'HIERARCHY' | string; hierarchy_setup_state?: Record<string, unknown> | null };
export type HierarchyWizardResponse = { mode: string; hierarchy_setup_state: { step: number; departments_ready: boolean; teams_ready: boolean; managers_ready: boolean; employees_distributed: boolean; telegram_sources_ready: boolean }; can_confirm: boolean; checklist: string[] };

export function getOrganizationMode() {
  return apiClient<OrganizationModeResponse>('/v2/org/mode');
}

export function startHierarchyWizard() {
  return apiClient<HierarchyWizardResponse>('/v2/org/hierarchy-wizard/start', { method: 'POST' });
}

export function updateHierarchyWizard(payload: Partial<HierarchyWizardResponse['hierarchy_setup_state']>) {
  return apiClient<HierarchyWizardResponse>('/v2/org/hierarchy-wizard', { method: 'PATCH', body: JSON.stringify(payload) });
}

export function confirmHierarchyMode() {
  return apiClient<HierarchyWizardResponse>('/v2/org/hierarchy-wizard/confirm', { method: 'POST' });
}

export function getTaskSources() {
  return apiClient<TaskSource[]>('/v2/org/task-sources');
}

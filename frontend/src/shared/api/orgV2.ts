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

export function createTelegramConnectCode(department_id?: string | null) {
  return apiClient<{ code: string; command: string; expires_at?: string | null; instruction: string[] }>('/v2/org/telegram/connect-code', { method: 'POST', body: JSON.stringify({ department_id }) });
}

export function updateOrganizationChat(id: string, payload: { ai_enabled: boolean; department_id?: string | null }) {
  return apiClient<OrganizationChat>(`/v2/org/chats/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

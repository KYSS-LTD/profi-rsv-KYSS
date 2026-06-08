import { KomandusTask, TaskStatusV2 } from '../../entities/saas/types';
import { apiClient } from './client';

export type CreateTaskV2Payload = {
  title: string;
  description?: string | null;
  employee_id?: string | null;
  department_id?: string | null;
  team_id?: string | null;
  due_at?: string | null;
};

export function getKomandusTasks() {
  return apiClient<KomandusTask[]>('/v2/tasks');
}

export function createKomandusTask(payload: CreateTaskV2Payload) {
  return apiClient<KomandusTask>('/v2/tasks', { method: 'POST', body: JSON.stringify(payload) });
}

export function moveKomandusTask(id: string, status: TaskStatusV2) {
  return apiClient<KomandusTask>(`/v2/tasks/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
}

export type UpdateTaskV2Payload = {
  title?: string;
  description?: string | null;
  employee_id?: string | null;
  due_at?: string | null;
};

export function updateKomandusTask(id: string, payload: UpdateTaskV2Payload) {
  return apiClient<KomandusTask>(`/v2/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function confirmKomandusTask(id: string, approved: boolean, reason?: string) {
  return apiClient<KomandusTask>(`/v2/tasks/${id}/confirm`, { method: 'POST', body: JSON.stringify({ approved, reason }) });
}

export function askAIAssistant(question: string) {
  return apiClient<{ answer: string; facts: string[] }>('/v2/analytics/assistant', { method: 'POST', body: JSON.stringify({ question }) });
}

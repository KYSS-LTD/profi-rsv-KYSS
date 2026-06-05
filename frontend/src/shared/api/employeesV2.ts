import { Employee, Role } from '../../entities/saas/types';
import { apiClient } from './client';

export type EmployeePayload = {
  full_name: string;
  email?: string | null;
  role: Role;
  department_id?: string | null;
  team_id?: string | null;
  position?: string | null;
  telegram_username?: string | null;
};

export function getEmployees() {
  return apiClient<Employee[]>('/v2/employees');
}

export function createEmployee(payload: EmployeePayload) {
  return apiClient<Employee>('/v2/employees', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateEmployee(id: string, payload: Partial<EmployeePayload> & { is_active?: boolean }) {
  return apiClient<Employee>(`/v2/employees/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
}

export function deactivateEmployee(id: string) {
  return apiClient<Employee>(`/v2/employees/${id}/deactivate`, { method: 'POST' });
}

export function deleteEmployee(id: string) {
  return apiClient<{ status: string }>(`/v2/employees/${id}`, { method: 'DELETE' });
}

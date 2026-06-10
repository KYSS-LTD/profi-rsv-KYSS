import { DashboardAnalytics } from '../../entities/saas/types';
import { apiClient } from './client';

export function getDashboardAnalytics() {
  return apiClient<DashboardAnalytics>('/v2/analytics/dashboard');
}

export function getEmployeeAnalytics(employeeId: string) {
  return apiClient(`/v2/analytics/employee/${employeeId}`);
}

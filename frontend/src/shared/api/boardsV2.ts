import { BoardIntegration } from '../../entities/saas/types';
import { apiClient } from './client';

export function verifyYouGile(apiToken: string) {
  return apiClient<BoardIntegration>('/v2/boards/yougile/verify', {
    method: 'POST',
    body: JSON.stringify({ api_token: apiToken }),
  });
}

export function mapColumn(integrationId: string, payload: { task_status: string; external_column_id: string; external_column_name?: string }) {
  return apiClient(`/v2/boards/${integrationId}/columns`, { method: 'POST', body: JSON.stringify(payload) });
}

export function mapEmployee(integrationId: string, payload: { employee_id: string; external_user_id: string; external_email?: string }) {
  return apiClient(`/v2/boards/${integrationId}/employees`, { method: 'POST', body: JSON.stringify(payload) });
}

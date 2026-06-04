import { ConfirmCandidatePayload, RejectCandidatePayload, TaskCandidate } from '../../entities/candidate/types';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export async function getTaskCandidates() {
  const response = await apiClient<ApiListResponse<TaskCandidate>>('/task-candidates', {
    params: { status: 'pending' },
  });
  return unwrapItems(response);
}

export async function confirmCandidate(candidateId: string, payload: ConfirmCandidatePayload) {
  return apiClient<{
    task_id: string | null;
    external_kanban_id?: string | null;
    external_kanban_url?: string | null;
    status: string;
  }>(`/task-candidates/${candidateId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function rejectCandidate(candidateId: string, payload: RejectCandidatePayload) {
  return apiClient<{ status: string }>(`/task-candidates/${candidateId}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

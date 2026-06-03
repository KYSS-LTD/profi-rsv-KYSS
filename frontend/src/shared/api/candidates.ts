import { ConfirmCandidatePayload, RejectCandidatePayload, TaskCandidate } from '../../entities/candidate/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';
import { mockCandidates } from './mock';

export async function getTaskCandidates() {
  if (env.useMocks) return mockCandidates;

  const response = await apiClient<ApiListResponse<TaskCandidate>>('/task-candidates', {
    params: { status: 'pending' },
  });
  return unwrapItems(response);
}

export async function confirmCandidate(candidateId: string, payload: ConfirmCandidatePayload) {
  if (env.useMocks) {
    return {
      task_id: `task_from_${candidateId}`,
      external_kanban_id: `card_${candidateId}`,
      external_kanban_url: `https://kanban.example/card/${candidateId}`,
      status: 'created',
    };
  }

  return apiClient<{
    task_id: string;
    external_kanban_id?: string;
    external_kanban_url?: string;
    status: string;
  }>(`/tasks/candidates/${candidateId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function rejectCandidate(candidateId: string, payload: RejectCandidatePayload) {
  if (env.useMocks) return { status: 'rejected' };

  return apiClient<{ status: string }>(`/tasks/candidates/${candidateId}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

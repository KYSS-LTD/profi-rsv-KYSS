import { Task, TasksQueryParams, UpdateTaskStatusPayload, RescheduleTaskPayload } from '../../entities/task/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export async function getTasks(params: TasksQueryParams = {}) {
  const response = await apiClient<ApiListResponse<Task>>('/tasks', { params });
  return unwrapItems(response);
}

export async function getMyTasks(userId = env.defaultUserId) {
  const response = await apiClient<ApiListResponse<Task>>('/tasks/my', { params: { user_id: userId } });
  return unwrapItems(response);
}

export async function updateTaskStatus(taskId: string, payload: UpdateTaskStatusPayload) {
  return apiClient<{
    task_id: string;
    old_status: string;
    new_status: string;
    external_synced: boolean;
    updated_at: string;
  }>(`/tasks/${taskId}/status`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function rescheduleTask(taskId: string, payload: RescheduleTaskPayload) {
  return apiClient<{ task_id: string; deadline: string; reminders_rebuilt: boolean }>(
    `/tasks/${taskId}/reschedule`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

import { Task, TasksQueryParams, UpdateTaskStatusPayload, RescheduleTaskPayload } from '../../entities/task/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';
import { mockTasks } from './mock';

export async function getTasks(params: TasksQueryParams = {}) {
  if (env.useMocks) return mockTasks;

  const response = await apiClient<ApiListResponse<Task>>('/tasks', { params });
  return unwrapItems(response);
}

export async function getMyTasks() {
  if (env.useMocks) return mockTasks.filter((task) => task.assignee === 'Иван');

  const response = await apiClient<ApiListResponse<Task>>('/tasks/my');
  return unwrapItems(response);
}

export async function updateTaskStatus(taskId: string, payload: UpdateTaskStatusPayload) {
  if (env.useMocks) {
    return {
      task_id: taskId,
      old_status: 'todo',
      new_status: payload.status,
      external_synced: true,
      updated_at: new Date().toISOString(),
    };
  }

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
  if (env.useMocks) {
    return { task_id: taskId, deadline: payload.new_deadline, reminders_rebuilt: true };
  }

  return apiClient<{ task_id: string; deadline: string; reminders_rebuilt: boolean }>(
    `/tasks/${taskId}/reschedule`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
}

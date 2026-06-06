import { mockAnalytics, mockCandidates, mockLeaderboard, mockMeetingSummary, mockProfile, mockTasks } from '@/entities/mockData';
import type { Analytics, LeaderboardUser, MeetingSummary, Profile, Task, TaskCandidate, TaskStatus } from '@/entities/types';
import { env } from '@/shared/config/env';
import { getTelegramInitData } from '@/shared/lib/telegram';

const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));

let tasksStore = [...mockTasks];
let candidatesStore = [...mockCandidates];

class ApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

const normalizeBaseUrl = (value: string) => value.replace(/\/$/, '');

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const initData = getTelegramInitData();
  const headers = new Headers(options.headers);

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (initData) {
    headers.set(env.telegramAuthHeader, initData);
  }

  const response = await fetch(`${normalizeBaseUrl(env.apiBaseUrl)}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new ApiError(text || `Request failed with status ${response.status}`, response.status);
  }

  if (response.status === 204) return undefined as T;

  const data = await response.json();
  return (Array.isArray(data) ? data : data.items ?? data) as T;
}

const mapAnalytics = (data: Partial<Analytics> & Record<string, unknown>): Analytics => {
  const velocity = (data.team_velocity ?? {}) as Record<string, number>;
  const quality = (data.ai_quality ?? {}) as Record<string, number>;

  return {
    aiCreatedTasks: Number(data.aiCreatedTasks ?? data.ai_created_tasks ?? quality.auto_created ?? 0),
    autoConfirmed: Number(data.autoConfirmed ?? data.auto_confirmed ?? 0),
    waitingConfirmation: Number(data.waitingConfirmation ?? data.waiting_confirmation ?? 0),
    rejectedSuggestions: Number(data.rejectedSuggestions ?? data.rejected_suggestions ?? quality.rejected_suggestions ?? 0),
    voiceMessagesProcessed: Number(data.voiceMessagesProcessed ?? data.voice_messages_processed ?? 0),
    meetingsSummarized: Number(data.meetingsSummarized ?? data.meetings_summarized ?? 0),
    averageConfidence: Number(data.averageConfidence ?? data.average_confidence ?? quality.average_confidence ?? 0),
    doneThisWeek: Number(data.doneThisWeek ?? velocity.done_this_week ?? 0),
    overduePercent: Number(data.overduePercent ?? velocity.overdue_percent ?? 0),
    teamVelocity: Number(data.teamVelocity ?? velocity.avg_lead_time_hours ?? velocity.done_this_week ?? 0),
    aiQuality: Number(data.aiQuality ?? Math.round(Number(quality.average_confidence ?? data.average_confidence ?? 0) * 100)),
  };
};

export const api = {
  async getTasks(): Promise<Task[]> {
    if (env.useMocks) {
      await delay();
      return [...tasksStore];
    }
    return request<Task[]>('/tasks');
  },

  async updateTaskStatus(taskId: string, status: TaskStatus): Promise<Task> {
    if (env.useMocks) {
      await delay(160);
      tasksStore = tasksStore.map((task) => (task.id === taskId ? { ...task, status } : task));
      return tasksStore.find((task) => task.id === taskId)!;
    }
    return request<Task>(`/tasks/${taskId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  },

  async rescheduleTask(taskId: string, deadline: string): Promise<Task> {
    if (env.useMocks) {
      await delay(160);
      tasksStore = tasksStore.map((task) => (task.id === taskId ? { ...task, deadline } : task));
      return tasksStore.find((task) => task.id === taskId)!;
    }
    return request<Task>(`/tasks/${taskId}/reschedule`, {
      method: 'POST',
      body: JSON.stringify({ deadline }),
    });
  },

  async getCandidates(): Promise<TaskCandidate[]> {
    if (env.useMocks) {
      await delay();
      return candidatesStore.filter((candidate) => candidate.status === 'pending');
    }
    return request<TaskCandidate[]>('/task-candidates');
  },

  async confirmCandidate(candidateId: string): Promise<void> {
    if (env.useMocks) {
      await delay(180);
      const candidate = candidatesStore.find((item) => item.id === candidateId);
      candidatesStore = candidatesStore.map((item) => (item.id === candidateId ? { ...item, status: 'confirmed' } : item));
      if (candidate) {
        tasksStore = [
          {
            id: `task-${Date.now()}`,
            title: candidate.title,
            assignee: candidate.suggestedAssignee || 'Команда',
            deadline: candidate.suggestedDeadline || new Date().toISOString().slice(0, 10),
            priority: 'medium',
            source: candidate.source === 'voice' ? 'telegram' : candidate.source,
            confidence: candidate.confidence,
            status: 'todo',
            createdByAi: true,
            sourceExcerpt: candidate.excerpt,
            kanbanProvider: 'Командус Board',
          },
          ...tasksStore,
        ];
      }
      return;
    }
    await request<void>(`/tasks/candidates/${candidateId}/confirm`, { method: 'POST' });
  },

  async rejectCandidate(candidateId: string): Promise<void> {
    if (env.useMocks) {
      await delay(180);
      candidatesStore = candidatesStore.map((item) => (item.id === candidateId ? { ...item, status: 'rejected' } : item));
      return;
    }
    await request<void>(`/tasks/candidates/${candidateId}/reject`, { method: 'POST' });
  },

  async uploadMeeting(file: File): Promise<{ id: string }> {
    if (env.useMocks) {
      await delay(600);
      return { id: `meeting-${file.name.replace(/\W+/g, '-').toLowerCase() || 'demo'}` };
    }
    const form = new FormData();
    form.append('file', file);
    return request<{ id: string }>('/meetings/upload', {
      method: 'POST',
      body: form,
    });
  },

  async getMeetingSummary(id = 'meeting-demo'): Promise<MeetingSummary> {
    if (env.useMocks) {
      await delay();
      return { ...mockMeetingSummary, id };
    }
    return request<MeetingSummary>(`/meetings/${id}/summary`);
  },

  async getAnalytics(): Promise<Analytics> {
    if (env.useMocks) {
      await delay();
      return mockAnalytics;
    }
    const data = await request<Record<string, unknown>>('/analytics/team');
    return mapAnalytics(data);
  },

  async getLeaderboard(): Promise<LeaderboardUser[]> {
    if (env.useMocks) {
      await delay();
      return mockLeaderboard;
    }
    return request<LeaderboardUser[]>('/analytics/leaderboard');
  },

  async getProfile(): Promise<Profile> {
    if (env.useMocks) {
      await delay();
      return mockProfile;
    }
    return request<Profile>('/profile/me');
  },
};

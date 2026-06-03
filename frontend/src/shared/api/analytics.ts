import { LeaderboardItem, TeamAnalytics } from '../../entities/analytics/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';
import { mockAnalytics } from './mock';

export async function getTeamAnalytics() {
  if (env.useMocks) return mockAnalytics;

  return apiClient<TeamAnalytics>('/analytics/team');
}

export async function getLeaderboard() {
  if (env.useMocks) {
    return [
      { user_id: 'user_ivan', name: 'Иван', xp: 420, level: 'Team Driver', done_tasks: 5 },
      { user_id: 'user_pavel', name: 'Павел', xp: 360, level: 'Reliable Executor', done_tasks: 4 },
      { user_id: 'user_daniil', name: 'Даниил', xp: 330, level: 'Contributor', done_tasks: 3 },
    ] satisfies LeaderboardItem[];
  }

  const response = await apiClient<ApiListResponse<LeaderboardItem>>('/analytics/leaderboard');
  return unwrapItems(response);
}

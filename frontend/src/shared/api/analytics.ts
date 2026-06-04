import { LeaderboardItem, TeamAnalytics } from '../../entities/analytics/types';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export async function getTeamAnalytics() {
  return apiClient<TeamAnalytics>('/analytics/team');
}

export async function getLeaderboard() {
  const response = await apiClient<ApiListResponse<LeaderboardItem>>('/analytics/leaderboard');
  return unwrapItems(response);
}

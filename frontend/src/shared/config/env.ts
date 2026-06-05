export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '/api',
  defaultTeamId: import.meta.env.VITE_DEFAULT_TEAM_ID ?? 'team_1',
  defaultUserId: import.meta.env.VITE_DEFAULT_USER_ID ?? 'user_ivan',
  defaultMeetingId: import.meta.env.VITE_DEFAULT_MEETING_ID ?? 'meeting_1',
};

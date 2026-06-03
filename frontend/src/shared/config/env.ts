export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  defaultTeamId: import.meta.env.VITE_DEFAULT_TEAM_ID ?? 'team_1',
  defaultUserId: import.meta.env.VITE_DEFAULT_USER_ID ?? 'user_ivan',
  defaultMeetingId: import.meta.env.VITE_DEFAULT_MEETING_ID ?? 'meeting_1',
  useMocks: import.meta.env.VITE_USE_MOCKS === 'true',
};

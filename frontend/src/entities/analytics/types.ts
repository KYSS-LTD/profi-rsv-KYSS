export type TeamVelocity = {
  done_this_week?: number;
  avg_lead_time_hours?: number;
  overdue_percent?: number;
};

export type AiQuality = {
  average_confidence?: number;
  auto_created?: number;
  rejected_suggestions?: number;
};

export type TeamAnalytics = {
  ai_created_tasks?: number;
  auto_confirmed?: number;
  waiting_confirmation?: number;
  rejected_suggestions?: number;
  voice_messages_processed?: number;
  meetings_summarized?: number;
  average_confidence?: number;
  overdue_tasks?: number;
  done_tasks?: number;
  team_velocity?: TeamVelocity;
  ai_quality?: AiQuality;
};

export type LeaderboardItem = {
  user_id: string;
  name: string;
  xp: number;
  level: string;
  done_tasks?: number;
};

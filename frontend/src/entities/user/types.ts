import { Task } from '../task/types';

export type UserProfile = {
  id: string;
  name: string;
  telegram_username?: string | null;
  role?: string | null;
  team?: string | null;
  timezone?: string | null;
  notification_preferences?: string[];
  xp?: number;
  level?: string;
  skills?: string[];
};

export type UserDigest = {
  user_id: string;
  date: string;
  tasks_today: Task[];
  overdue_tasks: Task[];
  upcoming_deadlines: Task[];
};

export type Note = {
  id: string;
  user_id?: string;
  team_id?: string;
  task_id?: string | null;
  meeting_id?: string | null;
  title: string;
  content: string;
  source: 'manual' | 'meeting' | 'ai_summary';
  created_at?: string;
  updated_at?: string;
};

export type Achievement = {
  id: string;
  code?: string;
  title: string;
  description: string;
  icon?: string;
  unlocked_at?: string;
};

export type Recommendation = {
  id: string;
  title: string;
  description: string;
  recommendation_type: 'course' | 'skill' | 'practice' | 'documentation';
  source?: string;
  created_at?: string;
};

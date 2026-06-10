export type TaskStatus = 'backlog' | 'todo' | 'in_progress' | 'review' | 'done' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical';
export type TaskSource = 'telegram_text' | 'telegram_voice' | 'meeting_audio';
export type KanbanProvider = 'external' | 'internal';

export type Task = {
  id: string;
  team_id?: string;
  candidate_id?: string;
  external_kanban_id?: string | null;
  external_kanban_url?: string | null;
  title: string;
  description?: string | null;
  assignee?: string | null;
  assignee_id?: string | null;
  deadline?: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  source: TaskSource;
  confidence?: number | null;
  created_by_ai?: boolean;
  created_at?: string;
  updated_at?: string;
  closed_at?: string | null;
  started_at?: string | null;
  last_status_change_at?: string | null;
  status_changed_count?: number;
  kanban_provider?: KanbanProvider;
  source_message_excerpt?: string | null;
};

export type UpdateTaskStatusPayload = {
  status: TaskStatus;
  changed_by?: string;
  source?: 'telegram_button' | 'dashboard' | 'external_kanban_sync' | 'ai_status_detection';
  comment?: string;
};

export type RescheduleTaskPayload = {
  new_deadline: string;
  changed_by?: string;
  reason?: string;
};

export type TasksQueryParams = {
  team_id?: string;
  assignee_id?: string;
  status?: TaskStatus;
  source?: TaskSource;
  deadline_from?: string;
  deadline_to?: string;
};

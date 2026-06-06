export type Role = 'OWNER' | 'ADMIN' | 'MANAGER' | 'EMPLOYEE' | 'OBSERVER';

export type CurrentUser = {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string | null;
  role: Role;
  department_id?: string | null;
  permission_scopes?: string[] | null;
  team_id?: string | null;
  must_change_password?: boolean;
  permissions?: string[];
  impersonated_by_user_id?: string | null;
};

export type Department = {
  id: string;
  organization_id: string;
  name: string;
  description?: string | null;
  employee_count: number;
  task_count: number;
  overdue_count: number;
  efficiency: number;
  created_at: string;
  updated_at: string;
};

export type Team = {
  id: string;
  organization_id: string;
  department_id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
};

export type OrganizationChat = {
  id: string;
  organization_id: string;
  department_id?: string | null;
  team_id?: string | null;
  telegram_chat_id: number;
  title: string;
  chat_type?: string | null;
  members_count?: number | null;
  is_active: boolean;
  ai_enabled: boolean;
  bot_is_admin: boolean;
  connected_at: string;
};

export type Employee = {
  id: string;
  organization_id: string;
  user_id?: string | null;
  manager_id?: string | null;
  full_name: string;
  email?: string | null;
  role: Role;
  department_id?: string | null;
  permission_scopes?: string[] | null;
  team_id?: string | null;
  position?: string | null;
  telegram_username?: string | null;
  telegram_first_name?: string | null;
  telegram_last_name?: string | null;
  avatar_url?: string | null;
  telegram_status: 'PENDING' | 'CONNECTED' | 'NOT_FOUND' | string;
  telegram_connected_at?: string | null;
  telegram_id?: number | null;
  generated_password?: string | null;
  invitation_text?: string | null;
  active?: boolean;
  is_active: boolean;
  deactivated_at?: string | null;
  deactivated_by?: string | null;
};

export type TaskStatusV2 = 'DETECTED' | 'PENDING_CONFIRMATION' | 'ACCEPTED' | 'REJECTED' | 'TO_DO' | 'IN_PROGRESS' | 'REVIEW' | 'DONE' | 'OVERDUE';

export type KomandusTask = {
  id: string;
  organization_id: string;
  employee_id?: string | null;
  department_id?: string | null;
  team_id?: string | null;
  organization_chat_id?: string | null;
  title: string;
  description?: string | null;
  status: TaskStatusV2;
  due_at?: string | null;
  llm_confidence?: number | null;
  llm_model?: string | null;
  extraction_version?: string | null;
  source_chat_id?: number | null;
  source_message_id?: number | null;
  external_task_id?: string | null;
  external_task_url?: string | null;
  ai_summary?: string | null;
  source_excerpt?: string | null;
  accepted_at?: string | null;
  completed_at?: string | null;
  rejected_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type BoardIntegration = {
  id: string;
  organization_id: string;
  provider: string;
  name: string;
  external_project_id?: string | null;
  external_board_id?: string | null;
  department_id?: string | null;
  team_id?: string | null;
  is_active: boolean;
  metadata_json?: Record<string, unknown> | null;
};

export type DashboardAnalytics = {
  total_tasks: number;
  in_work: number;
  completed: number;
  overdue: number;
  average_completion_time: number;
  average_response_time: number;
  ai_accuracy: number;
  ai_tasks: number;
  acceptance_percent: number;
  rejection_percent: number;
  pie_statuses: Record<string, number>;
  top_employees: Array<{ employee_id: string; employee_name: string; tasks: number }>;
  departments: Array<{ department_id: string; department_name: string; tasks: number }>;
  closed_by_day: Array<{ date: string; completed: number }>;
  burnup: Array<{ date: string; completed_total: number }>;
  attention: Array<{ type: string; title: string; count: number }>;
  activity: Array<{ at: string; text: string }>;
};

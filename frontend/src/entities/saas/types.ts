export type Role = 'SUPER_ADMIN' | 'MANAGER' | 'PRODUCT_MANAGER' | 'EMPLOYEE' | 'VIEWER';

export type CurrentUser = {
  id: string;
  organization_id: string;
  email: string;
  full_name?: string | null;
  role: Role;
};

export type Employee = {
  id: string;
  organization_id: string;
  full_name: string;
  email?: string | null;
  role: Role;
  telegram_id?: number | null;
  is_active: boolean;
};

export type TaskStatusV2 =
  | 'DETECTED'
  | 'PENDING_CONFIRMATION'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'TO_DO'
  | 'IN_PROGRESS'
  | 'REVIEW'
  | 'DONE'
  | 'OVERDUE';

export type KomandusTask = {
  id: string;
  organization_id: string;
  employee_id?: string | null;
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
};

export type BoardIntegration = {
  id: string;
  organization_id: string;
  provider: string;
  name: string;
  external_project_id?: string | null;
  external_board_id?: string | null;
  is_active: boolean;
  metadata_json?: Record<string, unknown> | null;
};

export type DashboardAnalytics = {
  total_tasks: number;
  completed: number;
  overdue: number;
  average_completion_time: number;
  average_response_time: number;
  acceptance_percent: number;
  rejection_percent: number;
  pie_statuses: Record<string, number>;
  top_employees: Array<{ employee_id: string; tasks: number }>;
  closed_by_day: Array<{ date: string; completed: number }>;
  burnup: Array<{ date: string; completed_total: number }>;
};

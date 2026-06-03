import { TaskPriority, TaskSource } from '../task/types';

export type CandidateStatus = 'pending' | 'confirmed' | 'rejected' | 'created' | 'duplicate';

export type TaskCandidate = {
  id: string;
  team_id?: string;
  message_id?: string | null;
  meeting_id?: string | null;
  title: string;
  description?: string | null;
  assignee_id?: string | null;
  assignee_raw?: string | null;
  deadline?: string | null;
  deadline_raw?: string | null;
  priority: TaskPriority;
  confidence: number;
  status: CandidateStatus;
  source: TaskSource;
  missing_fields?: string[];
  reason?: string | null;
  source_excerpt?: string | null;
  source_message_url?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type ConfirmCandidatePayload = {
  confirmed_by?: string;
  overrides?: {
    title?: string;
    description?: string | null;
    deadline?: string | null;
    assignee_id?: string | null;
    assignee_raw?: string | null;
    priority?: TaskPriority;
  };
};

export type RejectCandidatePayload = {
  rejected_by?: string;
  reason?: 'not_a_task' | 'duplicate' | 'wrong_data' | 'other';
};

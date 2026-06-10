import { TaskCandidate } from '../candidate/types';

export type MeetingActionItem = {
  title: string;
  assignee?: string | null;
  deadline?: string | null;
  task_id?: string | null;
};

export type MeetingSummary = {
  id: string;
  title?: string;
  date?: string;
  summary: string;
  decisions: string[];
  action_items: MeetingActionItem[];
  risks: string[];
  open_questions: string[];
  created_task_candidates?: TaskCandidate[];
  created_tasks?: Array<{
    id: string;
    title: string;
    assignee?: string | null;
    deadline?: string | null;
    status?: string | null;
  }>;
  transcript_quality?: number | null;
};

export type MeetingUploadResponse = {
  meeting_id: string;
  status: 'uploaded' | 'transcribing' | 'summarized' | 'failed';
};

export type TaskStatus = 'backlog' | 'todo' | 'in_progress' | 'review' | 'done';
export type Priority = 'low' | 'medium' | 'high' | 'critical';

export interface Task {
  id: string;
  title: string;
  assignee: string;
  deadline: string;
  priority: Priority;
  source: 'telegram' | 'meeting' | 'manual' | 'ai';
  confidence: number;
  externalUrl?: string;
  status: TaskStatus;
  createdByAi: boolean;
  sourceExcerpt: string;
  kanbanProvider?: string;
}

export interface TaskCandidate {
  id: string;
  title: string;
  description: string;
  confidence: number;
  source: 'telegram' | 'meeting' | 'voice';
  excerpt: string;
  suggestedAssignee?: string;
  suggestedDeadline?: string;
  status: 'pending' | 'confirmed' | 'rejected';
}

export interface MeetingSummary {
  id: string;
  title: string;
  shortSummary: string;
  decisions: string[];
  actionItems: string[];
  risks: string[];
  openQuestions: string[];
  createdTasks: number;
  createdCandidates: number;
  transcriptQuality: number;
  knowledgePreview: string[];
}

export interface Analytics {
  aiCreatedTasks: number;
  autoConfirmed: number;
  waitingConfirmation: number;
  rejectedSuggestions: number;
  voiceMessagesProcessed: number;
  meetingsSummarized: number;
  averageConfidence: number;
  doneThisWeek: number;
  overduePercent: number;
  teamVelocity: number;
  aiQuality: number;
}

export interface LeaderboardUser {
  id: string;
  name: string;
  role: string;
  score: number;
  done: number;
}

export interface Profile {
  id: string;
  name: string;
  role: string;
  telegram?: string;
  focus: string;
  achievements: string[];
  recommendations: string[];
  notes: string[];
}

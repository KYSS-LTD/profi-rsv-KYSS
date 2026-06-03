import { TaskPriority, TaskSource, TaskStatus } from './types';

export const kanbanColumns: Array<{ key: TaskStatus; title: string; hint: string }> = [
  { key: 'backlog', title: 'Бэклог', hint: 'новые идеи и входящие задачи' },
  { key: 'todo', title: 'К выполнению', hint: 'подтверждено, ждет старта' },
  { key: 'in_progress', title: 'В работе', hint: 'исполнитель уже начал' },
  { key: 'review', title: 'Проверка', hint: 'нужно ревью или согласование' },
  { key: 'done', title: 'Готово', hint: 'закрытые задачи' },
];

export const taskStatusLabel: Record<TaskStatus, string> = {
  backlog: 'Бэклог',
  todo: 'К выполнению',
  in_progress: 'В работе',
  review: 'Проверка',
  done: 'Готово',
  cancelled: 'Отменено',
};

export const priorityLabel: Record<TaskPriority, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  critical: 'Критичный',
};

export const sourceLabel: Record<TaskSource, string> = {
  telegram_text: 'Telegram текст',
  telegram_voice: 'Telegram голос',
  meeting_audio: 'Встреча',
};

export const kanbanProviderLabel = {
  external: 'Внешняя доска',
  internal: 'Внутренняя доска',
} as const;

export function formatConfidence(confidence?: number | null) {
  if (confidence === undefined || confidence === null) return '—';
  return `${Math.round(confidence * 100)}%`;
}

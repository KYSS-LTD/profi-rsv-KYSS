import { ExternalLink } from 'lucide-react';
import { formatConfidence, kanbanProviderLabel, priorityLabel, sourceLabel, taskStatusLabel } from '../../entities/task/helpers';
import { Task, TaskStatus } from '../../entities/task/types';
import { formatDateTime } from '../../shared/lib/date';
import { Badge } from '../../shared/ui/Badge';
import { Button } from '../../shared/ui/Button';
import { Card } from '../../shared/ui/Card';
import { Dropdown } from '../../shared/ui/Dropdown';

const priorityTone = {
  low: 'neutral',
  medium: 'blue',
  high: 'amber',
  critical: 'red',
} as const;

function askDeadline(): string | null {
  const value = window.prompt('Введите новый срок в формате ГГГГ-ММ-ДД ЧЧ:ММ', '2026-06-03 18:00');
  if (!value) return null;

  const parsed = new Date(value.trim().replace(' ', 'T'));
  if (Number.isNaN(parsed.getTime())) {
    window.alert('Не удалось распознать дату. Пример: 2026-06-03 18:00');
    return null;
  }

  return parsed.toISOString();
}

export function TaskCard({
  task,
  onStatusChange,
  onReschedule,
  isUpdating,
}: {
  task: Task;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string, deadline: string) => void;
  isUpdating?: boolean;
}) {
  return (
    <Card className="rounded-[22px] p-5">
      <div className="mb-4 flex min-w-0 items-start justify-between gap-4">
        <h3 className="min-w-0 text-base font-semibold leading-6 text-stone-950">{task.title}</h3>
        <Badge className="shrink-0" tone={priorityTone[task.priority]}>{priorityLabel[task.priority]}</Badge>
      </div>

      {task.description && <p className="mb-4 text-sm leading-6 text-stone-600">{task.description}</p>}

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge>{sourceLabel[task.source]}</Badge>
        <Badge tone="blue">Точность {formatConfidence(task.confidence)}</Badge>
        {task.created_by_ai && <Badge tone="green">Создано AI</Badge>}
        {task.kanban_provider && <Badge>{kanbanProviderLabel[task.kanban_provider]}</Badge>}
      </div>

      <div className="mb-5 space-y-2.5 text-sm text-stone-600">
        <MetaRow label="Ответственный" value={task.assignee ?? 'Не назначен'} />
        <MetaRow label="Срок" value={formatDateTime(task.deadline)} />
        <MetaRow label="Статус" value={taskStatusLabel[task.status]} />
      </div>

      {task.source_message_excerpt && (
        <p className="mb-5 rounded-2xl bg-stone-50 p-3 text-sm leading-6 text-stone-500">
          «{task.source_message_excerpt}»
        </p>
      )}

      <div className="grid gap-3">
        <Dropdown
          ariaLabel="Изменить статус задачи"
          value={task.status}
          disabled={isUpdating}
          onChange={(value) => onStatusChange(task.id, value as TaskStatus)}
          options={(['backlog', 'todo', 'in_progress', 'review', 'done', 'cancelled'] satisfies TaskStatus[]).map((status) => ({
            value: status,
            label: taskStatusLabel[status],
          }))}
        />

        <div className="grid grid-cols-2 gap-3">
          <Button className="w-full" variant="secondary" disabled={isUpdating} onClick={() => onStatusChange(task.id, 'in_progress')}>
            В работу
          </Button>
          <Button className="w-full" disabled={isUpdating} onClick={() => onStatusChange(task.id, 'done')}>
            Готово
          </Button>
        </div>

        <Button
          className="w-full"
          variant="secondary"
          disabled={isUpdating}
          onClick={() => {
            const deadline = askDeadline();
            if (deadline) onReschedule(task.id, deadline);
          }}
        >
          Перенести срок
        </Button>
      </div>

      {task.external_kanban_url && (
        <a
          className="focus-ring mt-3 inline-flex h-10 w-full items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white px-4 text-sm font-medium leading-none text-stone-800 transition hover:border-stone-300 hover:bg-stone-50"
          href={task.external_kanban_url}
          target="_blank"
          rel="noreferrer"
        >
          Открыть карточку
          <ExternalLink className="h-4 w-4" />
        </a>
      )}
    </Card>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-stone-500">{label}</span>
      <span className="max-w-[62%] text-right font-medium text-stone-900">{value}</span>
    </div>
  );
}

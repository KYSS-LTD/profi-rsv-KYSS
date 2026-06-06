import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarDays, ExternalLink, MoveRight } from 'lucide-react';
import type { Task, TaskStatus } from '@/entities/types';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { EmptyState } from '@/shared/ui/EmptyState';
import { Loader } from '@/shared/ui/Loader';
import { PageHeader } from '@/shared/ui/PageHeader';
import { haptic } from '@/shared/lib/telegram';

const columns: Array<{ id: TaskStatus; title: string }> = [
  { id: 'backlog', title: 'Backlog' },
  { id: 'todo', title: 'Todo' },
  { id: 'in_progress', title: 'In Progress' },
  { id: 'review', title: 'Review' },
  { id: 'done', title: 'Done' },
];

const priorityTone = {
  low: 'slate',
  medium: 'blue',
  high: 'yellow',
  critical: 'red',
} as const;

const nextStatus: Record<TaskStatus, TaskStatus> = {
  backlog: 'todo',
  todo: 'in_progress',
  in_progress: 'review',
  review: 'done',
  done: 'done',
};

function TaskCard({ task }: { task: Task }) {
  const queryClient = useQueryClient();
  const updateStatus = useMutation({
    mutationFn: (status: TaskStatus) => api.updateTaskStatus(task.id, status),
    onSuccess: () => {
      haptic.success();
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  const reschedule = useMutation({
    mutationFn: () => {
      const nextDate = new Date(task.deadline);
      nextDate.setDate(nextDate.getDate() + 1);
      return api.rescheduleTask(task.id, nextDate.toISOString().slice(0, 10));
    },
    onSuccess: () => {
      haptic.tap();
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  return (
    <article className="rounded-3xl border border-black/5 bg-tg-secondaryBg p-4 shadow-sm dark:border-white/10">
      <div className="flex flex-wrap gap-2">
        <Badge tone={priorityTone[task.priority]}>{task.priority}</Badge>
        <Badge tone="purple">{Math.round(task.confidence * 100)}% AI</Badge>
        <Badge tone="slate">{task.source}</Badge>
      </div>
      <h3 className="mt-3 text-base font-black leading-6 text-tg-text">{task.title}</h3>
      <p className="mt-2 text-sm leading-5 text-tg-hint">{task.sourceExcerpt}</p>

      <div className="mt-4 grid gap-2 text-xs text-tg-hint">
        <div className="flex items-center justify-between rounded-2xl bg-slate-100 px-3 py-2 dark:bg-white/10">
          <span>Assignee</span>
          <strong className="text-tg-text">{task.assignee}</strong>
        </div>
        <div className="flex items-center justify-between rounded-2xl bg-slate-100 px-3 py-2 dark:bg-white/10">
          <span className="inline-flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" /> Deadline</span>
          <strong className="text-tg-text">{task.deadline}</strong>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          size="sm"
          variant={task.status === 'done' ? 'secondary' : 'primary'}
          disabled={task.status === 'done' || updateStatus.isPending}
          onClick={() => updateStatus.mutate(nextStatus[task.status])}
        >
          Move <MoveRight className="h-3.5 w-3.5" />
        </Button>
        <Button size="sm" variant="secondary" disabled={reschedule.isPending} onClick={() => reschedule.mutate()}>
          +1 day
        </Button>
        {task.externalUrl && (
          <a href={task.externalUrl} target="_blank" rel="noreferrer">
            <Button size="sm" variant="ghost"><ExternalLink className="h-3.5 w-3.5" /> Source</Button>
          </a>
        )}
      </div>
    </article>
  );
}

export function TasksPage() {
  const { data, isLoading } = useQuery({ queryKey: ['tasks'], queryFn: api.getTasks });
  const grouped = useMemo(() => {
    const tasks = data ?? [];
    return columns.map((column) => ({ ...column, tasks: tasks.filter((task) => task.status === column.id) }));
  }, [data]);

  return (
    <section>
      <PageHeader
        eyebrow="Mini-kanban"
        title="Задачи команды"
        description="Статусы, дедлайны, source badges и confidence из AI. Можно менять статус и переносить дедлайн через backend endpoints или mock store."
      />

      {isLoading && <Loader />}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState title="Задач пока нет" description="Когда бот найдёт action items в чате или встрече, они появятся здесь." />
      )}

      {!isLoading && data && data.length > 0 && (
        <div className="grid gap-4 xl:grid-cols-5">
          {grouped.map((column) => (
            <Card key={column.id} className="p-3">
              <div className="mb-3 flex items-center justify-between px-1">
                <h2 className="font-black text-tg-text">{column.title}</h2>
                <Badge>{column.tasks.length}</Badge>
              </div>
              <div className="grid gap-3">
                {column.tasks.length ? column.tasks.map((task) => <TaskCard key={task.id} task={task} />) : (
                  <div className="rounded-3xl border border-dashed border-slate-300 p-5 text-center text-sm text-tg-hint dark:border-white/10">Пусто</div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

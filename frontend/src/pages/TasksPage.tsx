import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  CalendarDays,
  CheckCircle2,
  ExternalLink,
  MoreVertical,
  PackageOpen,
  PlayCircle,
  Plus,
  RotateCcw,
  Search,
  Settings2,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { formatConfidence, sourceLabel, taskStatusLabel } from '../entities/task/helpers';
import { Task, TaskSource, TaskStatus } from '../entities/task/types';
import { getTasks, rescheduleTask, updateTaskStatus } from '../shared/api/tasks';
import { env } from '../shared/config/env';
import { cn } from '../shared/lib/cn';
import { formatDateTime } from '../shared/lib/date';
import { Button } from '../shared/ui/Button';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { Select } from '../shared/ui/Select';

const visibleStatuses: TaskStatus[] = ['todo', 'in_progress', 'review', 'done'];

const statusDot: Record<TaskStatus, string> = {
  backlog: 'bg-stone-400',
  todo: 'bg-amber-500',
  in_progress: 'bg-blue-500',
  review: 'bg-red-500',
  done: 'bg-emerald-500',
  cancelled: 'bg-stone-300',
};

const assigneeInitials: Record<string, string> = {
  Алексей: 'А',
  Мария: 'М',
  Иван: 'И',
  Даниил: 'Д',
  Дарья: 'Д',
  Артём: 'А',
  Павел: 'П',
};

const demoRowsFallback: Task[] = [
  {
    id: 'demo_1',
    title: 'Интеграция Telegram бота с API',
    assignee: 'Алексей',
    deadline: '2026-05-20T18:00:00+03:00',
    status: 'in_progress',
    priority: 'high',
    source: 'telegram_text',
    confidence: 0.92,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/demo_1',
  },
  {
    id: 'demo_2',
    title: 'Обновить пайплайн обработки голоса',
    assignee: 'Мария',
    deadline: '2026-05-21T18:00:00+03:00',
    status: 'todo',
    priority: 'medium',
    source: 'telegram_voice',
    confidence: 0.74,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/demo_2',
  },
  {
    id: 'demo_3',
    title: 'Подготовить отчёт по встрече с клиентом',
    assignee: 'Иван',
    deadline: '2026-05-18T18:00:00+03:00',
    status: 'review',
    priority: 'critical',
    source: 'meeting_audio',
    confidence: 0.9,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/demo_3',
  },
  {
    id: 'demo_4',
    title: 'Создать дашборд по метрикам',
    assignee: 'Дарья',
    deadline: '2026-05-23T18:00:00+03:00',
    status: 'in_progress',
    priority: 'medium',
    source: 'meeting_audio',
    confidence: 0.76,
    created_by_ai: true,
    kanban_provider: 'internal',
  },
  {
    id: 'demo_5',
    title: 'Добавить экспорт в PDF',
    assignee: 'Артём',
    deadline: '2026-05-25T18:00:00+03:00',
    status: 'todo',
    priority: 'low',
    source: 'telegram_text',
    confidence: 0.52,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/demo_5',
  },
  {
    id: 'demo_6',
    title: 'Настроить уведомления о задачах',
    assignee: 'Алексей',
    deadline: '2026-05-15T18:00:00+03:00',
    status: 'done',
    priority: 'medium',
    source: 'meeting_audio',
    confidence: 0.88,
    created_by_ai: true,
    kanban_provider: 'external',
    external_kanban_url: 'https://kanban.example/card/demo_6',
  },
];

type SourceFilter = 'all' | TaskSource;
type StatusFilter = 'all' | TaskStatus;

type MetricTone = 'blue' | 'green' | 'amber' | 'red';

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

export function TasksPage() {
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [assignee, setAssignee] = useState('all');
  const [status, setStatus] = useState<StatusFilter>('all');
  const [source, setSource] = useState<SourceFilter>('all');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const tasksQuery = useQuery({
    queryKey: ['tasks', env.defaultTeamId],
    queryFn: () => getTasks({ team_id: env.defaultTeamId }),
  });

  const statusMutation = useMutation({
    mutationFn: ({ taskId, nextStatus }: { taskId: string; nextStatus: TaskStatus }) =>
      updateTaskStatus(taskId, { status: nextStatus, changed_by: env.defaultUserId, source: 'dashboard' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ taskId, deadline }: { taskId: string; deadline: string }) =>
      rescheduleTask(taskId, {
        new_deadline: deadline,
        changed_by: env.defaultUserId,
        reason: 'Перенос из frontend dashboard',
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  });

  const apiTasks = tasksQuery.data ?? [];
  const tasks = apiTasks.length > 0 ? apiTasks : demoRowsFallback;

  const assignees = useMemo(() => Array.from(new Set(tasks.map((task) => task.assignee).filter(Boolean))) as string[], [tasks]);

  const filteredTasks = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    return tasks.filter((task) => {
      const matchesQuery =
        !normalized ||
        [task.title, task.description, task.assignee, sourceLabel[task.source], taskStatusLabel[task.status]]
          .filter(Boolean)
          .join(' ')
          .toLowerCase()
          .includes(normalized);
      const matchesAssignee = assignee === 'all' || task.assignee === assignee;
      const matchesStatus = status === 'all' || task.status === status;
      const matchesSource = source === 'all' || task.source === source;

      return matchesQuery && matchesAssignee && matchesStatus && matchesSource;
    });
  }, [assignee, query, source, status, tasks]);

  const selectedTask = filteredTasks.find((task) => task.id === selectedTaskId) ?? filteredTasks[2] ?? filteredTasks[0];
  const isSaving = statusMutation.isPending || rescheduleMutation.isPending;
  const inWork = tasks.filter((task) => task.status === 'in_progress').length;
  const inReview = tasks.filter((task) => task.status === 'review').length;
  const overdue = tasks.filter((task) => task.deadline && new Date(task.deadline).getTime() < Date.now() && task.status !== 'done').length;

  function updateStatus(taskId: string, nextStatus: TaskStatus) {
    statusMutation.mutate({ taskId, nextStatus });
  }

  function reschedule(taskId: string) {
    const deadline = askDeadline();
    if (deadline) rescheduleMutation.mutate({ taskId, deadline });
  }

  function resetFilters() {
    setQuery('');
    setAssignee('all');
    setStatus('all');
    setSource('all');
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-stone-950 md:text-4xl">Задачи и мини-канбан</h1>
          <p className="mt-2 max-w-3xl text-base leading-7 text-stone-500">
            Все задачи команды и их текущий статус в компактном представлении.
          </p>
        </div>
      </div>

      <section className="rounded-3xl border border-stone-200 bg-white p-4 shadow-sm shadow-stone-950/[0.03]">
        <div className="grid gap-3 lg:grid-cols-[minmax(240px,1.4fr)_minmax(150px,0.8fr)_minmax(150px,0.8fr)_minmax(150px,0.8fr)_minmax(150px,0.9fr)_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
            <Input
              className="h-11 rounded-2xl pl-10"
              placeholder="Поиск по задачам..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <FilterSelect label="Ответственный" value={assignee} onChange={setAssignee}>
            <option value="all">Все</option>
            {assignees.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </FilterSelect>

          <FilterSelect label="Статус" value={status} onChange={(value) => setStatus(value as StatusFilter)}>
            <option value="all">Все</option>
            {visibleStatuses.map((item) => (
              <option key={item} value={item}>{taskStatusLabel[item]}</option>
            ))}
          </FilterSelect>

          <FilterSelect label="Источник" value={source} onChange={(value) => setSource(value as SourceFilter)}>
            <option value="all">Все</option>
            <option value="telegram_text">Telegram</option>
            <option value="telegram_voice">Voice</option>
            <option value="meeting_audio">Meeting</option>
          </FilterSelect>

          <button className="focus-ring flex h-11 items-center justify-center gap-2 rounded-2xl border border-stone-200 bg-white px-3 text-sm font-semibold text-stone-800 transition hover:bg-stone-50">
            <CalendarDays className="h-4 w-4" />
            12 мая – 18 мая
          </button>

          <button
            className="focus-ring flex h-11 items-center justify-center gap-2 rounded-2xl border border-stone-200 bg-white px-4 text-sm font-semibold text-stone-800 transition hover:bg-stone-50"
            onClick={resetFilters}
          >
            <RotateCcw className="h-4 w-4" />
            Сбросить
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<PackageOpen className="h-6 w-6" />} label="Всего задач" value={String(tasks.length)} note="на этой неделе" tone="blue" badge="+3" />
        <MetricCard icon={<PlayCircle className="h-6 w-6" />} label="В работе" value={String(inWork)} note="активные задачи" tone="green" badge="33%" />
        <MetricCard icon={<CheckCircle2 className="h-6 w-6" />} label="На проверке" value={String(inReview)} note="ждут ревью" tone="amber" badge="22%" />
        <MetricCard icon={<AlertCircle className="h-6 w-6" />} label="Просрочено" value={String(overdue)} note="нужна реакция" tone="red" badge="11%" />
      </section>

      {tasksQuery.isLoading && <Loader text="Загружаем задачи..." />}
      {tasksQuery.error && <ErrorState error={tasksQuery.error} />}

      {!tasksQuery.isLoading && !tasksQuery.error && (
        <section className="grid gap-5 xl:grid-cols-[minmax(650px,1.05fr)_minmax(520px,0.95fr)]">
          <TasksList
            tasks={filteredTasks}
            selectedTaskId={selectedTask?.id}
            onSelect={setSelectedTaskId}
            onStatusChange={updateStatus}
            onReschedule={reschedule}
            isSaving={isSaving}
          />

          <MiniKanban
            tasks={filteredTasks}
            onStatusChange={updateStatus}
            onReschedule={reschedule}
            isSaving={isSaving}
          />
        </section>
      )}
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  return (
    <label className="relative block">
      <span className="absolute -top-2 left-4 bg-white px-1 text-[11px] font-medium text-stone-500">{label}</span>
      <Select className="h-11 rounded-2xl pt-1 font-semibold" value={value} onChange={(event) => onChange(event.target.value)}>
        {children}
      </Select>
    </label>
  );
}

function MetricCard({ icon, label, value, note, tone, badge }: { icon: React.ReactNode; label: string; value: string; note: string; tone: MetricTone; badge: string }) {
  const tones: Record<MetricTone, string> = {
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    green: 'bg-emerald-50 text-emerald-600 border-emerald-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    red: 'bg-red-50 text-red-600 border-red-100',
  };

  const badgeTones: Record<MetricTone, string> = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700',
  };

  return (
    <article className="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm shadow-stone-950/[0.03]">
      <div className="flex items-center gap-4">
        <div className={cn('flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border', tones[tone])}>{icon}</div>
        <div className="min-w-0">
          <p className="text-sm text-stone-500">{label}</p>
          <div className="mt-1 flex items-center gap-2">
            <p className="text-3xl font-bold tracking-tight text-stone-950">{value}</p>
            <span className={cn('rounded-full px-2 py-1 text-xs font-bold', badgeTones[tone])}>{badge}</span>
          </div>
          <p className="text-sm text-stone-500">{note}</p>
        </div>
      </div>
    </article>
  );
}

function TasksList({
  tasks,
  selectedTaskId,
  onSelect,
  onStatusChange,
  onReschedule,
  isSaving,
}: {
  tasks: Task[];
  selectedTaskId?: string;
  onSelect: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string) => void;
  isSaving?: boolean;
}) {
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) ?? tasks[0];

  return (
    <section className="overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-sm shadow-stone-950/[0.03]">
      <div className="flex items-center justify-between gap-3 px-5 py-4">
        <h2 className="text-lg font-bold text-stone-950">Список задач</h2>
        <div className="flex items-center gap-2">
          <Button className="h-9 rounded-xl px-3" variant="secondary">
            <Plus className="h-4 w-4" />
            Новая задача
          </Button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl border border-stone-200 bg-white text-stone-500 hover:bg-stone-50">
            <MoreVertical className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[850px]">
          <div className="grid grid-cols-[minmax(220px,1.6fr)_120px_90px_120px_120px_110px_40px] border-b border-stone-100 px-5 py-3 text-xs font-medium text-stone-500">
            <span>Задача</span>
            <span>Ответственный</span>
            <span>Срок</span>
            <span>Источник</span>
            <span>AI уверенность</span>
            <span>Статус</span>
            <span />
          </div>

          {tasks.map((task) => {
            const selected = task.id === selectedTask?.id;
            return (
              <div key={task.id}>
                <button
                  className={cn(
                    'grid w-full grid-cols-[minmax(220px,1.6fr)_120px_90px_120px_120px_110px_40px] items-center border-b border-stone-100 px-5 py-3 text-left transition hover:bg-stone-50',
                    selected && 'bg-[#f7f1e8] hover:bg-[#f7f1e8]',
                  )}
                  onClick={() => onSelect(task.id)}
                >
                  <span className="flex min-w-0 items-start gap-3">
                    <span className={cn('mt-2 h-2 w-2 shrink-0 rounded-full', statusDot[task.status])} />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-bold leading-5 text-stone-950">{task.title}</span>
                      {task.description && <span className="block truncate text-xs text-stone-500">{task.description}</span>}
                    </span>
                  </span>
                  <span className="flex items-center gap-2 text-sm text-stone-500">
                    <Avatar name={task.assignee ?? 'Н'} />
                    <span className="truncate">{task.assignee ?? 'Не назначен'}</span>
                  </span>
                  <span className={cn('text-sm font-semibold', isOverdue(task) ? 'text-red-500' : 'text-stone-500')}>{shortDate(task.deadline)}</span>
                  <span><SourceBadge source={task.source} /></span>
                  <span><ConfidenceBadge confidence={task.confidence} /></span>
                  <span><StatusBadge status={task.status} /></span>
                  <span className="flex justify-end text-stone-400"><MoreVertical className="h-4 w-4" /></span>
                </button>

                {selected && (
                  <div className="border-b border-stone-100 bg-[#f7f1e8] px-5 pb-4">
                    <div className="rounded-2xl border border-stone-200 bg-white p-3">
                      <div className="grid gap-3 sm:grid-cols-[110px_110px_140px_1fr]">
                        <Button disabled={isSaving} onClick={() => onStatusChange(task.id, 'in_progress')}>В работу</Button>
                        <Button disabled={isSaving} variant="secondary" onClick={() => onStatusChange(task.id, 'done')}>Готово</Button>
                        <Button disabled={isSaving} variant="secondary" onClick={() => onReschedule(task.id)}>Перенести срок</Button>
                        {task.external_kanban_url ? (
                          <a
                            className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white px-4 text-sm font-semibold text-stone-800 transition hover:bg-stone-50"
                            href={task.external_kanban_url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Открыть карточку
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        ) : (
                          <Button className="justify-self-stretch" variant="secondary" disabled>Внутренняя доска</Button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 px-5 py-4 text-sm text-stone-500">
        <span>1–{Math.min(tasks.length, 5)} из {tasks.length} задач</span>
        <div className="flex items-center gap-3">
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl border border-stone-200 bg-white text-stone-300">‹</button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl bg-[#f7f1e8] font-semibold text-stone-950">1</button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl text-stone-950">2</button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl text-stone-950">3</button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl text-stone-950">4</button>
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl border border-stone-200 bg-white text-stone-950">›</button>
        </div>
      </div>
    </section>
  );
}

function MiniKanban({
  tasks,
  onStatusChange,
}: {
  tasks: Task[];
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string) => void;
  isSaving?: boolean;
}) {
  return (
    <section className="rounded-3xl border border-stone-200 bg-white p-5 shadow-sm shadow-stone-950/[0.03]">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-stone-950">Мини-канбан</h2>
        <button className="focus-ring inline-flex items-center gap-2 rounded-xl px-2 py-1 text-sm font-medium text-stone-500 hover:bg-stone-50">
          <Settings2 className="h-4 w-4" />
          Настроить
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {visibleStatuses.map((item) => {
          const columnTasks = tasks.filter((task) => task.status === item).slice(0, 2);
          return (
            <article key={item} className="rounded-2xl border border-stone-200 bg-stone-50/70 p-3">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h3 className="text-sm font-bold text-stone-950">{taskStatusLabel[item]}</h3>
                <span className="flex h-7 min-w-7 items-center justify-center rounded-lg border border-stone-200 bg-white px-2 text-xs font-bold text-stone-600">
                  {tasks.filter((task) => task.status === item).length}
                </span>
              </div>

              <div className="space-y-2">
                {columnTasks.map((task) => (
                  <button
                    key={task.id}
                    className="w-full rounded-xl border border-stone-200 bg-white p-3 text-left transition hover:-translate-y-0.5 hover:shadow-sm"
                    onClick={() => onStatusChange(task.id, item)}
                  >
                    <div className="mb-2 flex items-start gap-2">
                      <span className={cn('mt-1.5 h-2 w-2 shrink-0 rounded-full', statusDot[task.status])} />
                      <p className="line-clamp-2 text-sm font-bold leading-5 text-stone-950">{task.title}</p>
                    </div>
                    <div className="flex items-center justify-between gap-2 pl-4">
                      <span className="truncate text-xs text-stone-500">{task.assignee ?? 'Не назначен'} · {shortDate(task.deadline)}</span>
                      <SourceBadge source={task.source} compact />
                    </div>
                  </button>
                ))}
                {columnTasks.length === 0 && <div className="rounded-xl border border-dashed border-stone-200 bg-white p-4 text-center text-sm text-stone-400">Пусто</div>}
                <button className="focus-ring flex h-9 w-full items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white text-sm font-medium text-stone-500 hover:bg-stone-50">
                  <Plus className="h-4 w-4" />
                  Добавить задачу
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function Avatar({ name }: { name: string }) {
  const initial = assigneeInitials[name] ?? name.slice(0, 1).toUpperCase();
  return <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#f7f1e8] text-xs font-bold text-stone-700">{initial}</span>;
}

function SourceBadge({ source, compact }: { source: TaskSource; compact?: boolean }) {
  const config = {
    telegram_text: ['↗', 'Telegram', 'border-blue-200 bg-blue-50 text-blue-700'],
    telegram_voice: ['♬', 'Voice', 'border-violet-200 bg-violet-50 text-violet-700'],
    meeting_audio: ['♚', 'Meeting', 'border-teal-200 bg-teal-50 text-teal-700'],
  } as const;
  const [icon, label, className] = config[source];

  return (
    <span className={cn('inline-flex h-7 items-center justify-center gap-1 rounded-lg border px-2 text-xs font-bold leading-none', className, compact && 'h-6 px-1.5 text-[11px]')}>
      <span>{icon}</span>
      {!compact && label}
    </span>
  );
}

function ConfidenceBadge({ confidence }: { confidence?: number | null }) {
  const value = confidence ?? 0;
  const label = value >= 0.85 ? 'Высокая' : value >= 0.65 ? 'Средняя' : 'Низкая';
  const className =
    value >= 0.85
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : value >= 0.65
        ? 'border-amber-200 bg-amber-50 text-amber-700'
        : 'border-red-200 bg-red-50 text-red-700';

  return <span className={cn('inline-flex h-7 items-center justify-center rounded-lg border px-2 text-xs font-bold', className)}>{label}</span>;
}

function StatusBadge({ status }: { status: TaskStatus }) {
  const className =
    status === 'in_progress' || status === 'done'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
      : status === 'review'
        ? 'border-amber-200 bg-amber-50 text-amber-700'
        : 'border-stone-200 bg-stone-50 text-stone-600';

  return <span className={cn('inline-flex h-7 items-center justify-center rounded-lg border px-2 text-xs font-bold', className)}>{taskStatusLabel[status]}</span>;
}

function shortDate(deadline?: string | null) {
  if (!deadline) return '—';
  const date = new Date(deadline);
  if (Number.isNaN(date.getTime())) return deadline;
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }).replace('.', '');
}

function isOverdue(task: Task) {
  if (!task.deadline || task.status === 'done') return false;
  return new Date(task.deadline).getTime() < Date.now();
}

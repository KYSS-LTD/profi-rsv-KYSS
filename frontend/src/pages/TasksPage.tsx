import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertCircle,
  CalendarDays,
  Check,
  CheckCircle2,
  ChevronDown,
  ExternalLink,
  Maximize2,
  Minimize2,
  MoreVertical,
  PackageOpen,
  PlayCircle,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Settings2,
} from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { priorityLabel, sourceLabel, taskStatusLabel } from '../entities/task/helpers';
import { Task, TaskPriority, TaskSource, TaskStatus } from '../entities/task/types';
import { getTasks, rescheduleTask, updateTaskStatus } from '../shared/api/tasks';
import { env } from '../shared/config/env';
import { cn } from '../shared/lib/cn';
import { Button } from '../shared/ui/Button';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Dropdown, DropdownOption } from '../shared/ui/Dropdown';
import { Loader } from '../shared/ui/Loader';
import { Menu } from '../shared/ui/Menu';
import { Modal } from '../shared/ui/Modal';
import { MeetingIcon, TelegramIcon, VoiceIcon } from '../shared/ui/source-icons';

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

const RANGES = [
  { key: 'all', label: 'Всё время', days: null },
  { key: 'week', label: 'Ближайшая неделя', days: 7 },
  { key: 'two_weeks', label: 'Ближайшие 2 недели', days: 14 },
  { key: 'month', label: 'Ближайший месяц', days: 30 },
] as const;

type RangeKey = (typeof RANGES)[number]['key'];

const DAY_MS = 86_400_000;

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
  const [range, setRange] = useState<RangeKey>('all');
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [createState, setCreateState] = useState<{ open: boolean; status: TaskStatus }>({ open: false, status: 'todo' });

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
    const rangeDays = RANGES.find((item) => item.key === range)?.days ?? null;
    const rangeLimit = rangeDays == null ? null : Date.now() + rangeDays * DAY_MS;

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
      const matchesRange =
        rangeLimit == null || (task.deadline != null && new Date(task.deadline).getTime() <= rangeLimit);

      return matchesQuery && matchesAssignee && matchesStatus && matchesSource && matchesRange;
    });
  }, [assignee, query, range, source, status, tasks]);

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

  function openCreate(nextStatus: TaskStatus = 'todo') {
    setCreateState({ open: true, status: nextStatus });
  }

  function createTask(input: { title: string; assignee: string; deadline: string; priority: TaskPriority; status: TaskStatus }) {
    const newTask: Task = {
      id: crypto.randomUUID(),
      title: input.title.trim(),
      assignee: input.assignee.trim() || null,
      deadline: input.deadline ? new Date(`${input.deadline}T18:00`).toISOString() : null,
      status: input.status,
      priority: input.priority,
      source: 'telegram_text',
      confidence: null,
      created_by_ai: false,
      kanban_provider: 'internal',
    };

    queryClient.setQueryData<Task[]>(['tasks', env.defaultTeamId], (old) => [newTask, ...(old ?? [])]);
    setCreateState((state) => ({ ...state, open: false }));
    setSelectedTaskId(newTask.id);
  }

  function resetFilters() {
    setQuery('');
    setAssignee('all');
    setStatus('all');
    setSource('all');
    setRange('all');
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-display font-bold text-gradient-ink">Задачи и мини-канбан</h1>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-stone-500">
            Все задачи команды и их текущий статус в компактном представлении.
          </p>
        </div>
      </div>

      <section className="grain-surface rounded-3xl border border-stone-200 bg-white p-4 shadow-elevated">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(220px,1.4fr)_minmax(130px,0.85fr)_minmax(130px,0.85fr)_minmax(130px,0.85fr)_minmax(130px,0.9fr)_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
            <Input
              className="h-11 rounded-2xl pl-10"
              placeholder="Поиск по задачам..."
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <FilterSelect
            label="Ответственный"
            value={assignee}
            onChange={setAssignee}
            options={[{ value: 'all', label: 'Все' }, ...assignees.map((item) => ({ value: item, label: item }))]}
          />

          <FilterSelect
            label="Статус"
            value={status}
            onChange={(value) => setStatus(value as StatusFilter)}
            options={[{ value: 'all', label: 'Все' }, ...visibleStatuses.map((item) => ({ value: item, label: taskStatusLabel[item] }))]}
          />

          <FilterSelect
            label="Источник"
            value={source}
            onChange={(value) => setSource(value as SourceFilter)}
            options={[
              { value: 'all', label: 'Все' },
              { value: 'telegram_text', label: 'Telegram', icon: <TelegramIcon className="h-4 w-4 text-blue-600" /> },
              { value: 'telegram_voice', label: 'Voice', icon: <VoiceIcon className="h-4 w-4 text-violet-600" /> },
              { value: 'meeting_audio', label: 'Meeting', icon: <MeetingIcon className="h-4 w-4 text-teal-600" /> },
            ]}
          />

          <RangeFilter value={range} onChange={setRange} />

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
        <section className="grid gap-5 2xl:grid-cols-[minmax(704px,1.05fr)_minmax(448px,0.95fr)]">
          <TasksList
            tasks={filteredTasks}
            selectedTaskId={selectedTask?.id}
            onSelect={setSelectedTaskId}
            onStatusChange={updateStatus}
            onReschedule={reschedule}
            onNewTask={() => openCreate('todo')}
            onRefresh={() => queryClient.invalidateQueries({ queryKey: ['tasks'] })}
            onResetFilters={resetFilters}
            isSaving={isSaving}
          />

          <MiniKanban
            tasks={filteredTasks}
            onStatusChange={updateStatus}
            onReschedule={reschedule}
            onNewTask={openCreate}
            isSaving={isSaving}
          />
        </section>
      )}

      <NewTaskModal
        open={createState.open}
        initialStatus={createState.status}
        assignees={assignees}
        onClose={() => setCreateState((state) => ({ ...state, open: false }))}
        onCreate={createTask}
      />
    </div>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: DropdownOption[];
}) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute -top-2 left-4 z-10 bg-white px-1 text-[11px] font-medium text-stone-500">{label}</span>
      <Dropdown ariaLabel={label} className="h-11 rounded-2xl pt-1 font-semibold text-stone-800" value={value} onChange={onChange} options={options} />
    </div>
  );
}

function MetricCard({ icon, label, value, note, tone, badge }: { icon: React.ReactNode; label: string; value: string; note: string; tone: MetricTone; badge: string }) {
  const tones: Record<MetricTone, string> = {
    blue: 'bg-gradient-to-br from-blue-50 to-blue-100 text-blue-600 ring-1 ring-inset ring-blue-200/70',
    green: 'bg-gradient-to-br from-emerald-50 to-emerald-100 text-emerald-600 ring-1 ring-inset ring-emerald-200/70',
    amber: 'bg-gradient-to-br from-amber-50 to-amber-100 text-amber-600 ring-1 ring-inset ring-amber-200/70',
    red: 'bg-gradient-to-br from-red-50 to-red-100 text-red-600 ring-1 ring-inset ring-red-200/70',
  };

  const badgeTones: Record<MetricTone, string> = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    red: 'bg-red-100 text-red-700',
  };

  return (
    <article className="grain-surface rounded-3xl border border-stone-900/[0.06] bg-white p-5 shadow-elevated transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex items-center gap-4">
        <div className={cn('flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl shadow-sm', tones[tone])}>{icon}</div>
        <div className="min-w-0">
          <p className="text-sm text-stone-500">{label}</p>
          <div className="mt-1 flex items-center gap-2">
            <p className="nums font-display text-4xl font-bold leading-none text-stone-950">{value}</p>
            <span className={cn('nums rounded-full px-2 py-1 text-xs font-bold', badgeTones[tone])}>{badge}</span>
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
  onNewTask,
  onRefresh,
  onResetFilters,
  isSaving,
}: {
  tasks: Task[];
  selectedTaskId?: string;
  onSelect: (taskId: string) => void;
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string) => void;
  onNewTask: () => void;
  onRefresh: () => void;
  onResetFilters: () => void;
  isSaving?: boolean;
}) {
  const selectedTask = tasks.find((task) => task.id === selectedTaskId) ?? tasks[0];

  return (
    <section className="grain-surface overflow-hidden rounded-3xl border border-stone-200 bg-white shadow-elevated">
      <div className="flex items-center justify-between gap-3 px-5 py-4">
        <h2 className="text-lg font-semibold tracking-tight text-stone-950">Список задач</h2>
        <div className="flex items-center gap-2">
          <Button className="h-9 rounded-xl px-3" variant="secondary" onClick={onNewTask}>
            <Plus className="h-4 w-4" />
            Новая задача
          </Button>
          <Menu
            ariaLabel="Действия со списком"
            triggerClassName="focus-ring flex h-9 w-9 items-center justify-center rounded-xl border border-stone-200 bg-white text-stone-500 transition-colors hover:bg-stone-50"
            items={[
              { label: 'Обновить список', icon: <RefreshCw className="h-4 w-4" />, onClick: onRefresh },
              { label: 'Сбросить фильтры', icon: <RotateCcw className="h-4 w-4" />, onClick: onResetFilters },
            ]}
          >
            <MoreVertical className="h-4 w-4" />
          </Menu>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-[700px]">
          <div className="grid gap-x-4 grid-cols-[minmax(96px,1fr)_96px_56px_96px_92px_108px_24px] border-b border-stone-100 px-5 py-3 text-xs font-medium text-stone-500">
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
                    'grid w-full gap-x-4 grid-cols-[minmax(96px,1fr)_96px_56px_96px_92px_108px_24px] items-center border-b border-stone-100 px-5 py-3 text-left transition hover:bg-stone-50',
                    selected && 'bg-brand-50 hover:bg-brand-50',
                  )}
                  onClick={() => onSelect(task.id)}
                >
                  <span className="flex min-w-0 items-start gap-3">
                    <span className={cn('mt-2 h-2 w-2 shrink-0 rounded-full', statusDot[task.status])} />
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold leading-5 text-stone-950">{task.title}</span>
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
                  <div className="border-b border-stone-100 bg-brand-50 px-5 pb-4">
                    <div className="animate-scale-in rounded-2xl border border-stone-200 bg-white p-3">
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
          <button className="focus-ring flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 font-semibold text-white shadow-brand-sm">1</button>
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
  onNewTask,
}: {
  tasks: Task[];
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string) => void;
  onNewTask: (status: TaskStatus) => void;
  isSaving?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="grain-surface rounded-3xl border border-stone-200 bg-white p-5 shadow-elevated">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight text-stone-950">Мини-канбан</h2>
        <Menu
          ariaLabel="Настройки канбана"
          triggerClassName="focus-ring inline-flex items-center gap-2 rounded-xl px-2 py-1 text-sm font-medium text-stone-500 transition-colors hover:bg-stone-50"
          items={[
            {
              label: expanded ? 'Показывать по 2 задачи' : 'Показать все задачи',
              icon: expanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />,
              onClick: () => setExpanded((value) => !value),
            },
          ]}
        >
          <Settings2 className="h-4 w-4" />
          Настроить
        </Menu>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {visibleStatuses.map((item) => {
          const columnTasks = tasks.filter((task) => task.status === item).slice(0, expanded ? undefined : 2);
          return (
            <article key={item} className="rounded-2xl border border-stone-200 bg-stone-50/70 p-3">
              <div className="mb-3 flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold tracking-tight text-stone-950">{taskStatusLabel[item]}</h3>
                <span className="nums flex h-7 min-w-7 items-center justify-center rounded-lg border border-stone-200 bg-white px-2 text-xs font-bold text-stone-600">
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
                      <p className="line-clamp-2 text-sm font-semibold leading-5 text-stone-950">{task.title}</p>
                    </div>
                    <div className="flex items-center justify-between gap-2 pl-4">
                      <span className="truncate text-xs text-stone-500">{task.assignee ?? 'Не назначен'} · {shortDate(task.deadline)}</span>
                      <SourceBadge source={task.source} compact />
                    </div>
                  </button>
                ))}
                {columnTasks.length === 0 && <div className="rounded-xl border border-dashed border-stone-200 bg-white p-4 text-center text-sm text-stone-400">Пусто</div>}
                <button
                  type="button"
                  onClick={() => onNewTask(item)}
                  className="focus-ring flex h-9 w-full items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white text-sm font-medium text-stone-500 transition-colors hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700"
                >
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
  return <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">{initial}</span>;
}

const sourceConfig = {
  telegram_text: { Icon: TelegramIcon, label: 'Telegram', className: 'border-blue-200 bg-blue-50 text-blue-700' },
  telegram_voice: { Icon: VoiceIcon, label: 'Voice', className: 'border-violet-200 bg-violet-50 text-violet-700' },
  meeting_audio: { Icon: MeetingIcon, label: 'Meeting', className: 'border-teal-200 bg-teal-50 text-teal-700' },
} satisfies Record<TaskSource, { Icon: typeof TelegramIcon; label: string; className: string }>;

function SourceBadge({ source, compact }: { source: TaskSource; compact?: boolean }) {
  const { Icon, label, className } = sourceConfig[source];

  return (
    <span
      title={label}
      className={cn('inline-flex h-7 items-center justify-center gap-1.5 rounded-lg border px-2 text-xs font-bold leading-none', className, compact && 'h-6 gap-1 px-1.5 text-[11px]')}
    >
      <Icon className={cn('h-3.5 w-3.5', compact && 'h-3 w-3')} aria-hidden="true" />
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

function RangeFilter({ value, onChange }: { value: RangeKey; onChange: (value: RangeKey) => void }) {
  const [open, setOpen] = useState(false);
  const current = RANGES.find((item) => item.key === value) ?? RANGES[0];

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((previous) => !previous)}
        className="focus-ring flex h-11 w-full items-center justify-center gap-2 rounded-2xl border border-stone-200 bg-white px-3 text-sm font-semibold text-stone-800 transition hover:bg-stone-50"
      >
        <CalendarDays className="h-4 w-4 text-stone-500" />
        <span className="truncate">{current.label}</span>
        <ChevronDown className={cn('h-4 w-4 shrink-0 text-stone-400 transition-transform', open && 'rotate-180')} />
      </button>

      {open && (
        <>
          <button type="button" aria-hidden tabIndex={-1} className="fixed inset-0 z-10 cursor-default" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-[calc(100%+8px)] z-20 w-60 animate-scale-in rounded-2xl border border-stone-200 bg-white p-1.5 shadow-soft">
            {RANGES.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => {
                  onChange(item.key);
                  setOpen(false);
                }}
                className={cn(
                  'flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left text-sm font-medium transition-colors',
                  item.key === value ? 'bg-brand-50 text-brand-700' : 'text-stone-700 hover:bg-stone-50',
                )}
              >
                {item.label}
                {item.key === value && <Check className="h-4 w-4 shrink-0" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

const priorities: TaskPriority[] = ['low', 'medium', 'high', 'critical'];

function NewTaskModal({
  open,
  initialStatus,
  assignees,
  onClose,
  onCreate,
}: {
  open: boolean;
  initialStatus: TaskStatus;
  assignees: string[];
  onClose: () => void;
  onCreate: (input: { title: string; assignee: string; deadline: string; priority: TaskPriority; status: TaskStatus }) => void;
}) {
  const [title, setTitle] = useState('');
  const [assignee, setAssignee] = useState('');
  const [deadline, setDeadline] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');
  const [status, setStatus] = useState<TaskStatus>(initialStatus);

  useEffect(() => {
    if (open) {
      setTitle('');
      setAssignee('');
      setDeadline('');
      setPriority('medium');
      setStatus(initialStatus);
    }
  }, [open, initialStatus]);

  const canSubmit = title.trim().length > 0;

  function submit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    onCreate({ title, assignee, deadline, priority, status });
  }

  return (
    <Modal open={open} onClose={onClose} title="Новая задача" description="Создайте задачу вручную — она появится в списке и мини-канбане.">
      <form className="grid gap-4" onSubmit={submit}>
        <label className="grid gap-1.5 text-xs font-medium text-stone-500">
          Название
          <Input autoFocus value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Например: подготовить отчёт по спринту" />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-1.5 text-xs font-medium text-stone-500">
            Ответственный
            <Dropdown
              ariaLabel="Ответственный"
              value={assignee}
              onChange={setAssignee}
              options={[{ value: '', label: 'Не назначен' }, ...assignees.map((item) => ({ value: item, label: item }))]}
            />
          </div>
          <label className="grid gap-1.5 text-xs font-medium text-stone-500">
            Срок
            <Input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} />
          </label>
          <div className="grid gap-1.5 text-xs font-medium text-stone-500">
            Приоритет
            <Dropdown
              ariaLabel="Приоритет"
              value={priority}
              onChange={(value) => setPriority(value as TaskPriority)}
              options={priorities.map((item) => ({ value: item, label: priorityLabel[item] }))}
            />
          </div>
          <div className="grid gap-1.5 text-xs font-medium text-stone-500">
            Статус
            <Dropdown
              ariaLabel="Статус"
              value={status}
              onChange={(value) => setStatus(value as TaskStatus)}
              options={visibleStatuses.map((item) => ({ value: item, label: taskStatusLabel[item] }))}
            />
          </div>
        </div>

        <div className="mt-2 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose}>Отмена</Button>
          <Button type="submit" disabled={!canSubmit}>
            <Plus className="h-4 w-4" />
            Создать задачу
          </Button>
        </div>
      </form>
    </Modal>
  );
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bot, CalendarClock, CheckCircle2, Clock3, KanbanSquare, Plus, ShieldAlert, Sparkles } from 'lucide-react';
import { ReactNode, FormEvent, useMemo, useState } from 'react';
import { Employee, KomandusTask, TaskStatusV2 } from '../entities/saas/types';
import { getEmployees } from '../shared/api/employeesV2';
import { createKomandusTask, getKomandusTasks, moveKomandusTask } from '../shared/api/tasksV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { EmptyState } from '../shared/ui/EmptyState';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';
import { Textarea } from '../shared/ui/Textarea';

const columns: Array<{ key: TaskStatusV2; title: string; hint: string }> = [
  { key: 'PENDING_CONFIRMATION', title: 'На подтверждении', hint: 'низкая уверенность LLM или нужна проверка PM' },
  { key: 'ACCEPTED', title: 'Принято', hint: 'исполнитель подтвердил, ждет отправки на доску' },
  { key: 'TO_DO', title: 'К выполнению', hint: 'синхронизировано с рабочей колонкой' },
  { key: 'IN_PROGRESS', title: 'В работе', hint: 'исполнитель уже начал' },
  { key: 'REVIEW', title: 'Ревью', hint: 'нужна проверка менеджера' },
  { key: 'DONE', title: 'Готово', hint: 'завершено' },
];

const statusTone: Record<TaskStatusV2, 'neutral' | 'blue' | 'green' | 'amber' | 'red'> = {
  DETECTED: 'neutral',
  PENDING_CONFIRMATION: 'amber',
  ACCEPTED: 'blue',
  REJECTED: 'red',
  TO_DO: 'neutral',
  IN_PROGRESS: 'blue',
  REVIEW: 'amber',
  DONE: 'green',
  OVERDUE: 'red',
};

const statusLabel: Record<TaskStatusV2, string> = {
  DETECTED: 'Обнаружено',
  PENDING_CONFIRMATION: 'Подтверждение',
  ACCEPTED: 'Принято',
  REJECTED: 'Отклонено',
  TO_DO: 'К выполнению',
  IN_PROGRESS: 'В работе',
  REVIEW: 'Ревью',
  DONE: 'Готово',
  OVERDUE: 'Просрочено',
};

const moveTargets: TaskStatusV2[] = ['IN_PROGRESS', 'REVIEW', 'DONE', 'OVERDUE'];

function employeeName(employees: Employee[], id?: string | null) {
  return employees.find((employee) => employee.id === id)?.full_name ?? 'Не назначен';
}

export function SaasTasksPage() {
  const queryClient = useQueryClient();
  const tasksQuery = useQuery({ queryKey: ['v2', 'tasks'], queryFn: getKomandusTasks });
  const employeesQuery = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const employees = employeesQuery.data ?? [];
  const tasks = tasksQuery.data ?? [];
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [dueAt, setDueAt] = useState('');

  const createMutation = useMutation({
    mutationFn: () => createKomandusTask({ title, description: description || null, employee_id: employeeId || null, due_at: dueAt ? new Date(dueAt).toISOString() : null }),
    onSuccess: () => {
      setTitle('');
      setDescription('');
      setEmployeeId('');
      setDueAt('');
      queryClient.invalidateQueries({ queryKey: ['v2', 'tasks'] });
      queryClient.invalidateQueries({ queryKey: ['v2', 'analytics'] });
    },
  });

  const moveMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: TaskStatusV2 }) => moveKomandusTask(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2', 'tasks'] });
      queryClient.invalidateQueries({ queryKey: ['v2', 'analytics'] });
    },
  });

  const metrics = useMemo(() => ({
    total: tasks.length,
    pending: tasks.filter((task) => task.status === 'PENDING_CONFIRMATION').length,
    accepted: tasks.filter((task) => task.status === 'ACCEPTED').length,
    overdue: tasks.filter((task) => task.status === 'OVERDUE').length,
  }), [tasks]);

  function onCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <>
      <PageHeader
        eyebrow="Источник истины"
        title="Задачи Командуса"
        description="Витрина v2: задачи живут в Командусе, проходят подтверждение, валидируются state machine и затем синхронизируются с YouGile через фоновые события."
        actions={<Button form="create-task-form" type="submit" disabled={createMutation.isPending}><Plus className="h-4 w-4" />Создать</Button>}
      />

      <section className="grid gap-4 md:grid-cols-4">
        <Metric icon={<KanbanSquare />} label="Всего" value={metrics.total} tone="blue" />
        <Metric icon={<Clock3 />} label="Ждут подтверждения" value={metrics.pending} tone="amber" />
        <Metric icon={<CheckCircle2 />} label="Принято" value={metrics.accepted} tone="green" />
        <Metric icon={<ShieldAlert />} label="Просрочено" value={metrics.overdue} tone="red" />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="h-fit">
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-2xl bg-stone-900 p-3 text-white"><Sparkles className="h-5 w-5" /></div>
            <div>
              <h2 className="font-semibold text-stone-950">Быстрое создание</h2>
              <p className="mt-1 text-sm leading-6 text-stone-500">Ручные задачи сразу попадают в `TO_DO`; AI-задачи приходят через LLM pipeline.</p>
            </div>
          </div>
          <form id="create-task-form" className="space-y-4" onSubmit={onCreate}>
            <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Название задачи" required />
            <Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Описание, критерии готовности, контекст" />
            <Select value={employeeId} onChange={(event) => setEmployeeId(event.target.value)}>
              <option value="">Не назначать</option>
              {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}
            </Select>
            <Input type="datetime-local" value={dueAt} onChange={(event) => setDueAt(event.target.value)} />
            {createMutation.error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{createMutation.error.message}</p>}
          </form>
        </Card>

        <div className="min-w-0 space-y-4">
          {tasksQuery.isLoading && <Loader text="Загружаем задачи v2..." />}
          {tasksQuery.error && <ErrorState error={tasksQuery.error} />}
          {!tasksQuery.isLoading && !tasksQuery.error && tasks.length === 0 && <EmptyState title="Задач пока нет" text="Создайте первую задачу или подключите Telegram ingestion." />}
          <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-3">
            {columns.map((column) => (
              <TaskColumn key={column.key} column={column} tasks={tasks.filter((task) => task.status === column.key)} employees={employees} onMove={(id, status) => moveMutation.mutate({ id, status })} isMoving={moveMutation.isPending} />
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function Metric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: number; tone: 'blue' | 'green' | 'amber' | 'red' }) {
  const tones = { blue: 'bg-sky-50 text-sky-700', green: 'bg-emerald-50 text-emerald-700', amber: 'bg-amber-50 text-amber-700', red: 'bg-red-50 text-red-700' };
  return <Card className="flex items-center gap-4"><div className={`rounded-2xl p-3 ${tones[tone]}`}>{icon}</div><div><p className="text-sm text-stone-500">{label}</p><p className="text-3xl font-semibold text-stone-950">{value}</p></div></Card>;
}

function TaskColumn({ column, tasks, employees, onMove, isMoving }: { column: { key: TaskStatusV2; title: string; hint: string }; tasks: KomandusTask[]; employees: Employee[]; onMove: (id: string, status: TaskStatusV2) => void; isMoving: boolean }) {
  return (
    <Card className="bg-stone-50/70 p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div><h3 className="font-semibold text-stone-950">{column.title}</h3><p className="mt-1 text-xs leading-5 text-stone-500">{column.hint}</p></div>
        <Badge>{tasks.length}</Badge>
      </div>
      <div className="space-y-3">
        {tasks.map((task) => <TaskCard key={task.id} task={task} employees={employees} onMove={onMove} isMoving={isMoving} />)}
        {tasks.length === 0 && <div className="rounded-2xl border border-dashed border-stone-200 bg-white p-4 text-sm text-stone-400">Пусто</div>}
      </div>
    </Card>
  );
}

function TaskCard({ task, employees, onMove, isMoving }: { task: KomandusTask; employees: Employee[]; onMove: (id: string, status: TaskStatusV2) => void; isMoving: boolean }) {
  return (
    <article className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h4 className="font-semibold leading-6 text-stone-950">{task.title}</h4>
        <Badge tone={statusTone[task.status]}>{statusLabel[task.status]}</Badge>
      </div>
      {task.description && <p className="mb-3 line-clamp-3 text-sm leading-6 text-stone-500">{task.description}</p>}
      <div className="space-y-2 text-xs text-stone-500">
        <p>Исполнитель: <span className="font-medium text-stone-800">{employeeName(employees, task.employee_id)}</span></p>
        {task.due_at && <p className="flex items-center gap-1"><CalendarClock className="h-3.5 w-3.5" /> {new Date(task.due_at).toLocaleString('ru-RU')}</p>}
        {task.llm_confidence != null && <p className="flex items-center gap-1"><Bot className="h-3.5 w-3.5" /> LLM confidence {Math.round(task.llm_confidence * 100)}%</p>}
      </div>
      <Select className="mt-4" defaultValue="" disabled={isMoving} onChange={(event) => event.target.value && onMove(task.id, event.target.value as TaskStatusV2)}>
        <option value="">Переместить...</option>
        {moveTargets.map((status) => <option key={status} value={status}>{statusLabel[status]}</option>)}
      </Select>
    </article>
  );
}

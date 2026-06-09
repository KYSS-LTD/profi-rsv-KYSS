import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CalendarClock, KanbanSquare, MessageCircle, Pencil, PhoneCall, UserRound } from 'lucide-react';
import { ReactNode, useEffect, useState } from 'react';
import { KomandusTask, TaskStatusV2 } from '../entities/saas/types';
import { getEmployees } from '../shared/api/employeesV2';
import { getOrganizationChats } from '../shared/api/orgV2';
import { getKomandusTasks, moveKomandusTask, updateKomandusTask, UpdateTaskV2Payload } from '../shared/api/tasksV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { EmptyState } from '../shared/ui/EmptyState';
import { PageHeader } from '../shared/ui/PageHeader';
import { cn } from '../shared/lib/cn';
import { CallsView } from '../widgets/Meetings/CallsView';

const columns: Array<{ key: TaskStatusV2[]; title: string }> = [
  { key: ['DETECTED', 'PENDING_CONFIRMATION', 'ACCEPTED', 'TO_DO'], title: 'Новые' },
  { key: ['IN_PROGRESS'], title: 'В работе' },
  { key: ['REVIEW'], title: 'На проверке' },
  { key: ['DONE'], title: 'Завершено' },
];
const statusLabel: Record<TaskStatusV2, string> = {
  DETECTED: 'Обнаружена',
  PENDING_CONFIRMATION: 'На подтверждении',
  ACCEPTED: 'Принята',
  REJECTED: 'Отклонена',
  TO_DO: 'К выполнению',
  IN_PROGRESS: 'В работе',
  REVIEW: 'На проверке',
  DONE: 'Завершена',
  OVERDUE: 'Просрочена',
};
const next: Partial<Record<TaskStatusV2, TaskStatusV2>> = {
  DETECTED: 'IN_PROGRESS',
  PENDING_CONFIRMATION: 'IN_PROGRESS',
  ACCEPTED: 'IN_PROGRESS',
  TO_DO: 'IN_PROGRESS',
  IN_PROGRESS: 'REVIEW',
  REVIEW: 'DONE',
};

type EditForm = { title: string; description: string; employee_id: string; due_at: string };

export function SaasTasksPage() {
  const queryClient = useQueryClient();
  const [view, setView] = useState<'calls' | 'kanban'>('calls');
  const { data: tasks = [] } = useQuery({ queryKey: ['v2', 'tasks'], queryFn: getKomandusTasks });
  const { data: employees = [] } = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const { data: chats = [] } = useQuery({ queryKey: ['v2', 'chats'], queryFn: getOrganizationChats });
  const [selected, setSelected] = useState<KomandusTask | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<EditForm>({ title: '', description: '', employee_id: '', due_at: '' });

  useEffect(() => {
    if (selected) {
      setEditing(false);
      setForm({
        title: selected.title,
        description: selected.description ?? '',
        employee_id: selected.employee_id ?? '',
        due_at: selected.due_at ? selected.due_at.slice(0, 16) : '',
      });
    }
  }, [selected]);

  const moveMutation = useMutation({ mutationFn: ({ id, status }: { id: string; status: TaskStatusV2 }) => moveKomandusTask(id, status), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'tasks'] }) });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: UpdateTaskV2Payload }) => updateKomandusTask(id, payload),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['v2', 'tasks'] });
      setSelected(updated);
      setEditing(false);
    },
  });

  const employeeName = (id?: string | null) => employees.find((employee) => employee.id === id)?.full_name ?? 'Не назначен';
  const chatTitle = (task: KomandusTask) => chats.find((chat) => chat.id === task.organization_chat_id || chat.telegram_chat_id === task.source_chat_id)?.title ?? (task.source_chat_id ? `Чат ${task.source_chat_id}` : 'Без чата');

  const saveEdit = () => {
    if (!selected) return;
    updateMutation.mutate({
      id: selected.id,
      payload: {
        title: form.title.trim() || selected.title,
        description: form.description.trim() ? form.description.trim() : null,
        employee_id: form.employee_id || null,
        due_at: form.due_at ? new Date(form.due_at).toISOString() : null,
      },
    });
  };

  return <><PageHeader eyebrow="Канбан Командуса" title="Задачи" description="Собственный канбан: Командус остаётся источником истины, а YouGile — внешней синхронизируемой доской." />
    <div className="mb-6 inline-flex rounded-2xl border border-stone-200 bg-white p-1">
      <TabButton active={view === 'calls'} onClick={() => setView('calls')}><PhoneCall className="h-4 w-4" />Созвоны AI</TabButton>
      <TabButton active={view === 'kanban'} onClick={() => setView('kanban')}><KanbanSquare className="h-4 w-4" />Канбан</TabButton>
    </div>
    {view === 'calls' && <CallsView />}
    {view === 'kanban' && <>
    <section className="grid gap-4 xl:grid-cols-4">{columns.map((column) => <div key={column.title} className="rounded-3xl border border-stone-200 bg-white/70 p-3"><div className="mb-3 flex items-center justify-between px-2"><h2 className="font-semibold text-stone-950">{column.title}</h2><Badge tone="neutral">{tasks.filter((task) => column.key.includes(task.status)).length}</Badge></div><div className="space-y-3">{tasks.filter((task) => column.key.includes(task.status)).map((task) => <button key={task.id} onClick={() => setSelected(task)} className="block w-full rounded-2xl border border-stone-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"><div className="mb-3 flex items-start justify-between gap-3"><h3 className="font-semibold text-stone-950">{task.title}</h3><Badge tone={task.status === 'OVERDUE' ? 'red' : 'blue'}>{statusLabel[task.status]}</Badge></div><p className="line-clamp-2 text-sm text-stone-500">{task.description || task.ai_summary || 'Описание появится после анализа AI.'}</p><div className="mt-4 space-y-2 text-xs text-stone-500"><p className="flex items-center gap-2"><UserRound className="h-3.5 w-3.5" />{employeeName(task.employee_id)}</p><p className="flex items-center gap-2"><MessageCircle className="h-3.5 w-3.5" />{chatTitle(task)}</p><p className="flex items-center gap-2"><CalendarClock className="h-3.5 w-3.5" />{task.due_at ? new Date(task.due_at).toLocaleString('ru-RU') : 'Без дедлайна'}</p></div>{next[task.status] && <Button className="mt-4 w-full" variant="secondary" onClick={(event) => { event.stopPropagation(); moveMutation.mutate({ id: task.id, status: next[task.status]! }); }}>Дальше</Button>}</button>)}</div></div>)}</section>{!tasks.length && <EmptyState title="Задач пока нет" text="Они появятся из Telegram AI или ручного создания API." />}
    {selected && <div className="fixed inset-0 z-40 bg-stone-950/30" onClick={() => setSelected(null)}><aside className="ml-auto h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
      <div className="mb-5 flex items-start justify-between gap-4"><div><Badge tone="blue">{statusLabel[selected.status]}</Badge><h2 className="mt-3 text-2xl font-semibold text-stone-950">{selected.title}</h2></div><div className="flex gap-2">{!editing && <Button variant="secondary" onClick={() => setEditing(true)}><Pencil className="h-4 w-4" />Изменить</Button>}<Button variant="ghost" onClick={() => setSelected(null)}>Закрыть</Button></div></div>
      {editing ? <div className="space-y-4">
        <Field label="Название"><input className={inputClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></Field>
        <Field label="Описание"><textarea className={inputClass} rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
        <Field label="Исполнитель"><select className={inputClass} value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}><option value="">Не назначен</option>{employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}</select></Field>
        <Field label="Дедлайн"><input type="datetime-local" className={inputClass} value={form.due_at} onChange={(e) => setForm({ ...form, due_at: e.target.value })} /></Field>
        <div className="flex gap-2"><Button onClick={saveEdit} disabled={updateMutation.isPending}>Сохранить</Button><Button variant="ghost" onClick={() => setEditing(false)}>Отмена</Button></div>
        {updateMutation.isError && <p className="text-sm text-red-600">Не удалось сохранить. Проверьте права доступа.</p>}
      </div> : <>
        <DrawerItem label="Описание" value={selected.description || 'Нет описания'} />
        <DrawerItem label="Источник" value={selected.llm_model ? `AI ${selected.llm_model}` : 'manual'} />
        <DrawerItem label="Чат" value={chatTitle(selected)} />
        <DrawerItem label="Исполнитель" value={employeeName(selected.employee_id)} />
        <DrawerItem label="Дедлайн" value={selected.due_at ? new Date(selected.due_at).toLocaleString('ru-RU') : 'Не указан'} />
        <DrawerItem label="Как AI понял задачу" value={selected.ai_summary || selected.description || 'Нет AI-резюме'} />
        <DrawerItem label="Исходное сообщение" value={selected.source_excerpt || 'Фрагмент не сохранен'} />
        <DrawerItem label="История изменений" value={`Создано: ${new Date(selected.created_at).toLocaleString('ru-RU')}\nОбновлено: ${new Date(selected.updated_at).toLocaleString('ru-RU')}`} />
      </>}
    </aside></div>}
    </>}
  </>;
}

const inputClass = 'w-full rounded-2xl border border-stone-300 bg-white px-4 py-2 text-sm text-stone-900 outline-none focus:border-stone-900';

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: ReactNode }) {
  return <button type="button" onClick={onClick} className={cn('focus-ring inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition', active ? 'bg-stone-900 text-white' : 'text-stone-500 hover:text-stone-900')}>{children}</button>;
}
function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="block"><span className="mb-1 block text-xs uppercase tracking-[0.16em] text-stone-400">{label}</span>{children}</label>; }
function DrawerItem({ label, value }: { label: string; value: string }) { return <div className="mb-4 rounded-2xl bg-stone-50 p-4"><p className="text-xs uppercase tracking-[0.16em] text-stone-400">{label}</p><p className="mt-2 whitespace-pre-line text-sm leading-6 text-stone-800">{value}</p></div>; }

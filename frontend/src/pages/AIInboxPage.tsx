import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Bot, Check, Pencil, Trash2 } from 'lucide-react';
import { getEmployees } from '../shared/api/employeesV2';
import { confirmKomandusTask, getKomandusTasks } from '../shared/api/tasksV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { EmptyState } from '../shared/ui/EmptyState';
import { PageHeader } from '../shared/ui/PageHeader';

export function AIInboxPage() {
  const client = useQueryClient();
  const { data: tasks = [] } = useQuery({ queryKey: ['v2', 'tasks'], queryFn: getKomandusTasks });
  const { data: employees = [] } = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const mutation = useMutation({ mutationFn: ({ id, approved, reason }: { id: string; approved: boolean; reason?: string }) => confirmKomandusTask(id, approved, reason), onSuccess: () => client.invalidateQueries({ queryKey: ['v2', 'tasks'] }) });
  const inbox = tasks.filter((task) => task.status === 'PENDING_CONFIRMATION' || task.status === 'DETECTED');
  const name = (id?: string | null) => employees.find((employee) => employee.id === id)?.full_name ?? 'Не назначен';
  return <><PageHeader eyebrow="AI Inbox" title="Входящие AI" description="Очередь задач, которые AI извлек из Telegram. 85%+ отправляются сотруднику автоматически, остальные требуют проверки." />
    <section className="grid gap-4 xl:grid-cols-2">{inbox.map((task) => <Card key={task.id}>
      <div className="mb-4 flex items-start justify-between gap-4"><div className="flex items-center gap-3"><div className="rounded-2xl bg-stone-900 p-3 text-white"><Bot className="h-5 w-5" /></div><div><h2 className="font-semibold text-stone-950">{task.title}</h2><p className="text-sm text-stone-500">Уверенность {Math.round((task.llm_confidence ?? 0) * 100)}%</p></div></div><Badge tone={(task.llm_confidence ?? 0) >= 0.85 ? 'green' : 'amber'}>{(task.llm_confidence ?? 0) >= 0.85 ? 'auto' : 'review'}</Badge></div>
      <div className="grid gap-3 text-sm md:grid-cols-2"><Info label="Исходное сообщение" value={task.source_excerpt || 'Нет фрагмента'} /><Info label="Что понял AI" value={task.ai_summary || task.description || task.title} /><Info label="Исполнитель" value={name(task.employee_id)} /><Info label="Срок" value={task.due_at ? new Date(task.due_at).toLocaleString('ru-RU') : 'Не указан'} /></div>
      <div className="mt-5 flex flex-wrap gap-2"><Button onClick={() => mutation.mutate({ id: task.id, approved: true })}><Check className="h-4 w-4" />Подтвердить</Button><Button variant="secondary"><Pencil className="h-4 w-4" />Изменить</Button><Button variant="ghost" onClick={() => mutation.mutate({ id: task.id, approved: false, reason: 'Удалено менеджером' })}><Trash2 className="h-4 w-4" />Удалить</Button></div>
    </Card>)}{!inbox.length && <EmptyState title="Очередь пуста" text="Новые AI-задачи появятся после анализа подключенных Telegram-чатов." />}</section></>;
}
function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl bg-stone-50 p-4"><p className="text-xs uppercase tracking-[0.16em] text-stone-400">{label}</p><p className="mt-2 text-stone-800">{value}</p></div>; }

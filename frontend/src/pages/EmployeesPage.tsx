import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AtSign, BadgeCheck, Copy, MessageCircle, Plus, Shield, Trash2, UserRoundCheck } from 'lucide-react';
import { FormEvent, ReactNode, useMemo, useState } from 'react';
import { Employee, Role } from '../entities/saas/types';
import { createEmployee, deactivateEmployee, deleteEmployee, getEmployees, updateEmployee } from '../shared/api/employeesV2';
import { getDepartments, getTeams } from '../shared/api/orgV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { EmptyState } from '../shared/ui/EmptyState';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';

const roles: Role[] = ['MANAGER', 'DEPARTMENT_MANAGER', 'PRODUCT_MANAGER', 'EMPLOYEE', 'VIEWER'];
const roleLabel: Record<Role, string> = { SUPER_ADMIN: 'Super Admin', MANAGER: 'Менеджер', DEPARTMENT_MANAGER: 'Руководитель отдела', PRODUCT_MANAGER: 'Product Manager', EMPLOYEE: 'Сотрудник', VIEWER: 'Наблюдатель' };

export function EmployeesPage() {
  const queryClient = useQueryClient();
  const employeesQuery = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const departmentsQuery = useQuery({ queryKey: ['v2', 'departments'], queryFn: getDepartments });
  const teamsQuery = useQuery({ queryKey: ['v2', 'teams'], queryFn: () => getTeams() });
  const employees = employeesQuery.data ?? [];
  const departments = departmentsQuery.data ?? [];
  const teams = teamsQuery.data ?? [];
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<Role>('EMPLOYEE');
  const [departmentId, setDepartmentId] = useState('');
  const [teamId, setTeamId] = useState('');
  const [position, setPosition] = useState('');
  const [telegramUsername, setTelegramUsername] = useState('');
  const [invite, setInvite] = useState('');

  const stats = useMemo(() => ({ total: employees.length, active: employees.filter((e) => e.is_active).length, telegram: employees.filter((e) => e.telegram_status === 'CONNECTED').length, managers: employees.filter((e) => ['MANAGER', 'DEPARTMENT_MANAGER', 'PRODUCT_MANAGER'].includes(e.role)).length }), [employees]);
  const createMutation = useMutation({ mutationFn: () => createEmployee({ full_name: fullName, email: email || null, role, department_id: departmentId || null, team_id: teamId || null, position: position || null, telegram_username: telegramUsername || null }), onSuccess: (employee) => { setFullName(''); setEmail(''); setRole('EMPLOYEE'); setDepartmentId(''); setTeamId(''); setPosition(''); setTelegramUsername(''); setInvite(`Здравствуйте! Ваш аккаунт Командус создан.\nВойти: ${window.location.origin}\nEmail: ${employee.email}\nПароль: ${employee.generated_password}\nНапишите боту /start для привязки Telegram.`); queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }); } });
  const updateMutation = useMutation({ mutationFn: ({ id, payload }: { id: string; payload: Partial<Employee> }) => updateEmployee(id, payload), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }) });
  const deactivateMutation = useMutation({ mutationFn: deactivateEmployee, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }) });
  const deleteMutation = useMutation({ mutationFn: deleteEmployee, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }) });
  const departmentName = (id?: string | null) => departments.find((d) => d.id === id)?.name ?? 'Без отдела';
  const teamName = (id?: string | null) => teams.find((t) => t.id === id)?.name ?? 'Без команды';
  function onCreate(event: FormEvent) { event.preventDefault(); createMutation.mutate(); }

  return <><PageHeader eyebrow="Команда" title="Команда" description="Карточки сотрудников: роль, отдел, команда, нагрузка, эффективность и безопасная Telegram-привязка через @username и /start." actions={<Button form="employee-form" type="submit" disabled={createMutation.isPending}><Plus className="h-4 w-4" />Добавить</Button>} />
    <section className="grid gap-4 md:grid-cols-4"><Stat icon={<UserRoundCheck />} label="Всего" value={stats.total} /><Stat icon={<BadgeCheck />} label="Активны" value={stats.active} /><Stat icon={<MessageCircle />} label="Telegram связан" value={stats.telegram} /><Stat icon={<Shield />} label="Руководители" value={stats.managers} /></section>
    <section className="mt-6 grid gap-6 xl:grid-cols-[420px_1fr]"><Card className="h-fit"><h2 className="font-semibold text-stone-950">Новый сотрудник</h2><p className="mt-2 text-sm leading-6 text-stone-500">Telegram ID запрещен: менеджер вводит @username, а бот сам привязывает аккаунт после /start.</p><form id="employee-form" className="mt-5 space-y-4" onSubmit={onCreate}><Input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="ФИО" required /><Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email@company.com" required /><Input value={position} onChange={(e) => setPosition(e.target.value)} placeholder="Должность" /><Select value={role} onChange={(e) => setRole(e.target.value as Role)}>{roles.map((item) => <option key={item} value={item}>{roleLabel[item]}</option>)}</Select><Select value={departmentId} onChange={(e) => { setDepartmentId(e.target.value); setTeamId(''); }}><option value="">Отдел</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select><Select value={teamId} onChange={(e) => setTeamId(e.target.value)}><option value="">Команда</option>{teams.filter((t) => !departmentId || t.department_id === departmentId).map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}</Select><Input value={telegramUsername} onChange={(e) => setTelegramUsername(e.target.value)} placeholder="@ivan_petrov" />{createMutation.error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{createMutation.error.message}</p>}</form>{invite && <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900"><p className="whitespace-pre-line">{invite}</p><Button className="mt-3" variant="secondary" onClick={() => navigator.clipboard.writeText(invite)}><Copy className="h-4 w-4" />Скопировать приглашение</Button></div>}</Card>
      <div className="space-y-4">{employeesQuery.isLoading && <Loader text="Загружаем сотрудников..." />}{employeesQuery.error && <ErrorState error={employeesQuery.error} />}{!employeesQuery.isLoading && !employeesQuery.error && employees.length === 0 && <EmptyState title="Сотрудников пока нет" text="Добавьте команду, чтобы назначать задачи и строить аналитику." />}<div className="grid gap-4 lg:grid-cols-2">{employees.map((employee) => <Card key={employee.id} className={!employee.is_active ? 'opacity-60' : ''}><div className="flex items-start gap-4"><div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-stone-100 text-lg font-semibold text-stone-700">{employee.full_name.slice(0, 1)}</div><div className="min-w-0 flex-1"><h3 className="truncate text-lg font-semibold text-stone-950">{employee.full_name}</h3><p className="truncate text-sm text-stone-500">{employee.position || 'Должность не указана'}</p><p className="mt-1 flex items-center gap-1 truncate text-sm text-stone-500"><AtSign className="h-3.5 w-3.5" />{employee.telegram_username || employee.email}</p></div><Badge tone={employee.telegram_status === 'CONNECTED' ? 'green' : 'amber'}>{employee.telegram_status === 'CONNECTED' ? 'Telegram подключен' : 'Ожидает'}</Badge></div><div className="mt-5 grid gap-3 sm:grid-cols-2"><Info label="Роль" value={roleLabel[employee.role]} /><Info label="Отдел" value={departmentName(employee.department_id)} /><Info label="Команда" value={teamName(employee.team_id)} /><Info label="Эффективность" value="Рассчитывается" /></div><div className="mt-5 flex flex-wrap gap-2"><Button variant="secondary" disabled={!employee.is_active || deactivateMutation.isPending} onClick={() => deactivateMutation.mutate(employee.id)}>Деактивировать</Button><Button variant="danger" disabled={deleteMutation.isPending} onClick={() => window.confirm('Удалить сотрудника?') && deleteMutation.mutate(employee.id)}><Trash2 className="h-4 w-4" />Удалить</Button></div></Card>)}</div></div></section></>;
}
function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) { return <Card className="flex items-center gap-4"><div className="rounded-2xl bg-stone-100 p-3 text-stone-700">{icon}</div><div><p className="text-sm text-stone-500">{label}</p><p className="text-3xl font-semibold text-stone-950">{value}</p></div></Card>; }
function Info({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl bg-stone-50 p-3"><p className="text-xs text-stone-400">{label}</p><p className="font-medium text-stone-800">{value}</p></div>; }

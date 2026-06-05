import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AtSign, BadgeCheck, MessageCircle, Plus, Shield, Trash2, UserRoundCheck } from 'lucide-react';
import { ReactNode, FormEvent, useMemo, useState } from 'react';
import { Employee, Role } from '../entities/saas/types';
import { createEmployee, deactivateEmployee, deleteEmployee, getEmployees, updateEmployee } from '../shared/api/employeesV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { EmptyState } from '../shared/ui/EmptyState';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';

const roles: Role[] = ['MANAGER', 'PRODUCT_MANAGER', 'EMPLOYEE', 'VIEWER'];
const roleLabel: Record<Role, string> = {
  SUPER_ADMIN: 'Super Admin',
  MANAGER: 'Менеджер',
  PRODUCT_MANAGER: 'Product Manager',
  EMPLOYEE: 'Сотрудник',
  VIEWER: 'Наблюдатель',
};

export function EmployeesPage() {
  const queryClient = useQueryClient();
  const employeesQuery = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const employees = employeesQuery.data ?? [];
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<Role>('EMPLOYEE');
  const [telegramId, setTelegramId] = useState('');

  const stats = useMemo(() => ({
    total: employees.length,
    active: employees.filter((employee) => employee.is_active).length,
    telegram: employees.filter((employee) => employee.telegram_id).length,
    managers: employees.filter((employee) => employee.role === 'MANAGER' || employee.role === 'PRODUCT_MANAGER').length,
  }), [employees]);

  const createMutation = useMutation({
    mutationFn: () => createEmployee({ full_name: fullName, email: email || null, role, telegram_id: telegramId ? Number(telegramId) : null }),
    onSuccess: () => {
      setFullName('');
      setEmail('');
      setRole('EMPLOYEE');
      setTelegramId('');
      queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Partial<Employee> }) => updateEmployee(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateEmployee,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteEmployee,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'employees'] }),
  });

  function onCreate(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <>
      <PageHeader
        eyebrow="RBAC и команда"
        title="Сотрудники"
        description="Управляйте ролями, Telegram ID и активностью сотрудников внутри текущей организации. Все действия логируются AuditService на backend."
        actions={<Button form="employee-form" type="submit" disabled={createMutation.isPending}><Plus className="h-4 w-4" />Добавить</Button>}
      />

      <section className="grid gap-4 md:grid-cols-4">
        <Stat icon={<UserRoundCheck />} label="Всего" value={stats.total} />
        <Stat icon={<BadgeCheck />} label="Активны" value={stats.active} />
        <Stat icon={<MessageCircle />} label="Telegram связан" value={stats.telegram} />
        <Stat icon={<Shield />} label="PM/Manager" value={stats.managers} />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[420px_1fr]">
        <Card className="h-fit">
          <h2 className="font-semibold text-stone-950">Новый сотрудник</h2>
          <p className="mt-2 text-sm leading-6 text-stone-500">Пользователи не регистрируются сами — менеджер создает профиль и назначает роль.</p>
          <form id="employee-form" className="mt-5 space-y-4" onSubmit={onCreate}>
            <Input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="ФИО" required />
            <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="email@company.com" />
            <Select value={role} onChange={(event) => setRole(event.target.value as Role)}>{roles.map((item) => <option key={item} value={item}>{roleLabel[item]}</option>)}</Select>
            <Input inputMode="numeric" value={telegramId} onChange={(event) => setTelegramId(event.target.value)} placeholder="Telegram ID" />
            {createMutation.error && <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{createMutation.error.message}</p>}
          </form>
        </Card>

        <div className="space-y-4">
          {employeesQuery.isLoading && <Loader text="Загружаем сотрудников..." />}
          {employeesQuery.error && <ErrorState error={employeesQuery.error} />}
          {!employeesQuery.isLoading && !employeesQuery.error && employees.length === 0 && <EmptyState title="Сотрудников пока нет" text="Добавьте команду, чтобы назначать задачи и строить аналитику." />}
          <div className="grid gap-4 lg:grid-cols-2">
            {employees.map((employee) => (
              <Card key={employee.id} className={!employee.is_active ? 'opacity-60' : ''}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="truncate text-lg font-semibold text-stone-950">{employee.full_name}</h3>
                    <p className="mt-1 flex items-center gap-1 truncate text-sm text-stone-500"><AtSign className="h-3.5 w-3.5" /> {employee.email || 'email не указан'}</p>
                  </div>
                  <Badge tone={employee.is_active ? 'green' : 'red'}>{employee.is_active ? 'Активен' : 'Отключен'}</Badge>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  <label className="space-y-1 text-xs font-medium text-stone-500">Роль<Select value={employee.role} onChange={(event) => updateMutation.mutate({ id: employee.id, payload: { role: event.target.value as Role } })}>{(['MANAGER', 'PRODUCT_MANAGER', 'EMPLOYEE', 'VIEWER'] as Role[]).map((item) => <option key={item} value={item}>{roleLabel[item]}</option>)}</Select></label>
                  <label className="space-y-1 text-xs font-medium text-stone-500">Telegram<Input defaultValue={employee.telegram_id ?? ''} onBlur={(event) => updateMutation.mutate({ id: employee.id, payload: { telegram_id: event.target.value ? Number(event.target.value) : null } })} /></label>
                </div>
                <div className="mt-5 flex flex-wrap gap-2">
                  <Button variant="secondary" disabled={!employee.is_active || deactivateMutation.isPending} onClick={() => deactivateMutation.mutate(employee.id)}>Деактивировать</Button>
                  <Button variant="danger" disabled={deleteMutation.isPending} onClick={() => window.confirm('Удалить сотрудника?') && deleteMutation.mutate(employee.id)}><Trash2 className="h-4 w-4" />Удалить</Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function Stat({ icon, label, value }: { icon: ReactNode; label: string; value: number }) {
  return <Card className="flex items-center gap-4"><div className="rounded-2xl bg-stone-100 p-3 text-stone-700">{icon}</div><div><p className="text-sm text-stone-500">{label}</p><p className="text-3xl font-semibold text-stone-950">{value}</p></div></Card>;
}

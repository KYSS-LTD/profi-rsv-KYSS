import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Building2, Plus, UsersRound } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { createDepartment, createTeam, getDepartments, getTeams } from '../shared/api/orgV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';
import { Textarea } from '../shared/ui/Textarea';

export function DepartmentsPage() {
  const client = useQueryClient();
  const { data: departments = [] } = useQuery({ queryKey: ['v2', 'departments'], queryFn: getDepartments });
  const { data: teams = [] } = useQuery({ queryKey: ['v2', 'teams'], queryFn: () => getTeams() });
  const [departmentName, setDepartmentName] = useState('');
  const [description, setDescription] = useState('');
  const [teamName, setTeamName] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const depMutation = useMutation({ mutationFn: () => createDepartment({ name: departmentName, description }), onSuccess: () => { setDepartmentName(''); setDescription(''); client.invalidateQueries({ queryKey: ['v2', 'departments'] }); } });
  const teamMutation = useMutation({ mutationFn: () => createTeam({ department_id: departmentId, name: teamName }), onSuccess: () => { setTeamName(''); client.invalidateQueries({ queryKey: ['v2', 'teams'] }); } });
  function createDep(e: FormEvent) { e.preventDefault(); depMutation.mutate(); }
  function createTm(e: FormEvent) { e.preventDefault(); teamMutation.mutate(); }
  return <><PageHeader eyebrow="Структура организации" title="Отделы" description="Организация → отделы → команды → сотрудники → Telegram-чаты. Эта структура используется в процессах AI и правах доступа." />
    <section className="grid gap-6 xl:grid-cols-[1fr_420px]">
      <div className="grid gap-4 md:grid-cols-2">{departments.map((department) => <Card key={department.id}><div className="mb-4 flex items-start justify-between"><div className="flex items-center gap-3"><div className="rounded-2xl bg-stone-100 p-3 text-stone-700"><Building2 className="h-5 w-5" /></div><div><h2 className="font-semibold text-stone-950">{department.name}</h2><p className="text-sm text-stone-500">{department.description || 'Без описания'}</p></div></div><Badge tone={department.overdue_count ? 'red' : 'green'}>{department.efficiency}%</Badge></div><div className="grid grid-cols-3 gap-2 text-center"><K label="Сотрудники" value={department.employee_count} /><K label="Задачи" value={department.task_count} /><K label="Просрочки" value={department.overdue_count} /></div><div className="mt-4 flex flex-wrap gap-2">{teams.filter((team) => team.department_id === department.id).map((team) => <Badge key={team.id} tone="blue">{team.name}</Badge>)}</div></Card>)}</div>
      <div className="space-y-6"><Card><h2 className="mb-4 font-semibold text-stone-950">Создать отдел</h2><form className="space-y-3" onSubmit={createDep}><Input value={departmentName} onChange={(e) => setDepartmentName(e.target.value)} placeholder="Продажи / Маркетинг / Разработка" required /><Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Описание" /><Button type="submit"><Plus className="h-4 w-4" />Добавить отдел</Button></form></Card><Card><h2 className="mb-4 font-semibold text-stone-950">Создать команду</h2><form className="space-y-3" onSubmit={createTm}><Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)} required><option value="">Выберите отдел</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select><Input value={teamName} onChange={(e) => setTeamName(e.target.value)} placeholder="Backend / Frontend / QA" required /><Button type="submit"><UsersRound className="h-4 w-4" />Добавить команду</Button></form></Card></div>
    </section></>;
}
function K({ label, value }: { label: string; value: number }) { return <div className="rounded-2xl bg-stone-50 p-3"><p className="text-xl font-semibold text-stone-950">{value}</p><p className="text-xs text-stone-500">{label}</p></div>; }

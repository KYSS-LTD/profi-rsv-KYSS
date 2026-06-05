import { useMutation, useQuery } from '@tanstack/react-query';
import { CheckCircle2, KeyRound, MessageCircle, Send, UsersRound } from 'lucide-react';
import { useState } from 'react';
import { verifyYouGile } from '../shared/api/boardsV2';
import { getEmployees } from '../shared/api/employeesV2';
import { createTelegramConnectCode, getDepartments, getOrganizationChats } from '../shared/api/orgV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';

export function SetupWizardPage() {
  const [step, setStep] = useState(1);
  const [departmentId, setDepartmentId] = useState('');
  const [token, setToken] = useState('');
  const { data: departments = [] } = useQuery({ queryKey: ['v2', 'departments'], queryFn: getDepartments });
  const { data: chats = [] } = useQuery({ queryKey: ['v2', 'chats'], queryFn: getOrganizationChats });
  const { data: employees = [] } = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const codeMutation = useMutation({ mutationFn: () => createTelegramConnectCode(departmentId || null) });
  const yougileMutation = useMutation({ mutationFn: () => verifyYouGile(token) });
  return <><PageHeader eyebrow="Setup Wizard" title="Первичная настройка Командуса" description="5 шагов после регистрации: Telegram, сотрудники, YouGile, выбор доски и маппинг колонок." />
    <div className="mb-6 flex flex-wrap gap-2">{[1,2,3,4,5].map((n) => <Button key={n} variant={step === n ? 'primary' : 'secondary'} onClick={() => setStep(n)}>Шаг {n}</Button>)}</div>
    {step === 1 && <Card><WizardTitle icon={<MessageCircle />} title="Подключение Telegram-чата" /><div className="grid gap-4 md:grid-cols-[1fr_auto]"><Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}><option value="">Отдел для чата</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select><Button onClick={() => codeMutation.mutate()}><Send className="h-4 w-4" />Подключить чат</Button></div>{codeMutation.data && <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-5"><p className="text-3xl font-semibold text-stone-950">{codeMutation.data.code}</p><ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-stone-700">{codeMutation.data.instruction.map((item) => <li key={item}>{item}</li>)}</ol></div>}<div className="mt-5 space-y-2">{chats.map((chat) => <div key={chat.id} className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3"><span>{chat.title}</span><Badge tone={chat.ai_enabled ? 'green' : 'neutral'}>{chat.ai_enabled ? 'AI включен' : 'AI выключен'}</Badge></div>)}</div></Card>}
    {step === 2 && <Card><WizardTitle icon={<UsersRound />} title="Сотрудники" /><p className="text-sm text-stone-500">Telegram ID больше не вводится вручную. Добавьте ФИО, email, роль, отдел, команду и @username на странице «Команда».</p><div className="mt-5 grid gap-3 md:grid-cols-3">{employees.map((e) => <div key={e.id} className="rounded-2xl bg-stone-50 p-4"><p className="font-medium">{e.full_name}</p><p className="text-sm text-stone-500">{e.telegram_username}</p><Badge tone={e.telegram_status === 'CONNECTED' ? 'green' : 'amber'}>{e.telegram_status === 'CONNECTED' ? 'Подключен' : 'Ожидает подключения'}</Badge></div>)}</div></Card>}
    {step === 3 && <Card><WizardTitle icon={<KeyRound />} title="YouGile API Token" /><div className="flex gap-3"><Input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="API Token" /><Button onClick={() => yougileMutation.mutate()}>Проверить токен</Button></div>{yougileMutation.data && <p className="mt-4 text-sm text-emerald-700">Токен проверен, интеграция создана.</p>}</Card>}
    {step === 4 && <Card><WizardTitle icon={<CheckCircle2 />} title="Выбор проекта и доски" /><p className="text-sm text-stone-500">После проверки YouGile backend получает проекты, доски, колонки и пользователей. Выберите рабочую доску в интеграциях.</p></Card>}
    {step === 5 && <Card><WizardTitle icon={<CheckCircle2 />} title="Маппинг колонок" /><div className="grid gap-3 md:grid-cols-4">{['To Do','In Progress','Review','Done'].map((item) => <div key={item} className="rounded-2xl bg-stone-50 p-4 text-center font-medium">{item}</div>)}</div></Card>}
  </>;
}
function WizardTitle({ icon, title }: { icon: JSX.Element; title: string }) { return <div className="mb-5 flex items-center gap-3"><div className="rounded-2xl bg-stone-900 p-3 text-white">{icon}</div><h2 className="font-semibold text-stone-950">{title}</h2></div>; }

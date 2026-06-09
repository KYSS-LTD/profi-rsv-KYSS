import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle2, GitBranch, KeyRound, MessageCircle, Send, UsersRound } from 'lucide-react';
import { useState } from 'react';
import { verifyYouGile } from '../shared/api/boardsV2';
import { getEmployees } from '../shared/api/employeesV2';
import { confirmHierarchyMode, createTelegramConnectCode, getDepartments, getOrganizationChats, getOrganizationMode, getTaskSources, startHierarchyWizard, updateHierarchyWizard } from '../shared/api/orgV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';
import { PageHeader } from '../shared/ui/PageHeader';
import { Select } from '../shared/ui/Select';

export function SetupWizardPage() {
  const queryClient = useQueryClient();
  const [step, setStep] = useState(1);
  const [departmentId, setDepartmentId] = useState('');
  const [token, setToken] = useState('');
  const { data: mode } = useQuery({ queryKey: ['v2', 'org', 'mode'], queryFn: getOrganizationMode });
  const { data: departments = [] } = useQuery({ queryKey: ['v2', 'departments'], queryFn: getDepartments });
  const { data: chats = [] } = useQuery({ queryKey: ['v2', 'chats'], queryFn: getOrganizationChats });
  const { data: sources = [] } = useQuery({ queryKey: ['v2', 'task-sources'], queryFn: getTaskSources });
  const { data: employees = [] } = useQuery({ queryKey: ['v2', 'employees'], queryFn: getEmployees });
  const codeMutation = useMutation({ mutationFn: () => createTelegramConnectCode(departmentId || null), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'task-sources'] }) });
  const yougileMutation = useMutation({ mutationFn: () => verifyYouGile(token) });
  const startWizardMutation = useMutation({ mutationFn: startHierarchyWizard, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'org', 'mode'] }) });
  const updateWizardMutation = useMutation({ mutationFn: updateHierarchyWizard, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'org', 'mode'] }) });
  const confirmWizardMutation = useMutation({ mutationFn: confirmHierarchyMode, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['v2', 'org', 'mode'] }) });
  const wizardState = (mode?.hierarchy_setup_state ?? {}) as Record<string, boolean | number>;

  return <><PageHeader eyebrow="Настройки → Структура организации" title="Настройки Командуса" description="Адаптация, Telegram, YouGile и переход от простого режима к иерархическому без остановки текущей работы." />
    <Card className="mb-6"><WizardTitle icon={<GitBranch />} title="Режим организации" />
      <div className="grid gap-4 lg:grid-cols-[1fr_auto]"><div><p className="text-sm text-stone-500">Текущий режим</p><p className="mt-1 text-2xl font-semibold text-stone-950">{mode?.mode === 'HIERARCHY' ? 'Иерархическая структура' : 'Простая структура'}</p><p className="mt-2 text-sm leading-6 text-stone-500">Простой режим подходит компаниям до 30 сотрудников: без отделов, команд и делегирования; руководитель видит всю компанию. Иерархический режим включает отделы, команды, дерево подчинения, зоны ответственности и делегирование.</p></div><Button onClick={() => startWizardMutation.mutate()} disabled={mode?.mode === 'HIERARCHY'}>Перейти на организационную структуру</Button></div>
      {mode?.hierarchy_setup_state && mode.mode !== 'HIERARCHY' && <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{[
        ['departments_ready', 'Шаг 1: создать отделы'], ['teams_ready', 'Шаг 2: создать команды'], ['managers_ready', 'Шаг 3: назначить руководителей'], ['employees_distributed', 'Шаг 4: распределить сотрудников'], ['telegram_sources_ready', 'Шаг 5: привязать Telegram источники']
      ].map(([key, label]) => <label key={key} className="flex items-center gap-3 rounded-2xl bg-stone-50 p-4 text-sm"><input type="checkbox" checked={Boolean(wizardState[key])} onChange={(event) => updateWizardMutation.mutate({ [key]: event.target.checked } as Parameters<typeof updateHierarchyWizard>[0])} />{label}</label>)}<Button onClick={() => confirmWizardMutation.mutate()} className="md:col-span-2 xl:col-span-3">Шаг 6: подтвердить структуру</Button></div>}
      {confirmWizardMutation.error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">Нельзя включить иерархический режим: завершите все шаги мастера.</p>}
    </Card>
    <div className="mb-6 flex flex-wrap gap-2">{[1,2,3,4,5].map((n) => <Button key={n} variant={step === n ? 'primary' : 'secondary'} onClick={() => setStep(n)}>Шаг {n}</Button>)}</div>
    {step === 1 && <Card><WizardTitle icon={<MessageCircle />} title="Подключение Telegram-источников" /><div className="grid gap-4 md:grid-cols-[1fr_auto]"><Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}><option value="">Отдел для чата/темы</option>{departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</Select><Button onClick={() => codeMutation.mutate()}><Send className="h-4 w-4" />Подключить источник</Button></div>{codeMutation.data && <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-5"><p className="text-3xl font-semibold text-stone-950">{codeMutation.data.code}</p><ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-stone-700">{codeMutation.data.instruction.map((item) => <li key={item}>{item}</li>)}</ol></div>}<div className="mt-5 space-y-2">{sources.map((source) => <div key={source.id} className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3"><span>{source.title}</span><Badge tone={source.ai_enabled ? 'green' : 'neutral'}>{source.source_type === 'TELEGRAM_TOPIC' ? 'Тема' : 'Чат'}</Badge></div>)}{!sources.length && chats.map((chat) => <div key={chat.id} className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3"><span>{chat.title}</span><Badge tone={chat.ai_enabled ? 'green' : 'neutral'}>{chat.ai_enabled ? 'AI включен' : 'AI выключен'}</Badge></div>)}</div></Card>}
    {step === 2 && <Card><WizardTitle icon={<UsersRound />} title="Сотрудники" /><p className="text-sm text-stone-500">Telegram ID не вводится вручную. Менеджер добавляет ФИО, email, роль, должность и @username; сотрудник сам пишет /start боту, после чего Командус привязывает Telegram ID.</p><div className="mt-5 grid gap-3 md:grid-cols-3">{employees.map((e) => <div key={e.id} className="rounded-2xl bg-stone-50 p-4"><p className="font-medium">{e.full_name}</p><p className="text-sm text-stone-500">{e.telegram_username}</p><Badge tone={e.telegram_status === 'CONNECTED' ? 'green' : 'amber'}>{e.telegram_status === 'CONNECTED' ? 'Telegram подключён' : 'Ожидает /start'}</Badge></div>)}</div></Card>}
    {step === 3 && <Card><WizardTitle icon={<KeyRound />} title="API-токен YouGile" /><div className="flex gap-3"><Input type="password" value={token} onChange={(e) => setToken(e.target.value)} placeholder="API-токен" /><Button onClick={() => yougileMutation.mutate()}>Проверить токен</Button></div>{yougileMutation.data && <p className="mt-4 text-sm text-emerald-700">Токен проверен, интеграция создана. Доски можно привязать к команде или отделу.</p>}</Card>}
    {step === 4 && <Card><WizardTitle icon={<CheckCircle2 />} title="Доски YouGile" /><p className="text-sm text-stone-500">Поддерживается несколько досок: разработка, DevOps, продажи, маркетинг. Привязка выполняется через команду → доску или отдел → доску.</p></Card>}
    {step === 5 && <Card><WizardTitle icon={<CheckCircle2 />} title="Сопоставление колонок" /><div className="grid gap-3 md:grid-cols-4">{['К выполнению','В работе','На проверке','Завершено'].map((item) => <div key={item} className="rounded-2xl bg-stone-50 p-4 text-center font-medium">{item}</div>)}</div></Card>}
  </>;
}
function WizardTitle({ icon, title }: { icon: JSX.Element; title: string }) { return <div className="mb-5 flex items-center gap-3"><div className="rounded-2xl bg-stone-900 p-3 text-white">{icon}</div><h2 className="font-semibold text-stone-950">{title}</h2></div>; }

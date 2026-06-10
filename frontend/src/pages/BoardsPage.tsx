import { useMutation, useQuery } from '@tanstack/react-query';
import { Bot, CheckCircle2, Columns3, KeyRound, MessageCircle, PlugZap, RefreshCw } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { verifyYouGile } from '../shared/api/boardsV2';
import { getOrganizationChats } from '../shared/api/orgV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';
import { PageHeader } from '../shared/ui/PageHeader';

const lifecycle = ['«To Do» → К выполнению', '«In Progress» → В работе', '«Review» → На проверке', '«Done» → Завершено'];

export function BoardsPage() {
  const [token, setToken] = useState('');
  const { data: chats = [] } = useQuery({ queryKey: ['v2', 'chats'], queryFn: getOrganizationChats });
  const verifyMutation = useMutation({ mutationFn: () => verifyYouGile(token) });
  function onSubmit(event: FormEvent) { event.preventDefault(); verifyMutation.mutate(); }
  const cards = [
    { title: 'Telegram', icon: <MessageCircle />, status: chats.length ? 'Подключен' : 'Ожидает чат', last: chats[0]?.connected_at, errors: chats.filter((chat) => !chat.bot_is_admin).length ? 'Проверьте права администратора' : 'Нет' },
    { title: 'YouGile', icon: <PlugZap />, status: verifyMutation.data ? 'Подключен' : 'Не подключен', last: verifyMutation.data ? 'только что' : '—', errors: verifyMutation.error ? verifyMutation.error.message : 'Нет' },
    { title: 'LLM', icon: <Bot />, status: 'Настроен через переменные окружения', last: 'по запросу AI', errors: 'Нет' },
  ];
  return <><PageHeader eyebrow="Интеграции" title="Интеграции" description="Telegram слушает рабочие чаты, LLM извлекает задачи, YouGile получает подтверждённые карточки через единый слой провайдеров." />
    <section className="grid gap-4 md:grid-cols-3">{cards.map((card) => <Card key={card.title}><div className="mb-4 flex items-center justify-between"><div className="rounded-2xl bg-stone-100 p-3 text-stone-700">{card.icon}</div><Badge tone={card.status.includes('Подключен') || card.status.includes('Настроен') ? 'green' : 'amber'}>{card.status}</Badge></div><h2 className="font-semibold text-stone-950">{card.title}</h2><p className="mt-2 text-sm text-stone-500">Последняя синхронизация: {card.last || '—'}</p><p className="mt-1 text-sm text-stone-500">Ошибки: {card.errors}</p><Button className="mt-5" variant="secondary"><RefreshCw className="h-4 w-4" />Переподключить</Button></Card>)}</section>
    <section className="mt-6 grid gap-6 xl:grid-cols-[460px_1fr]"><Card><div className="mb-5 flex items-start gap-3"><div className="rounded-2xl bg-stone-900 p-3 text-white"><KeyRound className="h-5 w-5" /></div><div><h2 className="font-semibold text-stone-950">Подключить YouGile</h2><p className="mt-1 text-sm leading-6 text-stone-500">API-токен проверяется на сервере и хранится в зашифрованном виде.</p></div></div><form className="space-y-4" onSubmit={onSubmit}><Input type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="API-токен YouGile" minLength={8} required /><Button className="w-full" type="submit" disabled={verifyMutation.isPending}>{verifyMutation.isPending ? 'Проверяем...' : 'Проверить и подключить'}</Button></form>{verifyMutation.error && <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{verifyMutation.error.message}</p>}{verifyMutation.data && <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"><CheckCircle2 className="mb-2 h-5 w-5" />Интеграция создана: {verifyMutation.data.name}</div>}</Card><Card><div className="mb-4 flex items-center gap-3"><Columns3 className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Маппинг колонок</h2></div><div className="grid gap-3 md:grid-cols-2">{lifecycle.map((item) => <div key={item} className="rounded-2xl bg-stone-50 px-4 py-3 font-medium text-stone-800">{item}</div>)}</div></Card></section>
  </>;
}

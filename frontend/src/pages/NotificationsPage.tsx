import { Bell, CheckCircle2, PlugZap, Timer, UserRoundCheck } from 'lucide-react';
import { Card } from '../shared/ui/Card';
import { PageHeader } from '../shared/ui/PageHeader';

const items = [
  { icon: <Bell />, title: 'Новая задача', text: 'AI обнаружил задачу и отправил ее на подтверждение.' },
  { icon: <UserRoundCheck />, title: 'Подключение сотрудника', text: 'Сотрудник написал /start и связал Telegram.' },
  { icon: <Timer />, title: 'Просрочка', text: 'Дедлайн нарушен — менеджер получает сигнал.' },
  { icon: <PlugZap />, title: 'Ошибка интеграции', text: 'YouGile или LLM недоступны.' },
  { icon: <CheckCircle2 />, title: 'Отказ сотрудника', text: 'Причина отказа сохраняется для аналитики.' },
];
export function NotificationsPage() { return <><PageHeader eyebrow="Центр уведомлений" title="Уведомления" description="Колокольчик и центр событий для задач, отказов, просрочек, интеграций и подключений сотрудников." /><section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{items.map((item) => <Card key={item.title}><div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-100 text-stone-700">{item.icon}</div><h2 className="font-semibold text-stone-950">{item.title}</h2><p className="mt-2 text-sm leading-6 text-stone-500">{item.text}</p></Card>)}</section></>; }

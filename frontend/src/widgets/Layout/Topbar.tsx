import { Bell, Bot, LogOut, LucideIcon, ShieldCheck, Timer, UserRoundCheck } from 'lucide-react';
import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../../app/auth';
import { cn } from '../../shared/lib/cn';
import { Badge } from '../../shared/ui/Badge';
import { Button } from '../../shared/ui/Button';
import { navigationForRole } from './navigation';

const roleLabel: Record<string, string> = {
  OWNER: 'Владелец',
  ADMIN: 'Администратор',
  MANAGER: 'Руководитель',
  EMPLOYEE: 'Сотрудник',
  OBSERVER: 'Наблюдатель',
};

type NotificationTone = 'brand' | 'red' | 'green';
type Notification = { id: string; icon: LucideIcon; tone: NotificationTone; title: string; text: string; time: string };

const notifications: Notification[] = [
  { id: 'n1', icon: Bot, tone: 'brand', title: 'Новая задача от AI', text: 'Выделена задача «Сформировать чек-листы аудита МП Югра».', time: '5 минут назад' },
  { id: 'n2', icon: Timer, tone: 'red', title: 'Просрочка', text: 'Отчёт и ПКМ по аудиту 1 стороны просрочен на 2 дня.', time: '2 часа назад' },
  { id: 'n3', icon: UserRoundCheck, tone: 'green', title: 'Сотрудник подключён', text: 'Кудинова Дарья связала Telegram через /start.', time: 'вчера' },
];

const toneChip: Record<NotificationTone, string> = {
  brand: 'bg-brand-50 text-brand-600',
  red: 'bg-red-50 text-red-600',
  green: 'bg-emerald-50 text-emerald-600',
};

export function Topbar() {
  const { user, logout } = useAuth();
  const items = navigationForRole(user?.role);
  const role = user?.role ? roleLabel[user.role] ?? user.role : 'Доступ';

  return (
    <header className="sticky top-0 z-20 border-b border-stone-900/[0.06] bg-white/70 backdrop-blur-xl backdrop-saturate-150">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/logo.svg" alt="Командус" className="h-9 w-9 rounded-xl shadow-sm ring-1 ring-black/5 lg:hidden" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-stone-950 lg:hidden">Командус</p>
            <p className="hidden truncate text-sm text-stone-500 lg:block">{user?.email} · {role}</p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          <span className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 sm:inline-flex">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden />
            Все системы в норме
          </span>
          <NotificationsBell />
          <Badge tone="brand"><ShieldCheck className="mr-1 h-3.5 w-3.5" />{role}</Badge>
          <Button variant="ghost" size="sm" onClick={() => logout()}><LogOut className="h-4 w-4" />Выйти</Button>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-3 lg:hidden" aria-label="Мобильная навигация">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'shrink-0 rounded-lg border px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'border-brand-600 bg-brand-600 text-white shadow-brand-sm'
                  : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50',
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}

function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const unread = notifications.length;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="focus-ring relative inline-flex h-9 w-9 items-center justify-center rounded-xl text-stone-600 transition-colors hover:bg-stone-100 hover:text-stone-950"
        aria-label="Уведомления"
        aria-expanded={open}
      >
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-semibold text-white">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-30" onClick={() => setOpen(false)} />
          <div className="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-soft animate-scale-in">
            <div className="flex items-center justify-between border-b border-stone-100 px-4 py-3">
              <p className="text-sm font-semibold text-stone-950">Уведомления</p>
              <Badge tone="brand">{unread} новых</Badge>
            </div>
            <div className="max-h-96 overflow-y-auto p-1.5">
              {notifications.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.id} className="flex gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-stone-50">
                    <span className={cn('flex h-9 w-9 shrink-0 items-center justify-center rounded-lg', toneChip[item.tone])}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-stone-900">{item.title}</p>
                      <p className="mt-0.5 text-sm leading-5 text-stone-500">{item.text}</p>
                      <p className="mt-1 text-xs text-stone-400">{item.time}</p>
                    </div>
                  </div>
                );
              })}
            </div>
            <Link
              to="/notifications"
              onClick={() => setOpen(false)}
              className="block border-t border-stone-100 px-4 py-3 text-center text-sm font-medium text-brand-600 transition-colors hover:bg-stone-50"
            >
              Все уведомления
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

import type { ReactNode } from 'react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';
import { BarChart3, Bot, CheckSquare, LayoutDashboard, MessageSquareText, Sparkles, UserRound } from 'lucide-react';
import { env } from '@/shared/config/env';
import { getTelegramUser, isTelegramMiniApp } from '@/shared/lib/telegram';

const nav = [
  { to: '/', label: 'Обзор', icon: LayoutDashboard },
  { to: '/tasks', label: 'Задачи', icon: CheckSquare },
  { to: '/suggestions', label: 'AI', icon: Sparkles },
  { to: '/meetings', label: 'Встречи', icon: MessageSquareText },
  { to: '/analytics', label: 'Аналитика', icon: BarChart3 },
  { to: '/profile', label: 'Профиль', icon: UserRound },
];

function NavItem({ to, label, icon: Icon, compact = false }: (typeof nav)[number] & { compact?: boolean }) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-semibold transition',
          compact && 'flex-1 flex-col gap-1 rounded-2xl px-2 py-2 text-[11px]',
          isActive ? 'bg-tg-button text-tg-buttonText shadow-soft' : 'text-tg-hint hover:bg-black/5 hover:text-tg-text dark:hover:bg-white/10',
        )
      }
    >
      <Icon className={compact ? 'h-5 w-5' : 'h-4 w-4'} />
      <span>{label}</span>
    </NavLink>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const user = getTelegramUser();
  const inTelegram = isTelegramMiniApp();

  return (
    <div className="min-h-dvh bg-tg-bg text-tg-text">
      <div className="mx-auto flex min-h-dvh w-full max-w-7xl gap-5 px-3 pb-[calc(96px+env(safe-area-inset-bottom))] pt-[calc(12px+env(safe-area-inset-top))] md:px-5 md:pb-5">
        <aside className="sticky top-5 hidden h-[calc(100dvh-40px)] w-72 shrink-0 flex-col rounded-[32px] border border-black/5 bg-tg-secondaryBg p-4 shadow-soft dark:border-white/10 md:flex">
          <div className="flex items-center gap-3 rounded-3xl bg-slate-950 p-3 text-white dark:bg-white/10">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-tg-button text-tg-buttonText">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <p className="text-lg font-black">{env.appName}</p>
              <p className="text-xs text-white/60">AI project manager</p>
            </div>
          </div>

          <nav className="mt-6 grid gap-2">
            {nav.map((item) => <NavItem key={item.to} {...item} />)}
          </nav>

          <div className="mt-auto rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-tg-hint">{inTelegram ? 'Telegram Mini App' : 'PWA mode'}</p>
            <p className="mt-2 text-sm font-semibold text-tg-text">
              {user ? `${user.first_name}${user.username ? ` · @${user.username}` : ''}` : 'Mock/demo user'}
            </p>
            <p className="mt-2 text-xs leading-5 text-tg-hint">initData отправляется в backend через auth header, а тема берётся из Telegram клиента.</p>
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <div className="mb-4 flex items-center justify-between rounded-[28px] border border-black/5 bg-tg-secondaryBg px-4 py-3 shadow-soft dark:border-white/10 md:hidden">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-tg-button text-tg-buttonText">
                <Bot className="h-5 w-5" />
              </div>
              <div>
                <p className="font-black">{env.appName}</p>
                <p className="text-xs text-tg-hint">{inTelegram ? 'Mini App' : 'PWA'}</p>
              </div>
            </div>
            <div className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-tg-hint dark:bg-white/10">
              {env.useMocks ? 'Mock' : 'API'}
            </div>
          </div>
          {children}
        </main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-black/5 bg-tg-secondaryBg/95 px-2 pb-[calc(8px+env(safe-area-inset-bottom))] pt-2 shadow-[0_-10px_30px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 md:hidden">
        <div className="mx-auto flex max-w-xl gap-1">
          {nav.slice(1, 6).map((item) => <NavItem key={item.to} {...item} compact />)}
        </div>
      </nav>
    </div>
  );
}

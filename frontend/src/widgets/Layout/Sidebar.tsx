import { NavLink } from 'react-router-dom';
import { cn } from '../../shared/lib/cn';
import { navigation } from './navigation';

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-stone-900/[0.06] bg-white/60 px-4 py-6 backdrop-blur-xl backdrop-saturate-150 lg:flex lg:flex-col">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="relative">
          <span className="absolute -inset-1 rounded-2xl bg-brand-gradient opacity-25 blur-md" aria-hidden />
          <img src="/logo.svg" alt="Командус" className="relative h-11 w-11 rounded-xl shadow-sm ring-1 ring-black/5" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-500">AI PM</p>
          <p className="truncate font-display text-xl font-bold tracking-tight text-stone-950">Командус</p>
        </div>
      </div>

      <nav className="space-y-1" aria-label="Главная навигация">
        {navigation.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'group flex min-h-14 items-center gap-3 rounded-xl px-3 text-sm transition-all duration-150',
                  isActive
                    ? 'bg-brand-button text-white shadow-brand-sm'
                    : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cn(
                      'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors',
                      isActive ? 'bg-white/15 text-white' : 'bg-stone-100 text-stone-500 group-hover:bg-white group-hover:text-brand-600',
                    )}
                  >
                    <Icon className="h-5 w-5" />
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate font-semibold">{item.label}</span>
                    <span className={cn('block truncate text-xs', isActive ? 'text-white/70' : 'text-stone-400')}>{item.description}</span>
                  </span>
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="mt-auto rounded-2xl border border-stone-200/80 bg-stone-50/80 p-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-2.5 w-2.5 animate-pulse-ring rounded-full bg-emerald-500" aria-hidden />
          <p className="text-sm font-semibold text-stone-800">Ассистент онлайн</p>
        </div>
        <p className="mt-1.5 text-xs leading-5 text-stone-500">Бот следит за чатами и встречами в фоне.</p>
      </div>
    </aside>
  );
}

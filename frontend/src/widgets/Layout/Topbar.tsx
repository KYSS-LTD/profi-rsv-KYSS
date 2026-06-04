import { NavLink, useLocation } from 'react-router-dom';
import { env } from '../../shared/config/env';
import { cn } from '../../shared/lib/cn';
import { Badge } from '../../shared/ui/Badge';
import { navigation } from './navigation';

export function Topbar() {
  const { pathname } = useLocation();
  const active = navigation.find((item) => pathname.startsWith(item.to)) ?? navigation[0];

  return (
    <header className="sticky top-0 z-20 border-b border-stone-900/[0.06] bg-white/70 backdrop-blur-xl backdrop-saturate-150">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/logo.svg" alt="Командус" className="h-9 w-9 rounded-xl shadow-sm ring-1 ring-black/5 lg:hidden" />
          <div className="min-w-0">
            <p className="hidden text-xs font-medium text-stone-400 lg:block">Командус · {active.description}</p>
            <p className="truncate text-base font-semibold tracking-tight text-stone-950 lg:text-lg">{active.label}</p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          {env.useMocks && <Badge tone="amber">Демо-данные</Badge>}
          <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden />
            Все системы в норме
          </span>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-3 lg:hidden" aria-label="Мобильная навигация">
        {navigation.map((item) => (
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

import { NavLink } from 'react-router-dom';
import { env } from '../../shared/config/env';
import { cn } from '../../shared/lib/cn';
import { Badge } from '../../shared/ui/Badge';
import { navigation } from './navigation';

export function Topbar() {
  return (
    <header className="sticky top-0 z-20 border-b border-stone-200 bg-white/95 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/logo.svg" alt="Командус" className="h-9 w-9 rounded-xl lg:hidden" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-stone-950 lg:hidden">Командус</p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          {env.useMocks && <Badge tone="amber">Демо-данные</Badge>}
          <Badge tone="green"></Badge>
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-3 lg:hidden" aria-label="Мобильная навигация">
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'shrink-0 rounded-lg border px-3 py-2 text-sm font-medium transition',
                isActive ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-200 bg-white text-stone-600',
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

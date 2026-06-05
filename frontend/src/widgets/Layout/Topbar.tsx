import { LogOut, ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../app/auth';
import { cn } from '../../shared/lib/cn';
import { Badge } from '../../shared/ui/Badge';
import { Button } from '../../shared/ui/Button';
import { navigation } from './navigation';

export function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b border-stone-200 bg-white/95 backdrop-blur">
      <div className="flex min-h-16 items-center justify-between gap-3 px-4 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/logo.svg" alt="Командус" className="h-9 w-9 rounded-xl lg:hidden" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-stone-950 lg:hidden">Командус</p>
            <p className="hidden truncate text-sm text-stone-500 lg:block">Организация: {user?.organization_id.slice(0, 8)} · {user?.email}</p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          <Badge tone="green"><ShieldCheck className="mr-1 h-3.5 w-3.5" />{user?.role ?? 'RBAC'}</Badge>
          <Button variant="ghost" className="h-9 px-3" onClick={() => logout()}><LogOut className="h-4 w-4" />Выйти</Button>
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

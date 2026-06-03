import { NavLink } from 'react-router-dom';
import { cn } from '../../shared/lib/cn';
import { navigation } from './navigation';

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-stone-200 bg-white px-4 py-6 lg:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <img src="/logo.svg" alt="Командус" className="h-10 w-10 rounded-xl" />
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-stone-400">AI PM</p>
          <p className="truncate text-xl font-semibold tracking-tight text-stone-950">Командус</p>
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
                  'group flex min-h-14 items-center gap-3 rounded-xl px-3 text-sm transition',
                  isActive
                    ? 'bg-stone-900 text-white'
                    : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950',
                )
              }
            >
              <Icon className="h-5 w-5 shrink-0" />
              <span className="min-w-0">
                <span className="block truncate font-medium">{item.label}</span>
                <span className="block truncate text-xs opacity-70">{item.description}</span>
              </span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

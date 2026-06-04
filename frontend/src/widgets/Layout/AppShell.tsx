import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppShell() {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen text-stone-950">
      <div className="grain pointer-events-none fixed inset-0 -z-10" aria-hidden />
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="min-w-0 flex-1">
          <Topbar />
          <main className="mx-auto w-full max-w-[1680px] px-4 py-6 lg:px-8 lg:py-8">
            <div key={pathname} className="animate-fade-up">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

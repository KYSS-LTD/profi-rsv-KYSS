import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, LockKeyhole, Mail, ShieldCheck } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../app/auth';
import { login } from '../shared/api/authV2';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/tasks';

  const loginMutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      navigate(from, { replace: true });
    },
  });

  if (auth.isAuthenticated) {
    return <Navigate to="/tasks" replace />;
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    loginMutation.mutate();
  }

  return (
    <main className="min-h-screen overflow-hidden bg-stone-950 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(16,185,129,0.25),transparent_30%),radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.2),transparent_30%),linear-gradient(135deg,#0c0a09,#1c1917)]" />
      <div className="relative mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-4 py-10 lg:grid-cols-[1fr_430px]">
        <section className="max-w-2xl">
          <div className="mb-8 inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-sm text-stone-200 backdrop-blur">
            <Bot className="h-4 w-4" /> Командус v2 SaaS · источник истины задач
          </div>
          <h1 className="text-balance text-5xl font-semibold tracking-tight md:text-7xl">AI-помощник менеджера, который доводит задачи до результата.</h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-stone-300">Telegram, LLM, подтверждения исполнителей, YouGile-синхронизация, RBAC и аналитика в одном production-ready интерфейсе.</p>
          <div className="mt-10 grid gap-3 sm:grid-cols-3">
            {['Multi-tenant', 'RBAC', 'Audit log'].map((item) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/10 p-4 text-sm font-medium text-stone-100 backdrop-blur">
                <ShieldCheck className="mb-3 h-5 w-5 text-emerald-300" /> {item}
              </div>
            ))}
          </div>
        </section>

        <Card className="border-white/10 bg-white p-6 text-stone-950 shadow-2xl">
          <div className="mb-6">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-stone-400">Вход</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">Панель управления</h2>
            <p className="mt-2 text-sm leading-6 text-stone-500">Используйте учетную запись, созданную менеджером. Саморегистрация отключена.</p>
          </div>

          <form className="space-y-4" onSubmit={onSubmit}>
            <label className="block space-y-2 text-sm font-medium text-stone-700">
              <span>Email</span>
              <span className="relative block">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                <Input className="pl-10" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="manager@company.com" required />
              </span>
            </label>
            <label className="block space-y-2 text-sm font-medium text-stone-700">
              <span>Пароль</span>
              <span className="relative block">
                <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                <Input className="pl-10" type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required />
              </span>
            </label>

            {loginMutation.error && <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{loginMutation.error.message}</div>}

            <Button className="h-12 w-full rounded-2xl" type="submit" disabled={loginMutation.isPending}>{loginMutation.isPending ? 'Входим...' : 'Войти в Командус'}</Button>
          </form>
        </Card>
      </div>
    </main>
  );
}

import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, CheckCircle2, Clock3, Sparkles, Smartphone } from 'lucide-react';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { PageHeader } from '@/shared/ui/PageHeader';
import { getTelegramUser, isTelegramMiniApp } from '@/shared/lib/telegram';

export function DashboardPage() {
  const { data: tasks = [] } = useQuery({ queryKey: ['tasks'], queryFn: api.getTasks });
  const { data: candidates = [] } = useQuery({ queryKey: ['candidates'], queryFn: api.getCandidates });
  const { data: analytics } = useQuery({ queryKey: ['analytics'], queryFn: api.getAnalytics });
  const user = getTelegramUser();

  const stats = [
    { label: 'Активные задачи', value: tasks.filter((task) => task.status !== 'done').length, icon: Clock3 },
    { label: 'Готово за неделю', value: analytics?.doneThisWeek ?? 0, icon: CheckCircle2 },
    { label: 'AI suggestions', value: candidates.length, icon: Sparkles },
  ];

  return (
    <section>
      <PageHeader
        eyebrow="Telegram Mini App + PWA"
        title={user ? `Привет, ${user.first_name}` : 'Командус Dashboard'}
        description="Мобильный frontend для Командуса: задачи, AI-кандидаты, summaries встреч и аналитика команды внутри Telegram или как обычная PWA."
        action={<Link to="/tasks"><Button>Открыть задачи <ArrowRight className="h-4 w-4" /></Button></Link>}
      />

      <div className="grid gap-4 md:grid-cols-3">
        {stats.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-tg-hint">{label}</p>
                <p className="mt-2 text-3xl font-black text-tg-text">{value}</p>
              </div>
              <div className="rounded-2xl bg-tg-button/10 p-3 text-tg-button">
                <Icon className="h-6 w-6" />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card className="overflow-hidden">
          <div className="flex items-start justify-between gap-3">
            <div>
              <Badge tone="blue">Live demo flow</Badge>
              <h2 className="mt-3 text-2xl font-black">Что показывает frontend</h2>
              <p className="mt-2 text-sm leading-6 text-tg-hint">Dashboard закрывает фронтовую часть MVP: mini-kanban, подтверждение задач от AI, meeting summary, team analytics и профиль участника.</p>
            </div>
            <Smartphone className="h-10 w-10 text-tg-link" />
          </div>

          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {[
              ['Tasks', 'Статусы, дедлайны, source badges, confidence и быстрый reschedule.'],
              ['AI Suggestions', 'Confirm/reject кандидатов с invalidation React Query.'],
              ['Meetings', 'Upload audio + summary preview + Knowledge Base preview.'],
              ['PWA/Telegram', 'manifest, service worker, safe-area, haptics, Telegram themeParams.'],
            ].map(([title, text]) => (
              <div key={title} className="rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
                <p className="font-bold text-tg-text">{title}</p>
                <p className="mt-1 text-sm leading-5 text-tg-hint">{text}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <Badge tone={isTelegramMiniApp() ? 'green' : 'yellow'}>{isTelegramMiniApp() ? 'Запущено в Telegram' : 'Открыто как PWA/browser'}</Badge>
          <h2 className="mt-4 text-xl font-black">Production checklist</h2>
          <ul className="mt-4 grid gap-3 text-sm text-tg-hint">
            <li className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">HTTPS-домен добавлен в BotFather как Web App URL.</li>
            <li className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">Backend проверяет hash в Telegram initData.</li>
            <li className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">VITE_API_BASE_URL указывает на production API.</li>
            <li className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">VITE_USE_MOCKS=false после подключения backend.</li>
          </ul>
        </Card>
      </div>
    </section>
  );
}

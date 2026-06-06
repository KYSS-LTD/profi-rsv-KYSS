import { useQuery } from '@tanstack/react-query';
import { Activity, Bot, CheckCircle2, Mic2, Sparkles, Trophy } from 'lucide-react';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Card } from '@/shared/ui/Card';
import { Loader } from '@/shared/ui/Loader';
import { PageHeader } from '@/shared/ui/PageHeader';

export function AnalyticsPage() {
  const { data: analytics, isLoading } = useQuery({ queryKey: ['analytics'], queryFn: api.getAnalytics });
  const { data: leaderboard = [] } = useQuery({ queryKey: ['leaderboard'], queryFn: api.getLeaderboard });

  if (isLoading) {
    return (
      <section>
        <PageHeader eyebrow="Team Analytics" title="Аналитика" description="Метрики demo MVP и качества AI." />
        <Loader />
      </section>
    );
  }

  const metrics = [
    { label: 'AI created tasks', value: analytics?.aiCreatedTasks ?? 0, icon: Bot },
    { label: 'Auto confirmed', value: analytics?.autoConfirmed ?? 0, icon: CheckCircle2 },
    { label: 'Waiting confirmation', value: analytics?.waitingConfirmation ?? 0, icon: Sparkles },
    { label: 'Voice processed', value: analytics?.voiceMessagesProcessed ?? 0, icon: Mic2 },
    { label: 'Meetings summarized', value: analytics?.meetingsSummarized ?? 0, icon: Activity },
    { label: 'Avg confidence', value: `${Math.round((analytics?.averageConfidence ?? 0) * 100)}%`, icon: Trophy },
  ];

  return (
    <section>
      <PageHeader
        eyebrow="Team Analytics"
        title="Аналитика команды"
        description="MVP-метрики для live-demo: сколько задач создал AI, сколько подтверждено, качество распознавания и velocity команды."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map(({ label, value, icon: Icon }) => (
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

      <div className="mt-5 grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <Card>
          <Badge tone="yellow">Velocity & quality</Badge>
          <div className="mt-5 grid gap-4">
            <div>
              <div className="mb-2 flex justify-between text-sm"><span className="text-tg-hint">Done this week</span><strong>{analytics?.doneThisWeek}</strong></div>
              <div className="h-3 rounded-full bg-slate-100 dark:bg-white/10"><div className="h-3 rounded-full bg-tg-button" style={{ width: `${Math.min((analytics?.doneThisWeek ?? 0) * 3, 100)}%` }} /></div>
            </div>
            <div>
              <div className="mb-2 flex justify-between text-sm"><span className="text-tg-hint">Overdue percent</span><strong>{analytics?.overduePercent}%</strong></div>
              <div className="h-3 rounded-full bg-slate-100 dark:bg-white/10"><div className="h-3 rounded-full bg-rose-500" style={{ width: `${analytics?.overduePercent ?? 0}%` }} /></div>
            </div>
            <div>
              <div className="mb-2 flex justify-between text-sm"><span className="text-tg-hint">AI quality</span><strong>{analytics?.aiQuality}%</strong></div>
              <div className="h-3 rounded-full bg-slate-100 dark:bg-white/10"><div className="h-3 rounded-full bg-emerald-500" style={{ width: `${analytics?.aiQuality ?? 0}%` }} /></div>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <Badge tone="purple">Achievements / gamification</Badge>
              <h2 className="mt-3 text-xl font-black text-tg-text">Leaderboard</h2>
            </div>
            <Trophy className="h-8 w-8 text-tg-link" />
          </div>
          <div className="mt-4 grid gap-3">
            {leaderboard.map((user, index) => (
              <div key={user.id} className="flex items-center justify-between rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-tg-button text-sm font-black text-tg-buttonText">#{index + 1}</div>
                  <div>
                    <p className="font-bold text-tg-text">{user.name}</p>
                    <p className="text-xs text-tg-hint">{user.role} · {user.done} done</p>
                  </div>
                </div>
                <strong className="text-lg text-tg-text">{user.score}</strong>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </section>
  );
}

import { useQuery } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { BarChart3, CheckCircle2, Clock, PieChart, TrendingUp, UsersRound } from 'lucide-react';
import { getDashboardAnalytics } from '../shared/api/analyticsV2';
import { Badge } from '../shared/ui/Badge';
import { Card } from '../shared/ui/Card';
import { EmptyState } from '../shared/ui/EmptyState';
import { ErrorState } from '../shared/ui/ErrorState';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';

export function AnalyticsPage() {
  const analyticsQuery = useQuery({ queryKey: ['v2', 'analytics', 'dashboard'], queryFn: getDashboardAnalytics });
  const data = analyticsQuery.data;
  const maxStatus = Math.max(1, ...Object.values(data?.pie_statuses ?? {}));
  const maxClosed = Math.max(1, ...(data?.closed_by_day ?? []).map((item) => item.completed));

  return (
    <>
      <PageHeader
        eyebrow="Company intelligence"
        title="Аналитика v2"
        description="Dashboard строится только по данным Командуса внутри текущей организации: статусы, acceptance/rejection, скорость реакции, завершения и burnup."
      />

      {analyticsQuery.isLoading && <Loader text="Собираем dashboard..." />}
      {analyticsQuery.error && <ErrorState error={analyticsQuery.error} />}
      {data && (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Metric icon={<BarChart3 />} label="Всего задач" value={data.total_tasks} note="source-of-truth" />
            <Metric icon={<CheckCircle2 />} label="Завершено" value={data.completed} note={`${data.acceptance_percent}% принято`} />
            <Metric icon={<Clock />} label="Средняя реакция" value={`${data.average_response_time}ч`} note="до принятия" />
            <Metric icon={<TrendingUp />} label="Просрочено" value={data.overdue} note={`${data.rejection_percent}% отказов`} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-2">
            <Card>
              <div className="mb-5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3"><PieChart className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Распределение по статусам</h2></div>
                <Badge tone="blue">Pie data</Badge>
              </div>
              <div className="space-y-3">
                {Object.entries(data.pie_statuses).map(([status, count]) => (
                  <div key={status}>
                    <div className="mb-1 flex justify-between text-sm"><span className="font-medium text-stone-700">{status}</span><span className="text-stone-500">{count}</span></div>
                    <div className="h-3 overflow-hidden rounded-full bg-stone-100"><div className="h-full rounded-full bg-stone-900" style={{ width: `${(count / maxStatus) * 100}%` }} /></div>
                  </div>
                ))}
                {Object.keys(data.pie_statuses).length === 0 && <EmptyState title="Нет статусов" text="Создайте задачи, чтобы увидеть распределение." />}
              </div>
            </Card>

            <Card>
              <div className="mb-5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3"><UsersRound className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Топ сотрудников</h2></div>
                <Badge tone="green">Bar chart</Badge>
              </div>
              <div className="space-y-3">
                {data.top_employees.map((item, index) => (
                  <div key={item.employee_id} className="rounded-2xl bg-stone-50 p-3">
                    <div className="mb-2 flex items-center justify-between gap-3 text-sm"><span className="truncate font-medium text-stone-900">#{index + 1} · {item.employee_id}</span><span className="text-stone-500">{item.tasks}</span></div>
                    <div className="h-2 rounded-full bg-white"><div className="h-full rounded-full bg-emerald-500" style={{ width: `${(item.tasks / Math.max(1, data.top_employees[0]?.tasks ?? 1)) * 100}%` }} /></div>
                  </div>
                ))}
                {data.top_employees.length === 0 && <EmptyState title="Нет назначений" text="Назначьте задачи сотрудникам, чтобы построить рейтинг." />}
              </div>
            </Card>

            <Card>
              <h2 className="mb-5 font-semibold text-stone-950">Закрытые задачи по дням</h2>
              <div className="flex h-64 items-end gap-2 rounded-2xl bg-stone-50 p-4">
                {data.closed_by_day.map((item) => <div key={item.date} className="flex min-w-10 flex-1 flex-col items-center gap-2"><div className="w-full rounded-t-xl bg-blue-500" style={{ height: `${Math.max(8, (item.completed / maxClosed) * 190)}px` }} /><span className="text-[10px] text-stone-500">{item.date.slice(5)}</span></div>)}
                {data.closed_by_day.length === 0 && <p className="m-auto text-sm text-stone-400">Пока нет закрытых задач</p>}
              </div>
            </Card>

            <Card>
              <h2 className="mb-5 font-semibold text-stone-950">Burnup завершений</h2>
              <div className="space-y-3">
                {data.burnup.map((item) => <div key={item.date} className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3"><span className="text-sm text-stone-600">{item.date}</span><Badge tone="green">{item.completed_total}</Badge></div>)}
                {data.burnup.length === 0 && <EmptyState title="Burnup пуст" text="График появится после первых DONE задач." />}
              </div>
            </Card>
          </section>
        </>
      )}
    </>
  );
}

function Metric({ icon, label, value, note }: { icon: ReactNode; label: string; value: string | number; note: string }) {
  return <Card><div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-stone-100 text-stone-700">{icon}</div><p className="text-sm text-stone-500">{label}</p><p className="mt-1 text-3xl font-semibold text-stone-950">{value}</p><p className="mt-2 text-xs text-stone-400">{note}</p></Card>;
}

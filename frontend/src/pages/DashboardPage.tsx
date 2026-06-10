import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, Bot, CheckCircle2, Clock, LineChart, PieChart, TrendingUp, UsersRound } from 'lucide-react';
import { getDashboardAnalytics } from '../shared/api/analyticsV2';
import { Badge } from '../shared/ui/Badge';
import { Card } from '../shared/ui/Card';
import { ErrorState } from '../shared/ui/ErrorState';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';

export function DashboardPage() {
  const query = useQuery({ queryKey: ['v2', 'analytics', 'dashboard'], queryFn: getDashboardAnalytics });
  const data = query.data;
  const maxEmployee = Math.max(1, ...(data?.top_employees ?? []).map((item) => item.tasks));
  const maxStatus = Math.max(1, ...Object.values(data?.pie_statuses ?? {}));
  const maxClosed = Math.max(1, ...(data?.closed_by_day ?? []).map((item) => item.completed));

  return (
    <>
      <PageHeader eyebrow="AI-руководитель" title="Сводка" description="10-секундная операционная картина: задачи, риски, перегрузка, AI и интеграции без ручного обхода досок." />
      {query.isLoading && <Loader text="Собираем показатели компании..." />}
      {query.error && <ErrorState error={query.error} />}
      {data && (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
            <Metric label="Всего задач" value={data.total_tasks} icon={<Bot />} />
            <Metric label="В работе" value={data.in_work} icon={<Clock />} />
            <Metric label="Просрочено" value={data.overdue} icon={<AlertTriangle />} tone="red" />
            <Metric label="Завершено" value={data.completed} icon={<CheckCircle2 />} tone="green" />
            <Metric label="Точность AI" value={`${data.ai_accuracy}%`} icon={<TrendingUp />} tone="blue" />
            <Metric label="Среднее время" value={`${data.average_completion_time}ч`} icon={<LineChart />} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card>
              <div className="mb-5 flex items-center justify-between"><h2 className="font-semibold text-stone-950">Что требует внимания</h2><Badge tone={data.attention.length ? 'red' : 'green'}>{data.attention.length ? 'Требуется действие' : 'В норме'}</Badge></div>
              <div className="grid gap-3 md:grid-cols-2">
                {(data.attention.length ? data.attention : [{ type: 'ok', title: 'Критических сигналов нет', count: 0 }]).map((item) => (
                  <div key={item.type} className="rounded-2xl border border-stone-200 bg-stone-50 p-4"><p className="text-sm text-stone-500">{item.title}</p><p className="mt-2 text-3xl font-semibold text-stone-950">{item.count}</p></div>
                ))}
              </div>
            </Card>
            <Card>
              <div className="mb-5 flex items-center gap-3"><UsersRound className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Нагрузка сотрудников</h2></div>
              <div className="space-y-3">
                {data.top_employees.map((item) => <Bar key={item.employee_id} label={item.employee_name} value={item.tasks} max={maxEmployee} />)}
                {!data.top_employees.length && <p className="text-sm text-stone-500">Пока нет назначенных задач.</p>}
              </div>
            </Card>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-3">
            <Card><ChartTitle icon={<PieChart />} title="Статусы задач" />{Object.entries(data.pie_statuses).map(([status, count]) => <Bar key={status} label={status} value={count} max={maxStatus} />)}</Card>
            <Card><ChartTitle icon={<LineChart />} title="Продуктивность" />{data.closed_by_day.map((item) => <Bar key={item.date} label={item.date} value={item.completed} max={maxClosed} />)}</Card>
            <Card><ChartTitle icon={<Clock />} title="Последние события" /><div className="space-y-3">{data.activity.map((item) => <div key={`${item.at}-${item.text}`} className="rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">{item.text}</div>)}</div></Card>
          </section>
        </>
      )}
    </>
  );
}

function Metric({ label, value, icon, tone = 'neutral' }: { label: string; value: string | number; icon: JSX.Element; tone?: 'neutral' | 'red' | 'green' | 'blue' }) {
  const colors = { neutral: 'bg-stone-100 text-stone-700', red: 'bg-red-50 text-red-700', green: 'bg-emerald-50 text-emerald-700', blue: 'bg-blue-50 text-blue-700' };
  return <Card><div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-2xl ${colors[tone]}`}>{icon}</div><p className="text-sm text-stone-500">{label}</p><p className="mt-1 text-3xl font-semibold text-stone-950">{value}</p></Card>;
}

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  return <div><div className="mb-1 flex justify-between text-sm"><span className="font-medium text-stone-700">{label}</span><span className="text-stone-500">{value}</span></div><div className="h-3 overflow-hidden rounded-full bg-stone-100"><div className="h-full rounded-full bg-stone-900" style={{ width: `${(value / max) * 100}%` }} /></div></div>;
}
function ChartTitle({ icon, title }: { icon: JSX.Element; title: string }) { return <div className="mb-5 flex items-center gap-3 text-stone-950">{icon}<h2 className="font-semibold">{title}</h2></div>; }

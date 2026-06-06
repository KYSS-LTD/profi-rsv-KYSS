import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, BadgeCheck, ChevronDown, CircleGauge, Network, Search, ShieldCheck, UsersRound } from 'lucide-react';
import { useMemo, useState } from 'react';
import { getOrganizationMap, OrgMapNode } from '../shared/api/orgOS';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';

const roleLabels: Record<string, string> = {
  OWNER: 'Владелец',
  ADMIN: 'Администратор',
  MANAGER: 'Руководитель',
  EMPLOYEE: 'Сотрудник',
  OBSERVER: 'Наблюдатель',
};

export function OrgMapPage() {
  const query = useQuery({ queryKey: ['v2', 'org-os', 'map'], queryFn: getOrganizationMap });
  const [search, setSearch] = useState('');
  const [expanded, setExpanded] = useState(true);
  const data = query.data;
  const visibleNodes = useMemo(() => filterTree(data?.nodes ?? [], search), [data?.nodes, search]);
  const totals = useMemo(() => flatten(data?.nodes ?? []), [data?.nodes]);
  const overloaded = totals.filter((node) => node.workload.workload_score >= 80).length;
  const responsibilities = totals.reduce((sum, node) => sum + node.responsibilities.length, 0);

  return (
    <>
      <PageHeader eyebrow="Организационная ОС" title="Карта организации" description="Единая человеческая картина: кто кому подчиняется, кто чем владеет, где перегрузка, делегации и зоны внимания." />
      {query.isLoading && <Loader text="Строим дерево компании и считаем нагрузку..." />}
      {query.error && <ErrorState error={query.error} />}
      {data && (
        <>
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            <Metric icon={<UsersRound />} label="Сотрудники" value={totals.length} />
            <Metric icon={<CircleGauge />} label="Здоровье" value={`${data.health.score}/100`} tone={data.health.score < 70 ? 'red' : 'green'} />
            <Metric icon={<AlertTriangle />} label="Сигналы внимания" value={data.attention.length} tone={data.attention.length ? 'red' : 'green'} />
            <Metric icon={<BadgeCheck />} label="Зоны ответственности" value={responsibilities} />
            <Metric icon={<ShieldCheck />} label="Перегрузка" value={overloaded} tone={overloaded ? 'red' : 'green'} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[1fr_360px]">
            <Card>
              <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="flex items-center gap-2 text-lg font-semibold text-stone-950"><Network className="h-5 w-5" /> Дерево подчинения</h2>
                  <p className="text-sm text-stone-500">Иерархия строится только по manager_id, роли не определяют подчинение.</p>
                </div>
                <div className="flex gap-2">
                  <div className="relative"><Search className="absolute left-3 top-2.5 h-4 w-4 text-stone-400" /><Input className="pl-9" placeholder="Найти человека или роль" value={search} onChange={(event) => setSearch(event.target.value)} /></div>
                  <Button variant="secondary" onClick={() => setExpanded((value) => !value)}><ChevronDown className="h-4 w-4" />{expanded ? 'Свернуть' : 'Развернуть'}</Button>
                </div>
              </div>
              <div className="space-y-3">
                {visibleNodes.map((node) => <TreeNode key={node.id} node={node} level={0} expanded={expanded || Boolean(search)} />)}
                {!visibleNodes.length && <p className="rounded-2xl bg-stone-50 p-6 text-sm text-stone-500">Ничего не найдено. Попробуйте изменить поиск.</p>}
              </div>
            </Card>

            <aside className="space-y-6">
              <Card>
                <h2 className="font-semibold text-stone-950">Что требует внимания</h2>
                <div className="mt-4 space-y-3">
                  {(data.attention.length ? data.attention : [{ type: 'ok', title: 'Критических сигналов нет', count: 0, severity: 'info', explanation: 'Команда работает в нормальном режиме.' }]).map((item) => (
                    <div key={item.type} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                      <div className="flex items-start justify-between gap-3"><p className="font-medium text-stone-900">{item.title}</p><Badge tone={item.severity === 'critical' ? 'red' : item.severity === 'warning' ? 'amber' : 'green'}>{item.count}</Badge></div>
                      <p className="mt-2 text-sm text-stone-500">{item.explanation}</p>
                    </div>
                  ))}
                </div>
              </Card>
              <Card>
                <h2 className="font-semibold text-stone-950">Пять системных ролей</h2>
                <div className="mt-4 flex flex-wrap gap-2">{data.role_model.map((role) => <Badge key={role}>{roleLabels[role] ?? role}</Badge>)}</div>
                <p className="mt-4 text-sm text-stone-500">Бизнес-смысл хранится в должностях и зонах ответственности. Технический доступ расширяется scopes: {data.permission_scopes.join(', ')}.</p>
              </Card>
              <Card>
                <h2 className="font-semibold text-stone-950">Почему такой health score</h2>
                <ul className="mt-4 space-y-2 text-sm text-stone-600">{data.health.causes.map((cause) => <li key={cause}>• {cause}</li>)}</ul>
              </Card>
            </aside>
          </section>
        </>
      )}
    </>
  );
}

function TreeNode({ node, level, expanded }: { node: OrgMapNode; level: number; expanded: boolean }) {
  const hasChildren = node.children.length > 0;
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm" style={{ marginLeft: level ? Math.min(level * 24, 96) : 0 }}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold text-stone-950">{node.full_name}</p>
            <Badge tone={node.role === 'MANAGER' || node.role === 'OWNER' ? 'blue' : 'neutral'}>{roleLabels[node.role] ?? node.role}</Badge>
            {node.requires_attention && <Badge tone="red">Требует внимания</Badge>}
          </div>
          <p className="mt-1 text-sm text-stone-500">{node.position || 'Должность не указана'} · прямых: {node.direct_reports} · всего в ветке: {node.indirect_reports}</p>
          {!!node.responsibilities.length && <p className="mt-2 text-sm text-stone-700">Отвечает за: {node.responsibilities.join(', ')}</p>}
        </div>
        <div className="grid min-w-[260px] grid-cols-4 gap-2 text-center text-xs">
          <Mini label="Активно" value={node.workload.active_tasks} />
          <Mini label="Проср." value={node.workload.overdue_tasks} danger={node.workload.overdue_tasks > 0} />
          <Mini label="Блок" value={node.workload.blocked_tasks} />
          <Mini label="Нагрузка" value={`${node.workload.workload_score}%`} danger={node.workload.workload_score >= 80} />
        </div>
      </div>
      {expanded && hasChildren && <div className="mt-3 space-y-3">{node.children.map((child) => <TreeNode key={child.id} node={child} level={level + 1} expanded={expanded} />)}</div>}
    </div>
  );
}

function Metric({ icon, label, value, tone = 'neutral' }: { icon: JSX.Element; label: string; value: string | number; tone?: 'neutral' | 'red' | 'green' }) {
  const colors = { neutral: 'bg-stone-100 text-stone-700', red: 'bg-red-50 text-red-700', green: 'bg-emerald-50 text-emerald-700' };
  return <Card><div className={`mb-4 flex h-11 w-11 items-center justify-center rounded-2xl ${colors[tone]}`}>{icon}</div><p className="text-sm text-stone-500">{label}</p><p className="mt-1 text-3xl font-semibold text-stone-950">{value}</p></Card>;
}

function Mini({ label, value, danger }: { label: string; value: string | number; danger?: boolean }) {
  return <div className={`rounded-2xl px-3 py-2 ${danger ? 'bg-red-50 text-red-700' : 'bg-stone-50 text-stone-700'}`}><p className="font-semibold">{value}</p><p className="text-[11px] opacity-70">{label}</p></div>;
}

function flatten(nodes: OrgMapNode[]): OrgMapNode[] {
  return nodes.flatMap((node) => [node, ...flatten(node.children)]);
}

function filterTree(nodes: OrgMapNode[], search: string): OrgMapNode[] {
  const term = search.trim().toLowerCase();
  if (!term) return nodes;
  return nodes.flatMap((node) => {
    const children = filterTree(node.children, term);
    const matches = [node.full_name, node.position, node.role, ...node.responsibilities].filter(Boolean).join(' ').toLowerCase().includes(term);
    return matches || children.length ? [{ ...node, children }] : [];
  });
}

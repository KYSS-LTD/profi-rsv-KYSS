import { useQuery } from '@tanstack/react-query';
import { getLeaderboard, getTeamAnalytics } from '../shared/api/analytics';
import { getRoadmapCards } from '../shared/api/knowledge';
import { Badge } from '../shared/ui/Badge';
import { Card } from '../shared/ui/Card';
import { ErrorState } from '../shared/ui/ErrorState';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { AnalyticsGrid } from '../widgets/Analytics/AnalyticsGrid';
import { RoadmapCards } from '../widgets/Analytics/RoadmapCards';

export function AnalyticsPage() {
  const analyticsQuery = useQuery({ queryKey: ['team-analytics'], queryFn: getTeamAnalytics });
  const leaderboardQuery = useQuery({ queryKey: ['leaderboard'], queryFn: getLeaderboard });
  const roadmapCards = getRoadmapCards();

  return (
    <>
      <PageHeader
        eyebrow="Метрики команды"
        title="Аналитика"
        description="Карточки для демо: задачи от AI, подтверждения, голос, встречи, точность модели и скорость выполнения."
      />

      {analyticsQuery.isLoading && <Loader text="Загружаем аналитику команды..." />}
      {analyticsQuery.error && <ErrorState error={analyticsQuery.error} />}
      {analyticsQuery.data && <AnalyticsGrid analytics={analyticsQuery.data} />}

      <section className="mt-6 grid gap-6">
        <RoadmapCards cards={roadmapCards} />

        <Card>
          <h2 className="mb-4 font-semibold text-stone-950">Рейтинг команды</h2>
          {leaderboardQuery.isLoading && <p className="text-sm text-stone-500">Загружаем рейтинг...</p>}
          {leaderboardQuery.data && (
            <div className="space-y-2">
              {leaderboardQuery.data.map((item, index) => (
                <div key={item.user_id} className="flex items-center justify-between gap-4 rounded-xl bg-stone-50 px-4 py-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white text-sm font-semibold">{index + 1}</span>
                    <div className="min-w-0">
                      <p className="truncate font-medium text-stone-950">{item.name}</p>
                      <p className="truncate text-sm text-stone-500">{item.level}</p>
                    </div>
                  </div>
                  <Badge className="shrink-0" tone="blue">{item.xp} XP</Badge>
                </div>
              ))}
            </div>
          )}
        </Card>
      </section>
    </>
  );
}

import { Achievement } from '../../entities/user/types';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

export function Achievements({ achievements }: { achievements: Achievement[] }) {
  return (
    <Card>
      <h3 className="mb-4 font-semibold text-stone-950">Достижения</h3>
      <div className="space-y-3">
        {achievements.length === 0 && <p className="text-sm text-stone-500">Пока нет достижений.</p>}
        {achievements.map((achievement) => (
          <div key={achievement.id} className="rounded-xl bg-stone-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="break-words font-medium text-stone-950">{achievement.title}</p>
                <p className="mt-1 text-sm leading-6 text-stone-500">{achievement.description}</p>
              </div>
              {achievement.unlocked_at ? <Badge className="w-fit" tone="green">Получено</Badge> : <Badge className="w-fit">Закрыто</Badge>}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

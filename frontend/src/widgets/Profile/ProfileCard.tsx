import { UserProfile } from '../../entities/user/types';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

export function ProfileCard({ profile }: { profile: UserProfile }) {
  return (
    <Card>
      <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
        <div className="min-w-0">
          <p className="text-sm text-stone-500">{profile.telegram_username ?? 'Telegram не указан'}</p>
          <h2 className="mt-1 break-words text-3xl font-semibold tracking-tight text-stone-950">{profile.name}</h2>
          <p className="mt-2 text-stone-600">{profile.role ?? 'Роль не указана'}</p>
          <p className="mt-1 text-sm text-stone-500">{profile.team ?? 'Без команды'} · {profile.timezone ?? 'часовой пояс не задан'}</p>
        </div>
        <div className="w-full rounded-2xl bg-stone-900 px-5 py-4 text-white md:w-auto md:min-w-44">
          <p className="text-xs uppercase tracking-[0.18em] text-stone-400">Уровень</p>
          <p className="mt-2 text-xl font-semibold">{profile.level ?? 'Участник'}</p>
          <p className="mt-1 text-sm text-stone-300">{profile.xp ?? 0} XP</p>
        </div>
      </div>

      {profile.skills && profile.skills.length > 0 && (
        <div className="mt-6 flex flex-wrap gap-2">
          {profile.skills.map((skill) => <Badge key={skill} tone="blue">{skill}</Badge>)}
        </div>
      )}
    </Card>
  );
}

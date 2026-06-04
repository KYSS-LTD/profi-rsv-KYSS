import { UserDigest } from '../../entities/user/types';
import { formatDate } from '../../shared/lib/date';
import { Card } from '../../shared/ui/Card';

export function PersonalDigest({ digest }: { digest: UserDigest }) {
  return (
    <Card>
      <p className="text-sm text-stone-500">Личный дайджест · {formatDate(digest.date)}</p>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <DigestCell label="На сегодня" value={digest.tasks_today.length} />
        <DigestCell label="Просрочено" value={digest.overdue_tasks.length} />
        <DigestCell label="Ближайшие" value={digest.upcoming_deadlines.length} />
      </div>
    </Card>
  );
}

function DigestCell({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-stone-50 p-4">
      <p className="text-sm text-stone-500">{label}</p>
      <p className="nums mt-2 font-display text-3xl font-bold leading-none text-stone-950">{value}</p>
    </div>
  );
}

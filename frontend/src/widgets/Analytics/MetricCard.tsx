import { ReactNode } from 'react';
import { Card } from '../../shared/ui/Card';

export function MetricCard({ label, value, note, icon }: { label: string; value: ReactNode; note?: string; icon?: ReactNode }) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm text-stone-500">{label}</p>
          <p className="mt-3 break-words text-3xl font-semibold tracking-tight text-stone-950">{value}</p>
        </div>
        {icon && <div className="shrink-0 rounded-xl bg-stone-100 p-3 text-stone-700">{icon}</div>}
      </div>
      {note && <p className="mt-3 text-sm leading-6 text-stone-500">{note}</p>}
    </Card>
  );
}

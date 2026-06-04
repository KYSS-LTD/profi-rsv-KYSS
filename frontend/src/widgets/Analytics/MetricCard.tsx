import { ReactNode } from 'react';
import { Card } from '../../shared/ui/Card';

export function MetricCard({ label, value, note, icon }: { label: string; value: ReactNode; note?: string; icon?: ReactNode }) {
  return (
    <Card className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words text-sm text-stone-500">{label}</p>
          <p className="nums mt-3 break-words font-display text-4xl font-bold leading-none text-stone-950">{value}</p>
        </div>
        {icon && (
          <div className="shrink-0 rounded-xl bg-gradient-to-br from-brand-50 to-brand-100 p-3 text-brand-600 shadow-sm ring-1 ring-inset ring-brand-200/70">{icon}</div>
        )}
      </div>
      {note && <p className="mt-3 text-sm leading-6 text-stone-500">{note}</p>}
    </Card>
  );
}

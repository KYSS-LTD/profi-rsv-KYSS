import type { ReactNode } from 'react';
import { Inbox } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex min-h-[220px] flex-col items-center justify-center rounded-[28px] border border-dashed border-slate-300 bg-tg-secondaryBg p-8 text-center dark:border-white/15">
      <Inbox className="mb-4 h-10 w-10 text-tg-hint" />
      <h3 className="text-lg font-bold text-tg-text">{title}</h3>
      <p className="mt-2 max-w-md text-sm text-tg-hint">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

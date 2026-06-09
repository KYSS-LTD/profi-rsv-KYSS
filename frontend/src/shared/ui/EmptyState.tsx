import { Inbox, LucideIcon } from 'lucide-react';
import { Card } from './Card';

export function EmptyState({ title, text, icon: Icon = Inbox }: { title: string; text?: string; icon?: LucideIcon }) {
  return (
    <Card className="flex flex-col items-center py-10 text-center animate-fade-in">
      <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-stone-100 text-stone-400">
        <Icon className="h-6 w-6" />
      </span>
      <h3 className="font-semibold text-stone-950">{title}</h3>
      {text && <p className="mt-2 max-w-md text-sm leading-6 text-stone-500">{text}</p>}
    </Card>
  );
}

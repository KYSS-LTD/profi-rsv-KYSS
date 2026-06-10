import { Card } from './Card';

export function Loader({ text = 'Загрузка...' }: { text?: string }) {
  return (
    <Card className="flex items-center gap-3 animate-fade-in">
      <span className="relative flex h-5 w-5 shrink-0">
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" />
      </span>
      <span className="text-sm font-medium text-stone-500">{text}</span>
    </Card>
  );
}

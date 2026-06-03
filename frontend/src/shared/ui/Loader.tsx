import { Card } from './Card';

export function Loader({ text = 'Загрузка...' }: { text?: string }) {
  return (
    <Card className="flex items-center gap-3">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-stone-200 border-t-stone-900" />
      <span className="text-sm text-stone-500">{text}</span>
    </Card>
  );
}

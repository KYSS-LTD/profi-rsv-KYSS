import { Card } from './Card';

export function EmptyState({ title, text }: { title: string; text?: string }) {
  return (
    <Card className="text-center">
      <h3 className="font-semibold text-stone-950">{title}</h3>
      {text && <p className="mt-2 text-sm leading-6 text-stone-500">{text}</p>}
    </Card>
  );
}

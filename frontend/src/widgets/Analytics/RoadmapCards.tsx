import { Map } from 'lucide-react';
import { RoadmapCard } from '../../entities/knowledge/types';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

const statusTone = {
  mock: 'blue',
  roadmap: 'neutral',
  'ready-for-demo': 'green',
} as const;

const statusLabel = {
  mock: 'Макет',
  roadmap: 'План',
  'ready-for-demo': 'Готово к демо',
} as const;

export function RoadmapCards({ cards }: { cards: RoadmapCard[] }) {
  return (
    <Card>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-stone-950">
          <Map className="h-5 w-5" />
          <h2 className="font-semibold">Блоки развития</h2>
        </div>
        <Badge tone="amber">P2</Badge>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {cards.map((card) => (
          <article key={card.id} className="rounded-xl border border-stone-200 bg-stone-50 p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              <Badge tone="amber">{card.priority}</Badge>
              <Badge tone={statusTone[card.status]}>{statusLabel[card.status]}</Badge>
            </div>
            <h3 className="break-words text-sm font-semibold text-stone-950">{card.title}</h3>
            <p className="mt-2 text-sm leading-6 text-stone-600">{card.description}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

import { BookOpen } from 'lucide-react';
import { KnowledgeItem } from '../../entities/knowledge/types';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

const sourceLabel: Record<KnowledgeItem['source_type'], string> = {
  meeting: 'Встреча',
  chat: 'Чат',
  task: 'Задача',
  note: 'Заметка',
};

export function KnowledgePreview({ items }: { items: KnowledgeItem[] }) {
  return (
    <Card>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-stone-950">
          <BookOpen className="h-5 w-5" />
          <h2 className="font-semibold">База знаний команды</h2>
        </div>
        <Badge tone="blue">Превью</Badge>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((item) => (
          <article key={item.id} className="rounded-xl border border-stone-200 bg-stone-50 p-4">
            <div className="mb-3 flex flex-wrap gap-2">
              <Badge>{sourceLabel[item.source_type]}</Badge>
              {item.tags?.slice(0, 2).map((tag) => <Badge key={tag} tone="blue">{tag}</Badge>)}
            </div>
            <h3 className="break-words text-sm font-semibold text-stone-950">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-stone-600">{item.content}</p>
          </article>
        ))}
      </div>
    </Card>
  );
}

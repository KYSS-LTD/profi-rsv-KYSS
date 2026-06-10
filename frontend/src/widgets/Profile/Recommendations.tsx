import { Recommendation } from '../../entities/user/types';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

const recommendationLabel: Record<Recommendation['recommendation_type'], string> = {
  course: 'Курс',
  skill: 'Навык',
  practice: 'Практика',
  documentation: 'Документация',
};

export function Recommendations({ recommendations }: { recommendations: Recommendation[] }) {
  return (
    <Card>
      <h3 className="mb-4 font-semibold text-stone-950">AI-рекомендации</h3>
      <div className="space-y-3">
        {recommendations.length === 0 && <p className="text-sm text-stone-500">Рекомендаций пока нет.</p>}
        {recommendations.map((item) => (
          <div key={item.id} className="rounded-xl bg-stone-50 p-4">
            <div className="mb-2 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <p className="break-words font-medium text-stone-950">{item.title}</p>
              <Badge className="w-fit">{recommendationLabel[item.recommendation_type]}</Badge>
            </div>
            <p className="text-sm leading-6 text-stone-500">{item.description}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

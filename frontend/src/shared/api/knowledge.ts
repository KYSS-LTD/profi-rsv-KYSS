import { KnowledgeItem, RoadmapCard } from '../../entities/knowledge/types';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export const roadmapCards: RoadmapCard[] = [
  {
    id: 'roadmap_knowledge',
    title: 'Вопросы к базе знаний',
    description: 'Сохранять summary встреч, решения и действия после созвона, а потом отвечать на вопросы команды по истории проекта.',
    priority: 'P2',
    status: 'ready-for-demo',
  },
  {
    id: 'roadmap_government',
    title: 'Режим поручений',
    description: 'Переключатель терминов: задача → поручение, исполнитель → ответственный, готово → исполнено. Дополнительно — журнал изменений.',
    priority: 'P2',
    status: 'roadmap',
  },
  {
    id: 'roadmap_recommendations',
    title: 'Рекомендации по навыкам',
    description: 'Анализировать повторяющиеся типы задач и показывать участнику зоны роста и рекомендации по развитию.',
    priority: 'P2',
    status: 'ready-for-demo',
  },
];

export async function getKnowledgePreview() {
  const response = await apiClient<ApiListResponse<KnowledgeItem>>('/knowledge', {
    params: { limit: 3 },
  });
  return unwrapItems(response);
}

export function getRoadmapCards() {
  return roadmapCards;
}

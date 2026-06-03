import { KnowledgeItem, RoadmapCard } from '../../entities/knowledge/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export const mockKnowledgeItems: KnowledgeItem[] = [
  {
    id: 'knowledge_1',
    title: 'Решение по канбан-адаптеру',
    content: 'Основная логика не зависит от конкретной доски: внешняя доска подключается через адаптер, а внутренняя доска остается запасным вариантом для демо.',
    source_type: 'meeting',
    source_id: 'meeting_1',
    tags: ['канбан', 'адаптер', 'резерв'],
    created_at: '2026-06-03T12:00:00+03:00',
  },
  {
    id: 'knowledge_2',
    title: 'Зона ответственности Ивана',
    content: 'Иван закрывает макет dashboard, мини-канбан, AI-предложения, summary встреч, аналитику, профиль и полировку демо.',
    source_type: 'note',
    tags: ['фронтенд', 'Иван', 'dashboard'],
    created_at: '2026-06-03T13:00:00+03:00',
  },
  {
    id: 'knowledge_3',
    title: 'Риск backend API',
    content: 'Если backend не готов, демо переключается на VITE_USE_MOCKS=true без изменения интерфейса.',
    source_type: 'meeting',
    source_id: 'meeting_1',
    tags: ['демо', 'резерв'],
    created_at: '2026-06-03T14:00:00+03:00',
  },
];

export const roadmapCards: RoadmapCard[] = [
  {
    id: 'roadmap_knowledge',
    title: 'Вопросы к базе знаний',
    description: 'Сохранять summary встреч, решения и действия после созвона, а потом отвечать на вопросы команды по истории проекта.',
    priority: 'P2',
    status: 'mock',
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
  if (env.useMocks) return mockKnowledgeItems;

  const response = await apiClient<ApiListResponse<KnowledgeItem>>('/knowledge', {
    params: { limit: 3 },
  });
  return unwrapItems(response);
}

export function getRoadmapCards() {
  return roadmapCards;
}

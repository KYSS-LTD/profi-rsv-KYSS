export type KnowledgeItem = {
  id: string;
  title: string;
  content: string;
  source_type: 'meeting' | 'chat' | 'task' | 'note';
  source_id?: string;
  tags?: string[];
  created_at?: string;
};

export type RoadmapCard = {
  id: string;
  title: string;
  description: string;
  priority: 'P1' | 'P2';
  status: 'mock' | 'roadmap' | 'ready-for-demo';
};

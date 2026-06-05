import { BarChart3, Bot, CalendarDays, KanbanSquare, PlugZap, UserRound, UsersRound } from 'lucide-react';

export const navigation = [
  { to: '/tasks', label: 'Задачи', description: 'Источник истины', icon: KanbanSquare },
  { to: '/employees', label: 'Сотрудники', description: 'RBAC и Telegram', icon: UsersRound },
  { to: '/boards', label: 'Интеграции', description: 'YouGile sync', icon: PlugZap },
  { to: '/suggestions', label: 'AI-предложения', description: 'Подтверждение задач', icon: Bot },
  { to: '/meetings', label: 'Встречи', description: 'Итоги и действия', icon: CalendarDays },
  { to: '/analytics', label: 'Аналитика', description: 'Метрики компании', icon: BarChart3 },
  { to: '/profile', label: 'Профиль', description: 'Моя рабочая зона', icon: UserRound },
];

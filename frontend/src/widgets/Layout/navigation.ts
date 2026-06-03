import { BarChart3, Bot, CalendarDays, LayoutDashboard, UserRound } from 'lucide-react';

export const navigation = [
  { to: '/tasks', label: 'Задачи', description: 'Мини-канбан', icon: LayoutDashboard },
  { to: '/suggestions', label: 'AI-предложения', description: 'Подтверждение задач', icon: Bot },
  { to: '/meetings', label: 'Встречи', description: 'Итоги и действия', icon: CalendarDays },
  { to: '/analytics', label: 'Аналитика', description: 'Метрики команды', icon: BarChart3 },
  { to: '/profile', label: 'Профиль', description: 'Моя рабочая зона', icon: UserRound },
];

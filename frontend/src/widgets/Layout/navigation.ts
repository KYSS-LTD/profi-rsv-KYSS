import { BarChart3, Bell, Bot, Building2, KanbanSquare, LayoutDashboard, PlugZap, Settings, UsersRound } from 'lucide-react';

export const navigation = [
  { to: '/dashboard', label: 'Dashboard', description: 'Картина компании', icon: LayoutDashboard },
  { to: '/ai-inbox', label: 'Входящие AI', description: 'Подтверждение задач', icon: Bot },
  { to: '/tasks', label: 'Задачи', description: 'Kanban Командуса', icon: KanbanSquare },
  { to: '/employees', label: 'Команда', description: 'Сотрудники и роли', icon: UsersRound },
  { to: '/departments', label: 'Отделы', description: 'Оргструктура', icon: Building2 },
  { to: '/analytics', label: 'Аналитика', description: 'Реальные метрики', icon: BarChart3 },
  { to: '/boards', label: 'Интеграции', description: 'Telegram / YouGile / OpenAI', icon: PlugZap },
  { to: '/notifications', label: 'Уведомления', description: 'События и риски', icon: Bell },
  { to: '/setup', label: 'Настройки', description: 'Setup Wizard', icon: Settings },
];

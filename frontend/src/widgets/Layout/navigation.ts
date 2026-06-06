import { BarChart3, Bell, Bot, Building2, KanbanSquare, LayoutDashboard, Network, PlugZap, Settings, UsersRound } from 'lucide-react';
import { Role } from '../../entities/saas/types';

export type NavigationItem = {
  to: string;
  label: string;
  description: string;
  icon: typeof LayoutDashboard;
  roles: Role[];
};

const managerRoles: Role[] = ['MANAGER'];
const adminRoles: Role[] = ['ADMIN'];
const ownerRoles: Role[] = ['OWNER'];
const observerRoles: Role[] = ['OBSERVER'];
const allRoles: Role[] = ['OWNER', 'ADMIN', 'MANAGER', 'EMPLOYEE', 'OBSERVER'];

export const navigation: NavigationItem[] = [
  { to: '/dashboard', label: 'Внимание', description: 'Что требует внимания', icon: LayoutDashboard, roles: allRoles },
  { to: '/org-map', label: 'Карта организации', description: 'Кто кому подчиняется', icon: Network, roles: allRoles },
  { to: '/tasks', label: 'Мои задачи', description: 'Личный Kanban', icon: KanbanSquare, roles: allRoles },
  { to: '/employees', label: 'Команда', description: 'Сотрудники в зоне доступа', icon: UsersRound, roles: [...managerRoles, ...adminRoles, ...ownerRoles] },
  { to: '/departments', label: 'Отдел', description: 'Оргструктура', icon: Building2, roles: [...managerRoles, ...adminRoles, ...ownerRoles] },
  { to: '/analytics', label: 'Аналитика', description: 'Метрики зоны доступа', icon: BarChart3, roles: [...managerRoles, ...adminRoles, ...ownerRoles, ...observerRoles] },
  { to: '/ai-inbox', label: 'Входящие AI', description: 'LLM-поток', icon: Bot, roles: [...adminRoles, ...ownerRoles] },
  { to: '/boards', label: 'Интеграции', description: 'Telegram / YouGile / OpenAI', icon: PlugZap, roles: [...adminRoles, ...ownerRoles] },
  { to: '/notifications', label: 'Уведомления', description: 'События и риски', icon: Bell, roles: [...managerRoles, ...adminRoles, ...ownerRoles] },
  { to: '/setup', label: 'Настройки', description: 'Setup Wizard', icon: Settings, roles: [...adminRoles, ...ownerRoles] },
];

export function navigationForRole(role?: Role) {
  if (!role) return [];
  return navigation.filter((item) => item.roles.includes(role));
}

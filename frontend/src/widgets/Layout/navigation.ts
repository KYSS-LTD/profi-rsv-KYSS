import { BarChart3, Bell, Bot, Building2, KanbanSquare, LayoutDashboard, PlugZap, Settings, UsersRound } from 'lucide-react';
import { Role } from '../../entities/saas/types';

export type NavigationItem = {
  to: string;
  label: string;
  description: string;
  icon: typeof LayoutDashboard;
  roles: Role[];
};

const employeeRoles: Role[] = ['EMPLOYEE'];
const teamLeadRoles: Role[] = ['TEAM_LEAD'];
const departmentManagerRoles: Role[] = ['DEPARTMENT_MANAGER'];
const ownerRoles: Role[] = ['SUPER_ADMIN', 'ORG_OWNER', 'MANAGER'];
const productRoles: Role[] = ['PRODUCT_MANAGER'];
const analyticsRoles: Role[] = ['SUPER_ADMIN', 'ORG_OWNER', 'MANAGER', 'DEPARTMENT_MANAGER', 'TEAM_LEAD', 'PRODUCT_MANAGER', 'VIEWER'];

export const navigation: NavigationItem[] = [
  { to: '/dashboard', label: 'Компания', description: 'Картина компании', icon: LayoutDashboard, roles: ownerRoles },
  { to: '/tasks', label: 'Мои задачи', description: 'Личный Kanban', icon: KanbanSquare, roles: [...employeeRoles, ...teamLeadRoles, ...departmentManagerRoles, ...ownerRoles, ...productRoles] },
  { to: '/employees', label: 'Команда', description: 'Сотрудники в зоне доступа', icon: UsersRound, roles: [...teamLeadRoles, ...departmentManagerRoles, ...ownerRoles] },
  { to: '/departments', label: 'Отдел', description: 'Оргструктура', icon: Building2, roles: [...departmentManagerRoles, ...ownerRoles] },
  { to: '/analytics', label: 'Аналитика', description: 'Метрики зоны доступа', icon: BarChart3, roles: analyticsRoles },
  { to: '/ai-inbox', label: 'Входящие AI', description: 'LLM-поток', icon: Bot, roles: [...productRoles, ...ownerRoles] },
  { to: '/boards', label: 'Интеграции', description: 'Telegram / YouGile / OpenAI', icon: PlugZap, roles: [...productRoles, ...ownerRoles] },
  { to: '/notifications', label: 'Уведомления', description: 'События и риски', icon: Bell, roles: [...teamLeadRoles, ...departmentManagerRoles, ...ownerRoles, ...productRoles] },
  { to: '/setup', label: 'Настройки', description: 'Setup Wizard', icon: Settings, roles: ownerRoles },
];

export function navigationForRole(role?: Role) {
  if (!role) return [];
  return navigation.filter((item) => item.roles.includes(role));
}

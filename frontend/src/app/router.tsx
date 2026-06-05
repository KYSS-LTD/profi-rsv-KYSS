import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './auth';
import { AppShell } from '../widgets/Layout/AppShell';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { AIInboxPage } from '../pages/AIInboxPage';
import { DashboardPage } from '../pages/DashboardPage';
import { DepartmentsPage } from '../pages/DepartmentsPage';
import { NotificationsPage } from '../pages/NotificationsPage';
import { SetupWizardPage } from '../pages/SetupWizardPage';
import { BoardsPage } from '../pages/BoardsPage';
import { EmployeesPage } from '../pages/EmployeesPage';
import { LoginPage } from '../pages/LoginPage';
import { MeetingsPage } from '../pages/MeetingsPage';
import { ProfilePage } from '../pages/ProfilePage';
import { SaasTasksPage } from '../pages/SaasTasksPage';
import { SuggestionsPage } from '../pages/SuggestionsPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <DashboardPage /> },
          { path: 'ai-inbox', element: <AIInboxPage /> },
          { path: 'tasks', element: <SaasTasksPage /> },
          { path: 'employees', element: <EmployeesPage /> },
          { path: 'departments', element: <DepartmentsPage /> },
          { path: 'boards', element: <BoardsPage /> },
          { path: 'suggestions', element: <SuggestionsPage /> },
          { path: 'meetings', element: <MeetingsPage /> },
          { path: 'analytics', element: <AnalyticsPage /> },
          { path: 'notifications', element: <NotificationsPage /> },
          { path: 'setup', element: <SetupWizardPage /> },
          { path: 'profile', element: <ProfilePage /> },
        ],
      },
    ],
  },
]);

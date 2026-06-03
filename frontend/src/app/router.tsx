import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from '../widgets/Layout/AppShell';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { MeetingsPage } from '../pages/MeetingsPage';
import { ProfilePage } from '../pages/ProfilePage';
import { SuggestionsPage } from '../pages/SuggestionsPage';
import { TasksPage } from '../pages/TasksPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/tasks" replace /> },
      { path: 'tasks', element: <TasksPage /> },
      { path: 'suggestions', element: <SuggestionsPage /> },
      { path: 'meetings', element: <MeetingsPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'profile', element: <ProfilePage /> },
    ],
  },
]);

import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from '@/widgets/layout/AppShell';
import { AnalyticsPage } from '@/pages/AnalyticsPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { MeetingsPage } from '@/pages/MeetingsPage';
import { ProfilePage } from '@/pages/ProfilePage';
import { SuggestionsPage } from '@/pages/SuggestionsPage';
import { TasksPage } from '@/pages/TasksPage';

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/suggestions" element={<SuggestionsPage />} />
        <Route path="/meetings" element={<MeetingsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

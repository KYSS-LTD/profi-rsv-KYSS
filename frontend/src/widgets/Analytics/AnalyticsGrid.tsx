import { Bot, CalendarCheck, CalendarClock, CheckCircle2, Clock, ListChecks, Mic, TimerReset, TrendingUp } from 'lucide-react';
import { TeamAnalytics } from '../../entities/analytics/types';
import { formatConfidence } from '../../entities/task/helpers';
import { MetricCard } from './MetricCard';

export function AnalyticsGrid({ analytics }: { analytics: TeamAnalytics }) {
  const avgConfidence = analytics.average_confidence ?? analytics.ai_quality?.average_confidence;
  const autoConfirmed = analytics.auto_confirmed ?? analytics.ai_quality?.auto_created;

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <MetricCard label="Задач создано AI" value={analytics.ai_created_tasks ?? 0} note="Сколько задач создал бот" icon={<Bot className="h-5 w-5" />} />
      <MetricCard label="Автосоздание" value={autoConfirmed ?? 0} note="Созданы без ручного заполнения" icon={<CheckCircle2 className="h-5 w-5" />} />
      <MetricCard label="Ждут подтверждения" value={analytics.waiting_confirmation ?? 0} note="Pending TaskCandidates" icon={<Clock className="h-5 w-5" />} />
      <MetricCard label="Отклонено" value={analytics.rejected_suggestions ?? analytics.ai_quality?.rejected_suggestions ?? 0} note="Отклоненные AI-предложения" icon={<TimerReset className="h-5 w-5" />} />
      <MetricCard label="Голос обработан" value={analytics.voice_messages_processed ?? 0} note="Voice messages / ASR" icon={<Mic className="h-5 w-5" />} />
      <MetricCard label="Средняя точность" value={formatConfidence(avgConfidence)} note="Уверенность AI extraction" icon={<TrendingUp className="h-5 w-5" />} />
      <MetricCard label="Встреч обработано" value={analytics.meetings_summarized ?? 0} note="Meeting summary" icon={<CalendarCheck className="h-5 w-5" />} />
      <MetricCard label="Готово за неделю" value={analytics.team_velocity?.done_this_week ?? analytics.done_tasks ?? 0} note="Закрытые задачи" icon={<ListChecks className="h-5 w-5" />} />
      <MetricCard label="Просрочки" value={`${analytics.team_velocity?.overdue_percent ?? 0}%`} note="Доля просроченных задач" icon={<CalendarClock className="h-5 w-5" />} />
    </div>
  );
}

import { ReactNode } from 'react';
import { CheckCircle2, CircleHelp, ListChecks, ShieldAlert, Sparkles } from 'lucide-react';
import { MeetingSummary as MeetingSummaryType } from '../../entities/meeting/types';
import { formatConfidence } from '../../entities/task/helpers';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';

type CreatedTaskItem =
  | NonNullable<MeetingSummaryType['created_tasks']>[number]
  | NonNullable<MeetingSummaryType['created_task_candidates']>[number];

export function MeetingSummary({ meeting }: { meeting: MeetingSummaryType }) {
  return (
    <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <Card className="xl:col-span-2">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <p className="text-sm text-stone-500">Краткие итоги</p>
            <h2 className="mt-1 break-words text-title font-semibold text-stone-950">{meeting.title ?? meeting.id}</h2>
          </div>
          {meeting.transcript_quality !== undefined && meeting.transcript_quality !== null && (
            <Badge className="w-fit" tone="green">Качество транскрипта {formatConfidence(meeting.transcript_quality)}</Badge>
          )}
        </div>
        <p className="text-base leading-7 text-stone-700">{meeting.summary}</p>
      </Card>

      <InfoCard title="Решения" icon={<CheckCircle2 className="h-5 w-5" />} items={meeting.decisions} />
      <ActionItemsCard meeting={meeting} />
      <CreatedTasksCard meeting={meeting} />
      <InfoCard title="Риски" icon={<ShieldAlert className="h-5 w-5" />} items={meeting.risks} />
      <InfoCard title="Открытые вопросы" icon={<CircleHelp className="h-5 w-5" />} items={meeting.open_questions} />
    </div>
  );
}

function InfoCard({ title, icon, items }: { title: string; icon: ReactNode; items: string[] }) {
  return (
    <Card>
      <div className="mb-4 flex items-center gap-2 text-stone-950">
        {icon}
        <h3 className="font-semibold">{title}</h3>
      </div>
      <div className="space-y-2">
        {items.length === 0 && <p className="text-sm text-stone-500">Нет данных.</p>}
        {items.map((item) => (
          <div key={item} className="rounded-xl bg-stone-50 px-4 py-3 text-sm leading-6 text-stone-600">{item}</div>
        ))}
      </div>
    </Card>
  );
}

function ActionItemsCard({ meeting }: { meeting: MeetingSummaryType }) {
  return (
    <Card>
      <div className="mb-4 flex items-center gap-2 text-stone-950">
        <ListChecks className="h-5 w-5" />
        <h3 className="font-semibold">Действия после встречи</h3>
      </div>
      <div className="space-y-2">
        {meeting.action_items.length === 0 && <p className="text-sm text-stone-500">Нет задач после встречи.</p>}
        {meeting.action_items.map((item) => (
          <div key={`${item.title}-${item.assignee}`} className="rounded-xl bg-stone-50 px-4 py-3">
            <p className="break-words text-sm font-medium text-stone-900">{item.title}</p>
            <p className="mt-1 text-xs text-stone-500">{item.assignee ?? 'Не назначен'} · {item.deadline ?? 'без срока'}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function CreatedTasksCard({ meeting }: { meeting: MeetingSummaryType }) {
  const createdTasks = meeting.created_tasks ?? meeting.created_task_candidates ?? [];

  return (
    <Card>
      <div className="mb-4 flex items-center gap-2 text-stone-950">
        <Sparkles className="h-5 w-5" />
        <h3 className="font-semibold">Созданные задачи</h3>
      </div>
      <div className="space-y-2">
        {createdTasks.length === 0 && <p className="text-sm text-stone-500">Пока нет задач, созданных из этой встречи.</p>}
        {createdTasks.map((item) => (
          <div key={item.id} className="rounded-xl bg-stone-50 px-4 py-3">
            <p className="break-words text-sm font-medium text-stone-900">{item.title}</p>
            <p className="mt-1 text-xs text-stone-500">{getCreatedTaskAssignee(item)} · {getCreatedTaskDeadline(item)}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function getCreatedTaskAssignee(item: CreatedTaskItem) {
  const candidateAssignee = (item as { assignee_raw?: string | null }).assignee_raw;
  const taskAssignee = (item as { assignee?: string | null }).assignee;
  return candidateAssignee ?? taskAssignee ?? 'Не назначен';
}

function getCreatedTaskDeadline(item: CreatedTaskItem) {
  const candidateDeadline = (item as { deadline_raw?: string | null }).deadline_raw;
  const taskDeadline = (item as { deadline?: string | null }).deadline;
  return candidateDeadline ?? taskDeadline ?? 'без срока';
}

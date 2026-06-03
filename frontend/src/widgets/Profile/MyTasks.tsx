import { Task } from '../../entities/task/types';
import { formatConfidence, sourceLabel, taskStatusLabel } from '../../entities/task/helpers';
import { formatDateTime } from '../../shared/lib/date';
import { Badge } from '../../shared/ui/Badge';
import { Card } from '../../shared/ui/Card';
import { EmptyState } from '../../shared/ui/EmptyState';

export function MyTasks({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return <EmptyState title="Нет моих задач" text="Когда backend вернет /tasks/my, задачи появятся здесь." />;
  }

  return (
    <Card>
      <h3 className="mb-4 font-semibold text-stone-950">Мои задачи</h3>
      <div className="space-y-3">
        {tasks.map((task) => (
          <div key={task.id} className="rounded-xl border border-stone-200 bg-stone-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="break-words font-medium text-stone-950">{task.title}</p>
                <p className="mt-1 text-sm text-stone-500">{formatDateTime(task.deadline)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge>{taskStatusLabel[task.status]}</Badge>
                <Badge>{sourceLabel[task.source]}</Badge>
                <Badge tone="blue">{formatConfidence(task.confidence)}</Badge>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

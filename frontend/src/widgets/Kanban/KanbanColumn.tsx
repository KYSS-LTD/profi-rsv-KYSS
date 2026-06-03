import { Task, TaskStatus } from '../../entities/task/types';
import { TaskCard } from './TaskCard';

export function KanbanColumn({
  column,
  tasks,
  onStatusChange,
  onReschedule,
  isUpdating,
}: {
  column: { key: TaskStatus; title: string; hint: string };
  tasks: Task[];
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string, deadline: string) => void;
  isUpdating?: boolean;
}) {
  return (
    <section className="min-w-0 rounded-[28px] border border-stone-200 bg-white p-5 shadow-sm shadow-stone-950/5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-stone-950">{column.title}</h2>
          <p className="mt-1 text-sm leading-5 text-stone-500">{column.hint}</p>
        </div>
        <span className="flex h-8 min-w-8 shrink-0 items-center justify-center rounded-xl border border-stone-200 bg-stone-50 px-2 text-sm font-medium text-stone-600">
          {tasks.length}
        </span>
      </div>

      <div className="grid gap-4">
        {tasks.length === 0 && (
          <div className="flex h-28 items-center justify-center rounded-2xl border border-dashed border-stone-200 bg-stone-50 text-sm text-stone-400">
            Пусто
          </div>
        )}
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            onStatusChange={onStatusChange}
            onReschedule={onReschedule}
            isUpdating={isUpdating}
          />
        ))}
      </div>
    </section>
  );
}

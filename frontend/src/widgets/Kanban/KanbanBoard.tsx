import { Task, TaskStatus } from '../../entities/task/types';
import { kanbanColumns } from '../../entities/task/helpers';
import { KanbanColumn } from './KanbanColumn';

export function KanbanBoard({
  tasks,
  onStatusChange,
  onReschedule,
  isUpdating,
}: {
  tasks: Task[];
  onStatusChange: (taskId: string, status: TaskStatus) => void;
  onReschedule: (taskId: string, deadline: string) => void;
  isUpdating?: boolean;
}) {
  return (
    <div className="overflow-x-auto pb-4">
      <div className="grid min-w-max grid-flow-col auto-cols-[340px] gap-4">
        {kanbanColumns.map((column) => (
          <KanbanColumn
            key={column.key}
            column={column}
            tasks={tasks.filter((task) => task.status === column.key)}
            onStatusChange={onStatusChange}
            onReschedule={onReschedule}
            isUpdating={isUpdating}
          />
        ))}
      </div>
    </div>
  );
}

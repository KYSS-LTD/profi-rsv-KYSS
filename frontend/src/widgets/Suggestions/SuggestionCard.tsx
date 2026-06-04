import { ExternalLink, Pencil, Save, X } from 'lucide-react';
import { ReactNode, useState } from 'react';
import { formatConfidence, priorityLabel, sourceLabel } from '../../entities/task/helpers';
import { TaskPriority } from '../../entities/task/types';
import { TaskCandidate } from '../../entities/candidate/types';
import { Badge } from '../../shared/ui/Badge';
import { Button } from '../../shared/ui/Button';
import { Card } from '../../shared/ui/Card';
import { Dropdown } from '../../shared/ui/Dropdown';
import { Input } from '../../shared/ui/Input';
import { Textarea } from '../../shared/ui/Textarea';

const priorities: TaskPriority[] = ['low', 'medium', 'high', 'critical'];

const candidateStatusLabel: Record<string, string> = {
  pending: 'Ждет подтверждения',
  confirmed: 'Подтверждено',
  rejected: 'Отклонено',
  created: 'Создано',
  duplicate: 'Дубликат',
};

export function SuggestionCard({
  candidate,
  onConfirm,
  onReject,
  isLoading,
}: {
  candidate: TaskCandidate;
  onConfirm: (candidate: TaskCandidate) => void;
  onReject: (candidateId: string) => void;
  isLoading?: boolean;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState(candidate);

  return (
    <Card>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          {isEditing ? (
            <Input value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
          ) : (
            <h3 className="break-words text-lg font-semibold tracking-tight text-stone-950">{draft.title}</h3>
          )}
          <p className="mt-2 text-sm text-stone-500">Точность AI: {formatConfidence(draft.confidence)}</p>
        </div>
        <Badge className="w-fit" tone={draft.confidence >= 0.85 ? 'green' : draft.confidence >= 0.55 ? 'amber' : 'red'}>
          {candidateStatusLabel[draft.status] ?? draft.status}
        </Badge>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-3">
        <Field label="Ответственный">
          {isEditing ? (
            <Input value={draft.assignee_raw ?? ''} onChange={(event) => setDraft({ ...draft, assignee_raw: event.target.value })} />
          ) : (
            <span>{draft.assignee_raw ?? 'Не определен'}</span>
          )}
        </Field>
        <Field label="Дедлайн">
          {isEditing ? (
            <Input value={draft.deadline_raw ?? ''} onChange={(event) => setDraft({ ...draft, deadline_raw: event.target.value })} />
          ) : (
            <span>{draft.deadline_raw ?? 'Не указан'}</span>
          )}
        </Field>
        <Field label="Приоритет">
          {isEditing ? (
            <Dropdown
              ariaLabel="Приоритет"
              value={draft.priority}
              onChange={(value) => setDraft({ ...draft, priority: value as TaskPriority })}
              options={priorities.map((priority) => ({ value: priority, label: priorityLabel[priority] }))}
            />
          ) : (
            <span>{priorityLabel[draft.priority]}</span>
          )}
        </Field>
      </div>

      {isEditing ? (
        <Textarea
          value={draft.description ?? ''}
          onChange={(event) => setDraft({ ...draft, description: event.target.value })}
          placeholder="Описание задачи"
        />
      ) : (
        draft.description && <p className="mb-4 text-sm leading-6 text-stone-600">{draft.description}</p>
      )}

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge>{sourceLabel[draft.source]}</Badge>
        {draft.missing_fields?.map((field) => (
          <Badge key={field} tone="amber">Не хватает: {field}</Badge>
        ))}
      </div>

      {draft.source_excerpt && <p className="mb-4 rounded-xl bg-stone-50 p-3 text-sm leading-6 text-stone-500">«{draft.source_excerpt}»</p>}

      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <Button disabled={isLoading} onClick={() => onConfirm(draft)}>
          <Save className="h-4 w-4" />
          Создать
        </Button>
        <Button variant="danger" disabled={isLoading} onClick={() => onReject(draft.id)}>
          <X className="h-4 w-4" />
          Отклонить
        </Button>
        <Button variant="secondary" disabled={isLoading} onClick={() => setIsEditing((value) => !value)}>
          <Pencil className="h-4 w-4" />
          {isEditing ? 'Готово' : 'Изменить'}
        </Button>
        {draft.source_message_url && (
          <a
            href={draft.source_message_url}
            target="_blank"
            rel="noreferrer"
            className="focus-ring inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-xl border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-800 transition hover:border-stone-300 hover:bg-stone-50"
          >
            <ExternalLink className="h-4 w-4" />
            Источник
          </a>
        )}
      </div>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-1 text-xs font-medium text-stone-500">
      {label}
      <span className="min-w-0 break-words text-sm font-medium text-stone-900">{children}</span>
    </label>
  );
}

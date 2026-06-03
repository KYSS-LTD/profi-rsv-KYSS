import { FormEvent, useState } from 'react';
import { Note } from '../../entities/user/types';
import { Button } from '../../shared/ui/Button';
import { Card } from '../../shared/ui/Card';
import { Input } from '../../shared/ui/Input';
import { Textarea } from '../../shared/ui/Textarea';

const noteSourceLabel: Record<Note['source'], string> = {
  manual: 'Вручную',
  meeting: 'Из встречи',
  ai_summary: 'AI summary',
};

export function Notes({
  notes,
  onCreate,
  onDelete,
  isLoading,
}: {
  notes: Note[];
  onCreate: (payload: Pick<Note, 'title' | 'content' | 'source'>) => void;
  onDelete: (noteId: string) => void;
  isLoading?: boolean;
}) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !content.trim()) return;

    onCreate({ title, content, source: 'manual' });
    setTitle('');
    setContent('');
  }

  return (
    <Card>
      <h3 className="mb-4 font-semibold text-stone-950">Заметки</h3>
      <form className="mb-5 grid gap-2" onSubmit={handleSubmit}>
        <Input placeholder="Заголовок" value={title} onChange={(event) => setTitle(event.target.value)} />
        <Textarea placeholder="Текст заметки" value={content} onChange={(event) => setContent(event.target.value)} />
        <Button className="w-full sm:w-fit" type="submit" disabled={isLoading || !title.trim() || !content.trim()}>Добавить заметку</Button>
      </form>

      <div className="space-y-3">
        {notes.length === 0 && <p className="text-sm text-stone-500">Заметок пока нет.</p>}
        {notes.map((note) => (
          <div key={note.id} className="rounded-xl bg-stone-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <p className="break-words font-medium text-stone-950">{note.title}</p>
                <p className="mt-1 text-sm leading-6 text-stone-500">{note.content}</p>
                <p className="mt-2 text-xs text-stone-400">{noteSourceLabel[note.source]}</p>
              </div>
              <Button className="w-full sm:w-auto" variant="ghost" disabled={isLoading} onClick={() => onDelete(note.id)}>Удалить</Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

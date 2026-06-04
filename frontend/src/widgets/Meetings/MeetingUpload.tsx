import { Paperclip, Upload, X } from 'lucide-react';
import { useState } from 'react';
import { env } from '../../shared/config/env';
import { cn } from '../../shared/lib/cn';
import { Button } from '../../shared/ui/Button';
import { Card } from '../../shared/ui/Card';
import { Input } from '../../shared/ui/Input';

export function MeetingUpload({
  onUpload,
  isLoading,
}: {
  onUpload: (file: File, teamId: string, title: string) => void;
  isLoading?: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('Ежедневная встреча');
  const [teamId, setTeamId] = useState(env.defaultTeamId);

  return (
    <Card>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold text-stone-950">Загрузка записи встречи</h2>
          <p className="mt-1 text-sm leading-6 text-stone-500">Фронт отправляет audio-файл в backend и открывает готовые итоги.</p>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_180px_220px_auto] lg:items-end">
        <label className="grid gap-1.5 text-xs font-medium text-stone-500">
          Файл встречи
          <span className="group flex h-10 cursor-pointer items-center overflow-hidden rounded-xl border border-stone-200 bg-white transition-colors hover:border-stone-300 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-500 focus-within:ring-offset-2 focus-within:ring-offset-stone-50">
            <input
              type="file"
              accept="audio/*"
              className="sr-only"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
            <span className="flex h-full shrink-0 items-center gap-2 bg-stone-100 px-3 text-sm font-semibold text-stone-700 transition-colors group-hover:bg-stone-200">
              <Paperclip className="h-4 w-4" />
              Выбрать файл
            </span>
            <span className={cn('min-w-0 flex-1 truncate px-3 text-sm', file ? 'font-medium text-stone-800' : 'text-stone-400')}>
              {file ? file.name : 'Файл не выбран'}
            </span>
            {file && (
              <button
                type="button"
                onClick={(event) => {
                  event.preventDefault();
                  setFile(null);
                }}
                className="mr-1.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-700"
                aria-label="Очистить выбранный файл"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </span>
        </label>
        <label className="grid gap-1 text-xs font-medium text-stone-500">
          Команда
          <Input value={teamId} onChange={(event) => setTeamId(event.target.value)} />
        </label>
        <label className="grid gap-1 text-xs font-medium text-stone-500">
          Название
          <Input value={title} onChange={(event) => setTitle(event.target.value)} />
        </label>
        <Button className="w-full lg:w-auto" disabled={!file || isLoading} onClick={() => file && onUpload(file, teamId, title)}>
          <Upload className="h-4 w-4" />
          Загрузить
        </Button>
      </div>
    </Card>
  );
}

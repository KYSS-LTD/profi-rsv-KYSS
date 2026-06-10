import { Upload } from 'lucide-react';
import { useState } from 'react';
import { env } from '../../shared/config/env';
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
        <label className="grid gap-1 text-xs font-medium text-stone-500">
          Файл встречи
          <Input type="file" accept="audio/*" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
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

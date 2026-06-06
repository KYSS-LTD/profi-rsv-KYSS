import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { FileAudio, UploadCloud } from 'lucide-react';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { Loader } from '@/shared/ui/Loader';
import { PageHeader } from '@/shared/ui/PageHeader';
import { haptic } from '@/shared/lib/telegram';

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
      <h3 className="font-black text-tg-text">{title}</h3>
      <ul className="mt-3 grid gap-2 text-sm leading-6 text-tg-hint">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}

export function MeetingsPage() {
  const [meetingId, setMeetingId] = useState('meeting-demo');
  const { data: summary, isLoading, refetch } = useQuery({ queryKey: ['meeting-summary', meetingId], queryFn: () => api.getMeetingSummary(meetingId) });
  const upload = useMutation({
    mutationFn: api.uploadMeeting,
    onSuccess: (data) => {
      haptic.success();
      setMeetingId(data.id);
      requestAnimationFrame(() => refetch());
    },
  });

  return (
    <section>
      <PageHeader
        eyebrow="Meeting Summary"
        title="Встречи и summaries"
        description="Загрузка аудио встречи, просмотр summary, решений, action items, рисков и Knowledge Base preview."
        action={
          <label className="cursor-pointer">
            <input
              className="hidden"
              type="file"
              accept="audio/*,video/*"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                if (file) upload.mutate(file);
              }}
            />
            <span className="inline-flex items-center justify-center gap-2 rounded-2xl bg-tg-button px-4 py-3 text-sm font-semibold text-tg-buttonText shadow-soft transition active:scale-[0.98]">
              <UploadCloud className="h-4 w-4" /> Upload audio
            </span>
          </label>
        }
      />

      {upload.isPending && <Card className="mb-4"><p className="text-sm font-semibold text-tg-hint">Загружаю и обрабатываю файл…</p></Card>}
      {isLoading && <Loader />}

      {summary && !isLoading && (
        <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <Card>
            <div className="flex items-start justify-between gap-3">
              <div>
                <Badge tone="green">Transcript quality {Math.round(summary.transcriptQuality * 100)}%</Badge>
                <h2 className="mt-4 text-2xl font-black text-tg-text">{summary.title}</h2>
              </div>
              <FileAudio className="h-9 w-9 text-tg-link" />
            </div>
            <p className="mt-4 text-sm leading-6 text-tg-hint">{summary.shortSummary}</p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
                <p className="text-xs text-tg-hint">Created tasks</p>
                <p className="mt-1 text-3xl font-black text-tg-text">{summary.createdTasks}</p>
              </div>
              <div className="rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
                <p className="text-xs text-tg-hint">Candidates</p>
                <p className="mt-1 text-3xl font-black text-tg-text">{summary.createdCandidates}</p>
              </div>
            </div>
          </Card>

          <div className="grid gap-4">
            <ListBlock title="Decisions" items={summary.decisions} />
            <ListBlock title="Action items" items={summary.actionItems} />
            <ListBlock title="Risks" items={summary.risks} />
            <ListBlock title="Open questions" items={summary.openQuestions} />
            <Card>
              <Badge tone="purple">Knowledge Base preview</Badge>
              <div className="mt-4 grid gap-3">
                {summary.knowledgePreview.map((item) => (
                  <div key={item} className="rounded-2xl bg-slate-100 p-3 text-sm leading-6 text-tg-hint dark:bg-white/10">{item}</div>
                ))}
              </div>
              <Button className="mt-4" variant="secondary" onClick={() => haptic.tap()}>Сохранить в KB</Button>
            </Card>
          </div>
        </div>
      )}
    </section>
  );
}

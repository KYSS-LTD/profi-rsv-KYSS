import { useMutation, useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { env } from '../shared/config/env';
import { getMeetingSummary, uploadMeeting } from '../shared/api/meetings';
import { getKnowledgePreview } from '../shared/api/knowledge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { ErrorState } from '../shared/ui/ErrorState';
import { Input } from '../shared/ui/Input';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { MeetingSummary } from '../widgets/Meetings/MeetingSummary';
import { MeetingUpload } from '../widgets/Meetings/MeetingUpload';
import { KnowledgePreview } from '../widgets/Meetings/KnowledgePreview';

export function MeetingsPage() {
  const [meetingId, setMeetingId] = useState(env.defaultMeetingId);
  const [requestedMeetingId, setRequestedMeetingId] = useState(env.defaultMeetingId);

  const meetingQuery = useQuery({
    queryKey: ['meeting-summary', requestedMeetingId],
    queryFn: () => getMeetingSummary(requestedMeetingId),
    enabled: Boolean(requestedMeetingId),
  });

  const knowledgeQuery = useQuery({ queryKey: ['knowledge-preview'], queryFn: getKnowledgePreview });

  const uploadMutation = useMutation({
    mutationFn: ({ file, teamId, title }: { file: File; teamId: string; title: string }) => uploadMeeting(file, teamId, title),
    onSuccess: (response) => {
      setMeetingId(response.meeting_id);
      setRequestedMeetingId(response.meeting_id);
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Голос / Встречи"
        title="Итоги встречи"
        description="Загрузка аудио, просмотр решений, действий после встречи, рисков, открытых вопросов и задач, созданных из встречи."
      />

      <div className="mb-4 grid gap-4">
        <MeetingUpload onUpload={(file, teamId, title) => uploadMutation.mutate({ file, teamId, title })} isLoading={uploadMutation.isPending} />

        <Card className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
          <label className="grid gap-1 text-xs font-medium text-stone-500">
            ID встречи
            <Input value={meetingId} onChange={(event) => setMeetingId(event.target.value)} placeholder="meeting_id" />
          </label>
          <Button className="w-full sm:w-auto" onClick={() => setRequestedMeetingId(meetingId)} disabled={!meetingId.trim()}>
            Открыть итоги
          </Button>
        </Card>
      </div>

      {uploadMutation.error && <div className="mb-4"><ErrorState error={uploadMutation.error} /></div>}
      {meetingQuery.isLoading && <Loader text="Загружаем итоги встречи..." />}
      {meetingQuery.error && <ErrorState error={meetingQuery.error} />}
      {meetingQuery.data && <MeetingSummary meeting={meetingQuery.data} />}

      {knowledgeQuery.data && <section className="mt-6"><KnowledgePreview items={knowledgeQuery.data} /></section>}
    </>
  );
}

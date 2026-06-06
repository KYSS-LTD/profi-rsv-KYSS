import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, ExternalLink, PencilLine, X } from 'lucide-react';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Button } from '@/shared/ui/Button';
import { Card } from '@/shared/ui/Card';
import { EmptyState } from '@/shared/ui/EmptyState';
import { Loader } from '@/shared/ui/Loader';
import { PageHeader } from '@/shared/ui/PageHeader';
import { haptic } from '@/shared/lib/telegram';

export function SuggestionsPage() {
  const queryClient = useQueryClient();
  const { data: candidates = [], isLoading } = useQuery({ queryKey: ['candidates'], queryFn: api.getCandidates });

  const confirm = useMutation({
    mutationFn: api.confirmCandidate,
    onSuccess: () => {
      haptic.success();
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  const reject = useMutation({
    mutationFn: api.rejectCandidate,
    onSuccess: () => {
      haptic.warning();
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
    },
  });

  return (
    <section>
      <PageHeader
        eyebrow="AI Suggestions"
        title="Кандидаты в задачи"
        description="AI предлагает action items из Telegram-чата, voice messages и meeting summaries. Подтверждение превращает candidate в обычную задачу."
      />

      {isLoading && <Loader />}

      {!isLoading && candidates.length === 0 && (
        <EmptyState title="Нет pending suggestions" description="Все AI-кандидаты уже подтверждены или отклонены. Новые появятся после обработки чата или встречи." />
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {candidates.map((candidate) => (
          <Card key={candidate.id}>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="purple">{Math.round(candidate.confidence * 100)}% confidence</Badge>
              <Badge tone="blue">{candidate.source}</Badge>
              {candidate.suggestedDeadline && <Badge tone="yellow">до {candidate.suggestedDeadline}</Badge>}
            </div>
            <h2 className="mt-4 text-xl font-black text-tg-text">{candidate.title}</h2>
            <p className="mt-2 text-sm leading-6 text-tg-hint">{candidate.description}</p>
            <blockquote className="mt-4 rounded-3xl border-l-4 border-tg-button bg-slate-100 p-4 text-sm italic leading-6 text-tg-hint dark:bg-white/10">
              “{candidate.excerpt}”
            </blockquote>
            <div className="mt-4 grid gap-2 text-sm text-tg-hint sm:grid-cols-2">
              <div className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">
                Assignee: <strong className="text-tg-text">{candidate.suggestedAssignee || 'не назначен'}</strong>
              </div>
              <div className="rounded-2xl bg-slate-100 p-3 dark:bg-white/10">
                Status: <strong className="text-tg-text">{candidate.status}</strong>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button disabled={confirm.isPending} onClick={() => confirm.mutate(candidate.id)}>
                <Check className="h-4 w-4" /> Confirm
              </Button>
              <Button variant="danger" disabled={reject.isPending} onClick={() => reject.mutate(candidate.id)}>
                <X className="h-4 w-4" /> Reject
              </Button>
              <Button variant="secondary" onClick={() => haptic.tap()}>
                <PencilLine className="h-4 w-4" /> Edit locally
              </Button>
              <Button variant="ghost" onClick={() => haptic.tap()}>
                <ExternalLink className="h-4 w-4" /> Source
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}

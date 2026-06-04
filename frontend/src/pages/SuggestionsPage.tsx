import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { TaskCandidate } from '../entities/candidate/types';
import { env } from '../shared/config/env';
import { confirmCandidate, getTaskCandidates, rejectCandidate } from '../shared/api/candidates';
import { ErrorState } from '../shared/ui/ErrorState';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { SuggestionsList } from '../widgets/Suggestions/SuggestionsList';

export function SuggestionsPage() {
  const queryClient = useQueryClient();

  const candidatesQuery = useQuery({ queryKey: ['task-candidates'], queryFn: getTaskCandidates });

  const confirmMutation = useMutation({
    mutationFn: (candidate: TaskCandidate) =>
      confirmCandidate(candidate.id, {
        confirmed_by: env.defaultUserId,
        overrides: {
          title: candidate.title,
          description: candidate.description,
          deadline: candidate.deadline,
          assignee_raw: candidate.assignee_raw,
          priority: candidate.priority,
        },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['task-candidates'] });
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (candidateId: string) => rejectCandidate(candidateId, { rejected_by: env.defaultUserId, reason: 'not_a_task' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['task-candidates'] }),
  });

  return (
    <>
      <PageHeader
        eyebrow="AI-извлечение"
        title="AI-предложения"
        description="Кандидаты задач со статусом pending: можно подтвердить, отклонить или поправить перед созданием карточки."
      />

      {candidatesQuery.isLoading && <Loader text="Загружаем AI-предложения..." />}
      {candidatesQuery.error && <ErrorState error={candidatesQuery.error} />}
      {candidatesQuery.data && (
        <SuggestionsList
          candidates={candidatesQuery.data}
          onConfirm={(candidate) => confirmMutation.mutate(candidate)}
          onReject={(candidateId) => rejectMutation.mutate(candidateId)}
          isLoading={confirmMutation.isPending || rejectMutation.isPending}
        />
      )}
    </>
  );
}

import { TaskCandidate } from '../../entities/candidate/types';
import { EmptyState } from '../../shared/ui/EmptyState';
import { SuggestionCard } from './SuggestionCard';

export function SuggestionsList({
  candidates,
  onConfirm,
  onReject,
  isLoading,
}: {
  candidates: TaskCandidate[];
  onConfirm: (candidate: TaskCandidate) => void;
  onReject: (candidateId: string) => void;
  isLoading?: boolean;
}) {
  if (candidates.length === 0) {
    return <EmptyState title="Нет AI-предложений" text="Когда backend вернет pending TaskCandidates, они появятся здесь." />;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {candidates.map((candidate) => (
        <SuggestionCard key={candidate.id} candidate={candidate} onConfirm={onConfirm} onReject={onReject} isLoading={isLoading} />
      ))}
    </div>
  );
}

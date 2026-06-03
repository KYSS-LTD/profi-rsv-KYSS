import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getMyTasks } from '../shared/api/tasks';
import { createNote, deleteNote, getAchievements, getNotes, getProfile, getRecommendations, getUserDigest } from '../shared/api/profile';
import { env } from '../shared/config/env';
import { ErrorState } from '../shared/ui/ErrorState';
import { Loader } from '../shared/ui/Loader';
import { PageHeader } from '../shared/ui/PageHeader';
import { Achievements } from '../widgets/Profile/Achievements';
import { MyTasks } from '../widgets/Profile/MyTasks';
import { Notes } from '../widgets/Profile/Notes';
import { PersonalDigest } from '../widgets/Profile/PersonalDigest';
import { ProfileCard } from '../widgets/Profile/ProfileCard';
import { Recommendations } from '../widgets/Profile/Recommendations';

export function ProfilePage() {
  const queryClient = useQueryClient();

  const profileQuery = useQuery({ queryKey: ['profile'], queryFn: getProfile });
  const myTasksQuery = useQuery({ queryKey: ['my-tasks'], queryFn: getMyTasks });
  const digestQuery = useQuery({ queryKey: ['digest', env.defaultUserId], queryFn: () => getUserDigest(env.defaultUserId) });
  const notesQuery = useQuery({ queryKey: ['notes'], queryFn: getNotes });
  const achievementsQuery = useQuery({ queryKey: ['achievements', env.defaultUserId], queryFn: () => getAchievements(env.defaultUserId) });
  const recommendationsQuery = useQuery({ queryKey: ['recommendations', env.defaultUserId], queryFn: () => getRecommendations(env.defaultUserId) });

  const createNoteMutation = useMutation({ mutationFn: createNote, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notes'] }) });
  const deleteNoteMutation = useMutation({ mutationFn: deleteNote, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notes'] }) });

  const isLoading = profileQuery.isLoading || myTasksQuery.isLoading || digestQuery.isLoading;
  const error = profileQuery.error ?? myTasksQuery.error ?? digestQuery.error;

  return (
    <>
      <PageHeader
        eyebrow="Личная зона"
        title="Профиль"
        description="Мои задачи, дедлайны, дайджест, заметки, достижения и рекомендации по развитию."
      />

      {isLoading && <Loader text="Загружаем профиль..." />}
      {error && <ErrorState error={error} />}

      {profileQuery.data && (
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="grid gap-4">
            <ProfileCard profile={profileQuery.data} />
            {digestQuery.data && <PersonalDigest digest={digestQuery.data} />}
            {myTasksQuery.data && <MyTasks tasks={myTasksQuery.data} />}
          </div>

          <div className="grid gap-4">
            {achievementsQuery.data && <Achievements achievements={achievementsQuery.data} />}
            {recommendationsQuery.data && <Recommendations recommendations={recommendationsQuery.data} />}
            {notesQuery.data && (
              <Notes
                notes={notesQuery.data}
                onCreate={(payload) => createNoteMutation.mutate(payload)}
                onDelete={(noteId) => deleteNoteMutation.mutate(noteId)}
                isLoading={createNoteMutation.isPending || deleteNoteMutation.isPending}
              />
            )}
          </div>
        </div>
      )}
    </>
  );
}

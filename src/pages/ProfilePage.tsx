import { useQuery } from '@tanstack/react-query';
import { Award, Lightbulb, StickyNote, UserRound } from 'lucide-react';
import { api } from '@/shared/api/client';
import { Badge } from '@/shared/ui/Badge';
import { Card } from '@/shared/ui/Card';
import { Loader } from '@/shared/ui/Loader';
import { PageHeader } from '@/shared/ui/PageHeader';
import { getTelegramUser } from '@/shared/lib/telegram';

export function ProfilePage() {
  const telegramUser = getTelegramUser();
  const { data: profile, isLoading } = useQuery({ queryKey: ['profile'], queryFn: api.getProfile });

  if (isLoading) {
    return (
      <section>
        <PageHeader eyebrow="My Profile" title="Профиль" description="Личный контекст участника команды." />
        <Loader />
      </section>
    );
  }

  const name = telegramUser ? `${telegramUser.first_name}${telegramUser.last_name ? ` ${telegramUser.last_name}` : ''}` : profile?.name;
  const username = telegramUser?.username ? `@${telegramUser.username}` : profile?.telegram;

  return (
    <section>
      <PageHeader
        eyebrow="My Profile"
        title="Профиль участника"
        description="Telegram user, персональные рекомендации, achievements и notes. Эти блоки подходят для P1/P2 demo roadmap."
      />

      <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
        <Card>
          <div className="flex items-center gap-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-[28px] bg-tg-button text-tg-buttonText">
              <UserRound className="h-10 w-10" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-tg-text">{name}</h2>
              <p className="mt-1 text-sm text-tg-hint">{username || 'Telegram username hidden'}</p>
              <Badge className="mt-3" tone="blue">{profile?.role}</Badge>
            </div>
          </div>
          <div className="mt-5 rounded-3xl bg-slate-100 p-4 dark:bg-white/10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-tg-hint">Focus</p>
            <p className="mt-2 text-sm leading-6 text-tg-text">{profile?.focus}</p>
          </div>
        </Card>

        <div className="grid gap-4">
          <Card>
            <div className="flex items-center gap-2">
              <Award className="h-5 w-5 text-tg-link" />
              <h2 className="text-xl font-black text-tg-text">Achievements</h2>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {profile?.achievements.map((item) => <Badge key={item} tone="purple">{item}</Badge>)}
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-tg-link" />
              <h2 className="text-xl font-black text-tg-text">Skill recommendations</h2>
            </div>
            <div className="mt-4 grid gap-3">
              {profile?.recommendations.map((item) => (
                <div key={item} className="rounded-2xl bg-slate-100 p-3 text-sm leading-6 text-tg-hint dark:bg-white/10">{item}</div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-2">
              <StickyNote className="h-5 w-5 text-tg-link" />
              <h2 className="text-xl font-black text-tg-text">My notes</h2>
            </div>
            <div className="mt-4 grid gap-3">
              {profile?.notes.map((item) => (
                <div key={item} className="rounded-2xl bg-slate-100 p-3 text-sm leading-6 text-tg-hint dark:bg-white/10">{item}</div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}

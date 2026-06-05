import { useMutation } from '@tanstack/react-query';
import { CheckCircle2, Columns3, KeyRound, Link2, Lock, UsersRound } from 'lucide-react';
import { FormEvent, useState } from 'react';
import { verifyYouGile } from '../shared/api/boardsV2';
import { Badge } from '../shared/ui/Badge';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';
import { PageHeader } from '../shared/ui/PageHeader';

const lifecycle = [
  { status: 'TO_DO', label: 'К выполнению' },
  { status: 'IN_PROGRESS', label: 'В работе' },
  { status: 'REVIEW', label: 'Ревью' },
  { status: 'DONE', label: 'Готово' },
];

export function BoardsPage() {
  const [token, setToken] = useState('');
  const verifyMutation = useMutation({ mutationFn: () => verifyYouGile(token) });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    verifyMutation.mutate();
  }

  const integration = verifyMutation.data;

  return (
    <>
      <PageHeader
        eyebrow="Event-driven интеграции"
        title="YouGile и доски"
        description="Командус остается источником истины. YouGile используется как внешнее отображение задач через provider abstraction, маппинги колонок и идемпотентные webhooks."
      />

      <section className="grid gap-6 xl:grid-cols-[460px_1fr]">
        <Card>
          <div className="mb-5 flex items-start gap-3">
            <div className="rounded-2xl bg-stone-900 p-3 text-white"><KeyRound className="h-5 w-5" /></div>
            <div>
              <h2 className="font-semibold text-stone-950">Подключить YouGile</h2>
              <p className="mt-1 text-sm leading-6 text-stone-500">API Token проверяется backend-ом и хранится только в зашифрованном виде через Fernet.</p>
            </div>
          </div>
          <form className="space-y-4" onSubmit={onSubmit}>
            <Input type="password" value={token} onChange={(event) => setToken(event.target.value)} placeholder="YouGile API Token" minLength={8} required />
            <Button className="w-full" type="submit" disabled={verifyMutation.isPending}>{verifyMutation.isPending ? 'Проверяем...' : 'Проверить и подключить'}</Button>
          </form>
          {verifyMutation.error && <p className="mt-4 rounded-xl bg-red-50 px-3 py-2 text-sm text-red-700">{verifyMutation.error.message}</p>}
          {integration && <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800"><CheckCircle2 className="mb-2 h-5 w-5" />Интеграция создана: {integration.name}</div>}
        </Card>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <div className="mb-4 flex items-center gap-3"><Columns3 className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Маппинг колонок</h2></div>
            <div className="space-y-3">
              {lifecycle.map((item) => (
                <div key={item.status} className="flex items-center justify-between gap-4 rounded-2xl bg-stone-50 px-4 py-3">
                  <div><p className="font-medium text-stone-900">{item.label}</p><p className="text-xs text-stone-500">{item.status}</p></div>
                  <Badge tone="blue">YouGile column</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="mb-4 flex items-center gap-3"><UsersRound className="h-5 w-5 text-stone-500" /><h2 className="font-semibold text-stone-950">Маппинг пользователей</h2></div>
            <p className="text-sm leading-6 text-stone-500">Сотрудник связывается с пользователем YouGile по email или ручному external user id. Backend хранит связь в `EmployeeBoardMapping`.</p>
            <div className="mt-5 rounded-2xl bg-stone-950 p-4 text-white">
              <Link2 className="mb-3 h-5 w-5 text-emerald-300" />
              <p className="text-sm font-medium">После подтверждения задачи Celery отправит событие синхронизации в provider.</p>
            </div>
          </Card>

          <Card className="lg:col-span-2">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-amber-50 p-3 text-amber-700"><Lock className="h-5 w-5" /></div>
              <div>
                <h2 className="font-semibold text-stone-950">Webhook security</h2>
                <p className="mt-2 text-sm leading-6 text-stone-500">Входящие события проходят через `/api/v2/boards/yougile/webhook`; повторные события блокируются таблицей `ProcessedWebhookEvent` до изменения task lifecycle.</p>
              </div>
            </div>
          </Card>
        </div>
      </section>
    </>
  );
}

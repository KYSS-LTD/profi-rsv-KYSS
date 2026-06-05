import { useMutation, useQueryClient } from '@tanstack/react-query';
import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changePassword } from '../shared/api/authV2';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Input } from '../shared/ui/Input';

export function ChangePasswordPage() {
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => changePassword(password),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      navigate('/tasks', { replace: true });
    },
  });

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirmation) {
      setValidationError('Пароли не совпадают');
      return;
    }
    setValidationError(null);
    mutation.mutate();
  }

  return (
    <main className="grid min-h-screen place-items-center bg-stone-950 p-4 text-white">
      <Card className="w-full max-w-md bg-white p-6 text-stone-950">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-stone-400">Первый вход</p>
        <h1 className="mt-2 text-3xl font-semibold">Смените пароль</h1>
        <p className="mt-2 text-sm leading-6 text-stone-500">После входа по одноразовой ссылке нужно обязательно установить новый пароль.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <Input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Новый пароль" required />
          <Input type="password" minLength={8} value={confirmation} onChange={(event) => setConfirmation(event.target.value)} placeholder="Повторите пароль" required />
          {(validationError || mutation.error) && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{validationError ?? mutation.error?.message}</p>}
          <Button className="w-full" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Сохраняем...' : 'Сохранить пароль'}</Button>
        </form>
      </Card>
    </main>
  );
}

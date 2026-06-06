import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { magicLogin } from '../shared/api/authV2';
import { Button } from '../shared/ui/Button';
import { Card } from '../shared/ui/Card';
import { Loader } from '../shared/ui/Loader';
import { useEffect, useRef } from 'react';

export function MagicLoginPage({ mode = 'login' }: { mode?: 'login' | 'activate' }) {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const token = params.get('token') ?? '';
  const hasSubmitted = useRef(false);
  const mutation = useMutation({
    mutationFn: () => magicLogin(token),
    onSuccess: async (response) => {
      await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      navigate(response.must_change_password ? '/auth/change-password' : '/tasks', { replace: true });
    },
  });

  useEffect(() => {
    if (token && !hasSubmitted.current) {
      hasSubmitted.current = true;
      mutation.mutate();
    }
  }, [token]);

  return (
    <main className="grid min-h-screen place-items-center bg-stone-950 p-4 text-white">
      <Card className="max-w-md bg-white p-6 text-stone-950">
        <h1 className="text-2xl font-semibold">{mode === 'activate' ? 'Активация аккаунта' : 'Вход по Telegram-ссылке'}</h1>
        {!token && <p className="mt-4 text-sm text-red-700">В ссылке отсутствует token.</p>}
        {mutation.isPending && <div className="mt-6"><Loader text="Авторизуем вас..." /></div>}
        {mutation.error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700">Ссылка недействительна, истекла или уже использована. Вернитесь в Telegram и выполните /login или запросите новую ссылку у менеджера.</p>}
        <Link className="mt-6 inline-block" to="/login"><Button variant="secondary">Обычный вход</Button></Link>
      </Card>
    </main>
  );
}

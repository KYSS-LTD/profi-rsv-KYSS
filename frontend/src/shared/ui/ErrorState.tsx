import { AlertTriangle } from 'lucide-react';
import { Card } from './Card';

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'Неизвестная ошибка';

  return (
    <Card className="border-red-200 bg-red-50 animate-fade-in">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-100 text-red-600">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <h3 className="font-semibold text-red-800">Не удалось загрузить данные</h3>
          <p className="mt-1 break-words text-sm leading-6 text-red-700">{message}</p>
          <p className="mt-2 text-xs text-red-600">Проверь адрес backend в .env или включи VITE_USE_MOCKS=true.</p>
        </div>
      </div>
    </Card>
  );
}

import { Card } from './Card';

export function ErrorState({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'Неизвестная ошибка';

  return (
    <Card className="border-red-200 bg-red-50">
      <h3 className="font-semibold text-red-800">Не удалось загрузить данные</h3>
      <p className="mt-2 text-sm leading-6 text-red-700">{message}</p>
      <p className="mt-2 text-xs text-red-600">Проверь, что backend запущен и VITE_API_BASE_URL указывает на API.</p>
    </Card>
  );
}

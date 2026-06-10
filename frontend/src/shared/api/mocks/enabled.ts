// ЕДИНЫЙ ВЫКЛЮЧАТЕЛЬ ДЕМО-МОКОВ.
//
// По умолчанию моки ВКЛЮЧЕНЫ — чтобы у всех, кто развернул сервис локально,
// сразу были демо-данные без бэкенда и без логина.
//
// Как отключить моки (любой способ):
//   1. Запустить с переменной окружения:  VITE_USE_MOCKS=false  (npm run dev / build)
//   2. Или поменять значение по умолчанию ниже на false.
//   3. Полностью убрать: удалить папку src/shared/api/mocks и снять перехват
//      в src/shared/api/client.ts и вызов bootstrapMocks() в src/main.tsx.

const raw = import.meta.env.VITE_USE_MOCKS as string | undefined;

export const MOCKS_ENABLED = raw === undefined ? true : raw !== 'false' && raw !== '0';

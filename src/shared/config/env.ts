export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
  useMocks: (import.meta.env.VITE_USE_MOCKS ?? 'true') === 'true',
  telegramAuthHeader: import.meta.env.VITE_TELEGRAM_AUTH_HEADER || 'X-Telegram-Init-Data',
  appName: import.meta.env.VITE_APP_NAME || 'Командус',
};

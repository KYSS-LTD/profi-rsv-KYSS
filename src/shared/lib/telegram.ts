export interface TelegramWebAppUser {
  id: number;
  is_bot?: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  is_premium?: boolean;
}

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
  header_bg_color?: string;
  accent_text_color?: string;
  section_bg_color?: string;
  section_header_text_color?: string;
  subtitle_text_color?: string;
  destructive_text_color?: string;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe?: {
    query_id?: string;
    user?: TelegramWebAppUser;
    auth_date?: number;
    hash?: string;
  };
  version: string;
  platform: string;
  colorScheme: 'light' | 'dark';
  themeParams: TelegramThemeParams;
  isExpanded: boolean;
  viewportHeight: number;
  viewportStableHeight: number;
  ready: () => void;
  expand: () => void;
  close: () => void;
  enableClosingConfirmation: () => void;
  disableClosingConfirmation: () => void;
  setHeaderColor: (color: string) => void;
  setBackgroundColor: (color: string) => void;
  HapticFeedback?: {
    impactOccurred: (style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft') => void;
    notificationOccurred: (type: 'error' | 'success' | 'warning') => void;
    selectionChanged: () => void;
  };
  MainButton?: {
    text: string;
    show: () => void;
    hide: () => void;
    setText: (text: string) => void;
    onClick: (callback: () => void) => void;
    offClick: (callback: () => void) => void;
  };
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

export const getTelegramWebApp = (): TelegramWebApp | undefined => window.Telegram?.WebApp;

export const isTelegramMiniApp = () => Boolean(getTelegramWebApp()?.initData);

export const getTelegramInitData = () => getTelegramWebApp()?.initData || '';

export const getTelegramUser = () => getTelegramWebApp()?.initDataUnsafe?.user;

export const applyTelegramTheme = () => {
  const webApp = getTelegramWebApp();
  const root = document.documentElement;

  if (!webApp) return;

  const params = webApp.themeParams || {};
  const vars: Record<string, string | undefined> = {
    '--tg-bg-color': params.bg_color,
    '--tg-text-color': params.text_color,
    '--tg-hint-color': params.hint_color,
    '--tg-link-color': params.link_color,
    '--tg-button-color': params.button_color,
    '--tg-button-text-color': params.button_text_color,
    '--tg-secondary-bg-color': params.secondary_bg_color,
  };

  Object.entries(vars).forEach(([key, value]) => {
    if (value) root.style.setProperty(key, value);
  });

  document.body.dataset.telegram = 'true';
  document.body.dataset.theme = webApp.colorScheme;
};

export const initTelegramShell = () => {
  const webApp = getTelegramWebApp();
  if (!webApp) return;

  applyTelegramTheme();
  webApp.ready();
  webApp.expand();
  webApp.enableClosingConfirmation?.();

  const header = webApp.themeParams.header_bg_color || webApp.themeParams.bg_color || '#101828';
  const background = webApp.themeParams.bg_color || '#f4f7fb';

  try {
    webApp.setHeaderColor(header);
    webApp.setBackgroundColor(background);
  } catch {
    // Older Telegram clients may reject custom colors. Safe to ignore.
  }
};

export const haptic = {
  success: () => getTelegramWebApp()?.HapticFeedback?.notificationOccurred('success'),
  warning: () => getTelegramWebApp()?.HapticFeedback?.notificationOccurred('warning'),
  error: () => getTelegramWebApp()?.HapticFeedback?.notificationOccurred('error'),
  tap: () => getTelegramWebApp()?.HapticFeedback?.impactOccurred('light'),
};

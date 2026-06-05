export const ACCESS_TOKEN_KEY = 'komandus_access_token';
export const AUTH_TOKEN_EVENT = 'komandus-auth-token-changed';

export function getAccessToken() {
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string) {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  window.dispatchEvent(new Event(AUTH_TOKEN_EVENT));
}

export function clearAccessToken() {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_TOKEN_EVENT));
}

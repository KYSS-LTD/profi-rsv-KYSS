import { CurrentUser } from '../../entities/saas/types';
import { clearAccessToken, setAccessToken } from '../auth/token';
import { apiClient } from './client';

type TokenResponse = { access_token: string; token_type: 'bearer' };

export type SetupStatusResponse = { initialized: boolean };

export type SetupRequest = {
  organization_name: string;
  full_name: string;
  email: string;
  password: string;
};

export async function login(email: string, password: string) {
  const response = await apiClient<TokenResponse>('/v2/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setAccessToken(response.access_token);
  return response;
}

export function getSetupStatus() {
  return apiClient<SetupStatusResponse>('/v2/setup/status');
}

export async function setupSystem(payload: SetupRequest) {
  const response = await apiClient<TokenResponse>('/v2/setup', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  setAccessToken(response.access_token);
  return response;
}

export async function refreshToken() {
  const response = await apiClient<TokenResponse>('/v2/auth/refresh', { method: 'POST' });
  setAccessToken(response.access_token);
  return response;
}

export async function logout() {
  try {
    await apiClient<{ status: string }>('/v2/auth/logout', { method: 'POST' });
  } finally {
    clearAccessToken();
  }
}

export function getMe() {
  return apiClient<CurrentUser>('/v2/auth/me');
}

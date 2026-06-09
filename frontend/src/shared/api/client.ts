import { env } from '../config/env';
import { getAccessToken } from '../auth/token';
import { resolveMock } from './mocks';
import { MOCKS_ENABLED } from './mocks/enabled';

type RequestOptions = RequestInit & {
  params?: Record<string, string | number | boolean | undefined | null>;
};

export type ApiListResponse<T> = T[] | { items: T[] };

export function unwrapItems<T>(response: ApiListResponse<T>): T[] {
  return Array.isArray(response) ? response : response.items;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function resolveApiUrl(path: string) {
  const baseUrl = env.apiBaseUrl.endsWith('/') ? env.apiBaseUrl : `${env.apiBaseUrl}/`;
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path;

  if (baseUrl.startsWith('http://') || baseUrl.startsWith('https://')) {
    return new URL(normalizedPath, baseUrl);
  }

  return new URL(`${baseUrl}${normalizedPath}`, window.location.origin);
}

export async function apiClient<T>(path: string, options: RequestOptions = {}): Promise<T> {
  // Перехват демо-мокoв (см. ./mocks/enabled.ts — как отключить).
  if (MOCKS_ENABLED) {
    const method = (options.method ?? 'GET').toUpperCase();
    const mocked = await resolveMock(method, path, options.body);
    if (mocked.matched) return mocked.data as T;
  }

  const url = resolveApiUrl(path);

  Object.entries(options.params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      url.searchParams.set(key, String(value));
    }
  });

  const isFormData = options.body instanceof FormData;
  const headers = new Headers(options.headers);

  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getAccessToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    credentials: 'include',
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;

    try {
      const data = await response.json();
      message = data.detail ?? data.message ?? message;
    } catch {
      // ignore non-json errors
    }

    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

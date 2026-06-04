import { Achievement, Note, Recommendation, UserDigest, UserProfile } from '../../entities/user/types';
import { apiClient, ApiListResponse, unwrapItems } from './client';

export async function getProfile() {
  return apiClient<UserProfile>('/profile/me');
}

export async function getUserDigest(userId: string) {
  return apiClient<UserDigest>(`/users/${userId}/digest`);
}

export async function getNotes() {
  const response = await apiClient<ApiListResponse<Note>>('/notes/my');
  return unwrapItems(response);
}

export async function createNote(payload: Pick<Note, 'title' | 'content' | 'source'>) {
  return apiClient<Note>('/notes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateNote(noteId: string, payload: Partial<Pick<Note, 'title' | 'content'>>) {
  return apiClient<Note>(`/notes/${noteId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteNote(noteId: string) {
  return apiClient<{ status: string; note_id?: string }>(`/notes/${noteId}`, {
    method: 'DELETE',
  });
}

export async function getAchievements(userId: string) {
  const response = await apiClient<ApiListResponse<Achievement>>(`/users/${userId}/achievements`);
  return unwrapItems(response);
}

export async function getRecommendations(userId: string) {
  const response = await apiClient<ApiListResponse<Recommendation>>(`/users/${userId}/recommendations`);
  return unwrapItems(response);
}

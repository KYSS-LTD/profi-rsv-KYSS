import { Achievement, Note, Recommendation, UserDigest, UserProfile } from '../../entities/user/types';
import { env } from '../config/env';
import { apiClient, ApiListResponse, unwrapItems } from './client';
import { mockAchievements, mockDigest, mockNotes, mockProfile, mockRecommendations } from './mock';

export async function getProfile() {
  if (env.useMocks) return mockProfile;

  return apiClient<UserProfile>('/profile/me');
}

export async function getUserDigest(userId: string) {
  if (env.useMocks) return mockDigest;

  return apiClient<UserDigest>(`/users/${userId}/digest`);
}

export async function getNotes() {
  if (env.useMocks) return mockNotes;

  const response = await apiClient<ApiListResponse<Note>>('/notes/my');
  return unwrapItems(response);
}

export async function createNote(payload: Pick<Note, 'title' | 'content' | 'source'>) {
  if (env.useMocks) return { ...payload, id: `note_${Date.now()}` } as Note;

  return apiClient<Note>('/notes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateNote(noteId: string, payload: Partial<Pick<Note, 'title' | 'content'>>) {
  if (env.useMocks) return { ...mockNotes[0], ...payload, id: noteId } as Note;

  return apiClient<Note>(`/notes/${noteId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteNote(noteId: string) {
  if (env.useMocks) return { status: 'deleted', note_id: noteId };

  return apiClient<{ status: string; note_id?: string }>(`/notes/${noteId}`, {
    method: 'DELETE',
  });
}

export async function getAchievements(userId: string) {
  if (env.useMocks) return mockAchievements;

  const response = await apiClient<ApiListResponse<Achievement>>(`/users/${userId}/achievements`);
  return unwrapItems(response);
}

export async function getRecommendations(userId: string) {
  if (env.useMocks) return mockRecommendations;

  const response = await apiClient<ApiListResponse<Recommendation>>(`/users/${userId}/recommendations`);
  return unwrapItems(response);
}

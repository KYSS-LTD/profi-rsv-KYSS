import { MeetingSummary, MeetingUploadResponse } from '../../entities/meeting/types';
import { env } from '../config/env';
import { apiClient } from './client';
import { mockMeeting } from './mock';

export async function getMeetingSummary(meetingId: string) {
  if (env.useMocks) return mockMeeting;

  return apiClient<MeetingSummary>(`/meetings/${meetingId}/summary`);
}

export async function uploadMeeting(file: File, teamId: string, title: string) {
  if (env.useMocks) return { meeting_id: 'meeting_1', status: 'transcribing' } as MeetingUploadResponse;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('team_id', teamId);
  formData.append('title', title);

  return apiClient<MeetingUploadResponse>('/meetings/upload', {
    method: 'POST',
    body: formData,
  });
}

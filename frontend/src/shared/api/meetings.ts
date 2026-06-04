import { MeetingSummary, MeetingUploadResponse } from '../../entities/meeting/types';
import { apiClient } from './client';

export async function getMeetingSummary(meetingId: string) {
  return apiClient<MeetingSummary>(`/meetings/${meetingId}/summary`);
}

export async function uploadMeeting(file: File, teamId: string, title: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('team_id', teamId);
  formData.append('title', title);

  return apiClient<MeetingUploadResponse>('/meetings/upload', {
    method: 'POST',
    body: formData,
  });
}

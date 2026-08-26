import { apiRequest, apiUpload } from "./client";
import type { SpeakingAttempt } from "./types";

export function generateSpeakingPrompt(): Promise<SpeakingAttempt> {
  return apiRequest<SpeakingAttempt>("/speaking/prompts", { method: "POST" });
}

export function startLessonSpeakingAttempt(lessonSlug: string): Promise<SpeakingAttempt> {
  return apiRequest<SpeakingAttempt>(`/speaking/lessons/${lessonSlug}/attempts`, {
    method: "POST",
  });
}

export function getSpeakingAttempt(id: string): Promise<SpeakingAttempt> {
  return apiRequest<SpeakingAttempt>(`/speaking/attempts/${id}`);
}

export function submitSpeakingAttempt(
  id: string,
  audio: Blob,
  filename: string,
): Promise<SpeakingAttempt> {
  const formData = new FormData();
  formData.append("audio", audio, filename);
  return apiUpload<SpeakingAttempt>(`/speaking/attempts/${id}/submit`, formData);
}

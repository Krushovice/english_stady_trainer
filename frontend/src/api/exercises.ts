import { apiRequest } from "./client";
import type { AttemptResult, Exercise, SubmittedAnswer } from "./types";

export function listLessonExercises(lessonSlug: string): Promise<Exercise[]> {
  return apiRequest<Exercise[]>(`/lessons/${lessonSlug}/exercises`);
}

export function submitAttempt(
  exerciseId: string,
  submittedAnswer: SubmittedAnswer,
): Promise<AttemptResult> {
  return apiRequest<AttemptResult>(`/exercises/${exerciseId}/attempts`, {
    method: "POST",
    body: { submitted_answer: submittedAnswer },
  });
}

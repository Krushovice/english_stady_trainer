import { apiRequest } from "./client";
import type { AttemptResult, Exercise, SkillProgress, SubmittedAnswer } from "./types";

export function listLessonExercises(lessonSlug: string): Promise<Exercise[]> {
  return apiRequest<Exercise[]>(`/lessons/${lessonSlug}/exercises`);
}

export function getDailyQuiz(): Promise<Exercise[]> {
  return apiRequest<Exercise[]>("/practice/daily-quiz");
}

export function getProgress(): Promise<SkillProgress[]> {
  return apiRequest<SkillProgress[]>("/progress");
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

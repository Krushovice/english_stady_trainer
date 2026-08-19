import { apiRequest } from "./client";
import type { CEFRLevel, ExamAttempt, ExamResult, ExamStatus, SubmittedAnswer } from "./types";

export function getExamStatus(level: CEFRLevel): Promise<ExamStatus> {
  return apiRequest<ExamStatus>(`/levels/${level}/exam/status`);
}

export function startExamAttempt(level: CEFRLevel): Promise<ExamAttempt> {
  return apiRequest<ExamAttempt>(`/levels/${level}/exam/attempts`, { method: "POST" });
}

export function submitExamAttempt(
  level: CEFRLevel,
  attemptId: string,
  answers: { exercise_id: string; submitted_answer: SubmittedAnswer }[],
): Promise<ExamResult> {
  return apiRequest<ExamResult>(`/levels/${level}/exam/attempts/${attemptId}/submit`, {
    method: "POST",
    body: { answers },
  });
}

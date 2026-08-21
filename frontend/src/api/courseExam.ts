import { apiRequest } from "./client";
import type { CourseExamStatus, ExamAttempt, ExamResult, SubmittedAnswer } from "./types";

export function getCourseExamStatus(): Promise<CourseExamStatus> {
  return apiRequest<CourseExamStatus>("/course-exam/status");
}

export function startCourseExamAttempt(): Promise<ExamAttempt> {
  return apiRequest<ExamAttempt>("/course-exam/attempts", { method: "POST" });
}

export function submitCourseExamAttempt(
  attemptId: string,
  answers: { exercise_id: string; submitted_answer: SubmittedAnswer }[],
): Promise<ExamResult> {
  return apiRequest<ExamResult>(`/course-exam/attempts/${attemptId}/submit`, {
    method: "POST",
    body: { answers },
  });
}

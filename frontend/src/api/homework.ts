import { apiRequest } from "./client";
import type { Homework, HomeworkAttempt } from "./types";

export function generateHomework(): Promise<Homework> {
  return apiRequest<Homework>("/homework/generate", { method: "POST" });
}

export function getHomework(id: string): Promise<Homework> {
  return apiRequest<Homework>(`/homework/${id}`);
}

export function submitHomeworkTask(
  homeworkId: string,
  taskId: string,
  text: string,
): Promise<HomeworkAttempt> {
  return apiRequest<HomeworkAttempt>(`/homework/${homeworkId}/tasks/${taskId}/submit`, {
    method: "POST",
    body: { text },
  });
}

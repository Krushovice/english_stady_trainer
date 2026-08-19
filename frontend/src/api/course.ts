import { apiRequest } from "./client";
import type { CEFRLevel, Level, LessonDetail, LessonSummary, Module } from "./types";

export function listLevels(): Promise<Level[]> {
  return apiRequest<Level[]>("/levels");
}

export function listModules(levelCode: CEFRLevel): Promise<Module[]> {
  return apiRequest<Module[]>(`/levels/${levelCode}/modules`);
}

export function listLessons(moduleSlug: string): Promise<LessonSummary[]> {
  return apiRequest<LessonSummary[]>(`/modules/${moduleSlug}/lessons`);
}

export function getLesson(lessonSlug: string): Promise<LessonDetail> {
  return apiRequest<LessonDetail>(`/lessons/${lessonSlug}`);
}

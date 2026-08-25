import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { LessonCompletion, LessonDetail, MiniTest } from "../api/types";
import { LessonPage } from "./LessonPage";

vi.mock("../api/course", () => ({ getLesson: vi.fn() }));
vi.mock("../api/exercises", () => ({
  getLessonCompletion: vi.fn(),
  getMiniTest: vi.fn(),
  listLessonExercises: vi.fn(),
  submitAttempt: vi.fn(),
}));

import { getLesson } from "../api/course";
import { getLessonCompletion, getMiniTest, listLessonExercises } from "../api/exercises";

const baseLesson: LessonDetail = {
  id: "l1",
  slug: "making-small-talk",
  title: "Making Small Talk",
  order_index: 1,
  blocks: [],
  vocabulary: [],
  grammar_topics: [],
  next_lesson_slug: null,
};

const noMiniTest: MiniTest = { previous_lesson_title: null, exercises: [] };

function completion(overrides: Partial<LessonCompletion> = {}): LessonCompletion {
  return {
    attempted: true,
    accuracy: 1,
    passed: true,
    wrong_exercise_ids: [],
    total: 0,
    correct: 0,
    ...overrides,
  };
}

function renderLesson(lesson: LessonDetail, lessonCompletion: LessonCompletion) {
  vi.mocked(getLesson).mockResolvedValue(lesson);
  vi.mocked(getLessonCompletion).mockResolvedValue(lessonCompletion);
  vi.mocked(getMiniTest).mockResolvedValue(noMiniTest);
  vi.mocked(listLessonExercises).mockResolvedValue([]);

  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[`/lessons/${lesson.slug}`]}>
        <Routes>
          <Route path="/lessons/:lessonSlug" element={<LessonPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(getLesson).mockReset();
  vi.mocked(getLessonCompletion).mockReset();
  vi.mocked(getMiniTest).mockReset();
  vi.mocked(listLessonExercises).mockReset();
});

describe("LessonPage — next lesson link", () => {
  it("links to the next lesson once this one is passed", async () => {
    renderLesson(
      { ...baseLesson, next_lesson_slug: "talking-about-experiences" },
      completion({ passed: true }),
    );
    const link = await screen.findByRole("link", { name: /Следующий урок/ });
    expect(link).toHaveAttribute("href", "/lessons/talking-about-experiences");
  });

  it("stays hidden while the lesson isn't passed yet", async () => {
    renderLesson(
      { ...baseLesson, next_lesson_slug: "talking-about-experiences" },
      completion({ passed: false, accuracy: 0.3 }),
    );
    await screen.findByText("Making Small Talk");
    expect(screen.queryByRole("link", { name: /Следующий урок/ })).not.toBeInTheDocument();
  });

  it("stays hidden for the last lesson in a level, even once passed", async () => {
    renderLesson({ ...baseLesson, next_lesson_slug: null }, completion({ passed: true }));
    await screen.findByText("Making Small Talk");
    expect(screen.queryByRole("link", { name: /Следующий урок/ })).not.toBeInTheDocument();
  });
});

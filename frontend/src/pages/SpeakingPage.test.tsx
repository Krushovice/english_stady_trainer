import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SpeakingAttempt } from "../api/types";
import { SpeakingPage } from "./SpeakingPage";

vi.mock("../api/speaking", () => ({
  generateSpeakingPrompt: vi.fn(),
  getSpeakingAttempt: vi.fn(),
  startLessonSpeakingAttempt: vi.fn(),
  submitSpeakingAttempt: vi.fn(),
}));

import {
  generateSpeakingPrompt,
  getSpeakingAttempt,
  startLessonSpeakingAttempt,
} from "../api/speaking";

const attempt: SpeakingAttempt = {
  id: "a1",
  lesson_title: "Making Small Talk",
  prompt: "Introduce yourself to a new colleague.",
  transcript: null,
  feedback: null,
  generated_at: new Date().toISOString(),
  submitted_at: null,
};

beforeEach(() => {
  localStorage.clear();
  vi.mocked(generateSpeakingPrompt).mockReset();
  vi.mocked(getSpeakingAttempt).mockReset();
  vi.mocked(startLessonSpeakingAttempt).mockReset();
});

describe("SpeakingPage — arriving from a lesson", () => {
  it("starts the lesson's own speaking task automatically, without a click", async () => {
    vi.mocked(startLessonSpeakingAttempt).mockResolvedValue(attempt);

    render(
      <MemoryRouter initialEntries={["/speaking?lessonSlug=making-small-talk"]}>
        <SpeakingPage />
      </MemoryRouter>,
    );

    await screen.findByText("Introduce yourself to a new colleague.");
    expect(startLessonSpeakingAttempt).toHaveBeenCalledWith("making-small-talk");
    expect(generateSpeakingPrompt).not.toHaveBeenCalled();
  });
});

describe("SpeakingPage — standalone", () => {
  it("generates a prompt from the last studied lesson on click", async () => {
    const user = userEvent.setup();
    vi.mocked(generateSpeakingPrompt).mockResolvedValue(attempt);

    render(
      <MemoryRouter initialEntries={["/speaking"]}>
        <SpeakingPage />
      </MemoryRouter>,
    );

    const button = await screen.findByRole("button", { name: "Получить задание для говорения" });
    await user.click(button);

    await screen.findByText("Introduce yourself to a new colleague.");
    expect(generateSpeakingPrompt).toHaveBeenCalled();
    expect(startLessonSpeakingAttempt).not.toHaveBeenCalled();
  });
});

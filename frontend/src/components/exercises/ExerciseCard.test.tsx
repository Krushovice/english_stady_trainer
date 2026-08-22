import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AttemptResult, Exercise } from "../../api/types";
import { ExerciseCard } from "./ExerciseCard";

vi.mock("../../api/exercises", () => ({
  submitAttempt: vi.fn(),
}));

import { submitAttempt } from "../../api/exercises";

const exercise: Exercise = {
  id: "ex-1",
  slug: "ex-1",
  skill: "grammar",
  difficulty: "A1",
  exercise_type: "multiple_choice",
  prompt: {
    question: "This is ___ sister.",
    options: [
      { id: "a", text: "my" },
      { id: "b", text: "me" },
    ],
  },
};

function renderWithClient(ui: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

const correctResult: AttemptResult = {
  id: "attempt-1",
  is_correct: true,
  score: 1,
  explanation: "«my» is the possessive form used before a noun.",
  answer_key: {},
  attempted_at: "2026-08-22T00:00:00Z",
};

beforeEach(() => {
  vi.mocked(submitAttempt).mockReset();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("ExerciseCard", () => {
  it("disables submission until an answer is chosen", () => {
    renderWithClient(<ExerciseCard exercise={exercise} />);
    expect(screen.getByRole("button", { name: "Проверить" })).toBeDisabled();
  });

  it("submits the chosen option and shows a correct verdict with the explanation", async () => {
    const user = userEvent.setup();
    vi.mocked(submitAttempt).mockResolvedValue(correctResult);
    renderWithClient(<ExerciseCard exercise={exercise} />);

    await user.click(screen.getByLabelText("my"));
    await user.click(screen.getByRole("button", { name: "Проверить" }));

    expect(submitAttempt).toHaveBeenCalledWith("ex-1", { option_id: "a" });
    expect(await screen.findByText("Верно!")).toBeInTheDocument();
    expect(screen.getByText(correctResult.explanation)).toBeInTheDocument();
  });

  it("shows an incorrect verdict and lets the learner retry with a clean slate", async () => {
    const user = userEvent.setup();
    vi.mocked(submitAttempt).mockResolvedValue({
      ...correctResult,
      is_correct: false,
      explanation: "Not quite — «me» is an object pronoun, not a possessive.",
    });
    renderWithClient(<ExerciseCard exercise={exercise} />);

    await user.click(screen.getByLabelText("me"));
    await user.click(screen.getByRole("button", { name: "Проверить" }));
    expect(await screen.findByText("Не совсем.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Попробовать снова" }));

    expect(screen.queryByText("Не совсем.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Проверить" })).toBeDisabled();
  });

  it("shows a retry-friendly error and keeps the answer instead of crashing when the API call fails", async () => {
    const user = userEvent.setup();
    vi.mocked(submitAttempt).mockRejectedValue(new Error("network down"));
    renderWithClient(<ExerciseCard exercise={exercise} />);

    await user.click(screen.getByLabelText("my"));
    await user.click(screen.getByRole("button", { name: "Проверить" }));

    expect(
      await screen.findByText("Не удалось отправить ответ. Попробуйте ещё раз."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Проверить" })).toBeEnabled();
  });
});

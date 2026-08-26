import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AttemptResult, Exercise } from "../api/types";
import { DailyQuizPage } from "./DailyQuizPage";

vi.mock("../api/exercises", () => ({
  getDailyQuiz: vi.fn(),
  submitAttempt: vi.fn(),
}));

import { getDailyQuiz, submitAttempt } from "../api/exercises";

const exercises: Exercise[] = [
  {
    id: "e1",
    slug: "e1",
    skill: "grammar",
    difficulty: "A1",
    exercise_type: "multiple_choice",
    prompt: { question: "She ___ to work every day.", options: [{ id: "a", text: "go" }, { id: "b", text: "goes" }] },
  },
  {
    id: "e2",
    slug: "e2",
    skill: "vocabulary",
    difficulty: "A1",
    exercise_type: "multiple_choice",
    prompt: { question: "Choose the odd one out.", options: [{ id: "a", text: "apple" }, { id: "b", text: "car" }] },
  },
];

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DailyQuizPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(getDailyQuiz).mockReset();
  vi.mocked(submitAttempt).mockReset();
});

describe("DailyQuizPage", () => {
  it("shows an empty-state message when there's nothing to test", async () => {
    vi.mocked(getDailyQuiz).mockResolvedValue([]);
    renderPage();
    await screen.findByText(/Пока нечего тестировать/);
  });

  it("keeps the single check button disabled until every exercise is answered", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyQuiz).mockResolvedValue(exercises);
    renderPage();

    const button = await screen.findByRole("button", { name: "Проверить" });
    expect(button).toBeDisabled();

    const cards = screen.getAllByRole("group");
    await user.click(within(cards[0]).getByLabelText("goes"));
    expect(button).toBeDisabled();

    await user.click(within(cards[1]).getByLabelText("car"));
    expect(button).toBeEnabled();
  });

  it("submits every answer once and shows an aggregate result", async () => {
    const user = userEvent.setup();
    vi.mocked(getDailyQuiz).mockResolvedValue(exercises);
    vi.mocked(submitAttempt).mockImplementation(async (exerciseId): Promise<AttemptResult> => ({
      id: `attempt-${exerciseId}`,
      is_correct: exerciseId === "e1",
      score: exerciseId === "e1" ? 1 : 0,
      explanation: exerciseId === "e1" ? "Correct: goes." : "Not quite: car is the vehicle.",
      answer_key: {},
      attempted_at: new Date().toISOString(),
    }));
    renderPage();

    const cards = await screen.findAllByRole("group");
    await user.click(within(cards[0]).getByLabelText("goes"));
    await user.click(within(cards[1]).getByLabelText("car"));
    await user.click(screen.getByRole("button", { name: "Проверить" }));

    await waitFor(() => expect(submitAttempt).toHaveBeenCalledTimes(2));
    expect(submitAttempt).toHaveBeenCalledWith("e1", { option_id: "b" });
    expect(submitAttempt).toHaveBeenCalledWith("e2", { option_id: "b" });

    await screen.findByText("Верно: 1/2");
    expect(screen.queryByRole("button", { name: "Проверить" })).not.toBeInTheDocument();
  });
});

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ReviewItem } from "../api/types";
import { ReviewFlashcard } from "./ReviewFlashcard";

vi.mock("../api/review", () => ({ completeReview: vi.fn() }));
import { completeReview } from "../api/review";

const vocabItem: ReviewItem = {
  id: "r1",
  item_type: "vocabulary",
  due_at: new Date().toISOString(),
  interval_days: 1,
  review_count: 0,
  vocabulary: {
    id: "v1",
    headword: "inevitably",
    translation: "неизбежно, обязательно (произойдёт)",
    example_sentence: "It was inevitably going to rain.",
    audio_url: null,
  },
  grammar_topic: null,
  exercise: null,
};

const grammarItem: ReviewItem = {
  id: "r2",
  item_type: "grammar_topic",
  due_at: new Date().toISOString(),
  interval_days: 1,
  review_count: 0,
  vocabulary: null,
  grammar_topic: { id: "g1", slug: "present-simple", title: "Present Simple", description: "..." },
  exercise: null,
};

function renderCard(item: ReviewItem) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ReviewFlashcard item={item} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(completeReview).mockReset();
  vi.mocked(completeReview).mockResolvedValue(vocabItem);
});

describe("ReviewFlashcard — vocabulary translation check", () => {
  it("accepts a synonym even with different case/whitespace and marks it correct", async () => {
    const user = userEvent.setup();
    renderCard(vocabItem);

    await user.type(screen.getByLabelText("Перевод на русский"), "  Обязательно  ");
    await user.click(screen.getByRole("button", { name: "Проверить" }));

    await screen.findByText("Верно");
    expect(completeReview).toHaveBeenCalledWith("r1", true);
  });

  it("rejects a wrong translation and reveals the correct one", async () => {
    const user = userEvent.setup();
    renderCard(vocabItem);

    await user.type(screen.getByLabelText("Перевод на русский"), "может быть");
    await user.click(screen.getByRole("button", { name: "Проверить" }));

    await screen.findByText("Не совсем.");
    screen.getByText("неизбежно, обязательно (произойдёт)");
    expect(completeReview).toHaveBeenCalledWith("r1", false);
  });
});

describe("ReviewFlashcard — grammar topic self-report", () => {
  it("keeps the reveal + Забыл/Помню flow for grammar items", async () => {
    const user = userEvent.setup();
    renderCard(grammarItem);

    expect(screen.queryByLabelText("Перевод на русский")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Показать ответ" }));
    await user.click(screen.getByRole("button", { name: "Помню" }));

    expect(completeReview).toHaveBeenCalledWith("r2", true);
  });
});

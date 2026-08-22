import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { SentenceOrderingPrompt } from "../../api/types";
import { SentenceOrderingExercise } from "./SentenceOrderingExercise";

const prompt: SentenceOrderingPrompt = { words: ["I", "like", "coffee"] };

describe("SentenceOrderingExercise", () => {
  it("starts with every word in the bank and none chosen", () => {
    render(<SentenceOrderingExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);
    for (const word of prompt.words) {
      expect(screen.getByText(word)).toBeInTheDocument();
    }
    expect(screen.getByText("Нажимайте на слова ниже по порядку")).toBeInTheDocument();
  });

  it("moves a word from the bank to the chosen row in click order and reports that order", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SentenceOrderingExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.click(screen.getByText("coffee"));
    await user.click(screen.getByText("I"));

    expect(onChange).toHaveBeenLastCalledWith(["coffee", "I"]);
  });

  it("moves a word back to the bank when its chosen chip is clicked again", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SentenceOrderingExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.click(screen.getByText("like"));
    await user.click(screen.getByText("like"));

    expect(onChange).toHaveBeenLastCalledWith([]);
    expect(screen.getByText("Нажимайте на слова ниже по порядку")).toBeInTheDocument();
  });

  it("disables every word chip once the exercise is locked", () => {
    render(<SentenceOrderingExercise prompt={prompt} disabled onChange={vi.fn()} />);
    for (const word of prompt.words) {
      expect(screen.getByText(word)).toBeDisabled();
    }
  });
});

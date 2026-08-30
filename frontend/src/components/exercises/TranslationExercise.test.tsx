import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { TranslationPrompt } from "../../api/types";
import { TranslationExercise } from "./TranslationExercise";

describe("TranslationExercise", () => {
  it("shows the phrase to translate", () => {
    const prompt: TranslationPrompt = { text: "Сколько это стоит?" };
    render(<TranslationExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);
    screen.getByText("Сколько это стоит?");
  });

  it("reports the typed translation as the learner types", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const prompt: TranslationPrompt = { text: "Сколько это стоит?" };
    render(<TranslationExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.type(screen.getByRole("textbox"), "How much is it?");

    expect(onChange).toHaveBeenLastCalledWith("How much is it?");
  });

  it("disables the input once the exercise is locked", () => {
    const prompt: TranslationPrompt = { text: "Сколько это стоит?" };
    render(<TranslationExercise prompt={prompt} disabled onChange={vi.fn()} />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});

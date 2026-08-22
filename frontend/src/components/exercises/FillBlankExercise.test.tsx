import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { FillBlankPrompt } from "../../api/types";
import { FillBlankExercise } from "./FillBlankExercise";

describe("FillBlankExercise", () => {
  it("renders one input per blank", () => {
    const prompt: FillBlankPrompt = { text: "My mother's brother is my ___." };
    render(<FillBlankExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);
    expect(screen.getAllByRole("textbox")).toHaveLength(1);
  });

  it("renders one input per blank when the sentence has several", () => {
    const prompt: FillBlankPrompt = { text: "I ___ to the shop and ___ some milk." };
    render(<FillBlankExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);
    expect(screen.getAllByRole("textbox")).toHaveLength(2);
  });

  it("reports every blank's current text, positionally, as the learner types", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const prompt: FillBlankPrompt = { text: "I ___ to the shop and ___ some milk." };
    render(<FillBlankExercise prompt={prompt} disabled={false} onChange={onChange} />);

    const [first, second] = screen.getAllByRole("textbox");
    await user.type(first, "went");
    await user.type(second, "bought");

    expect(onChange).toHaveBeenLastCalledWith(["went", "bought"]);
  });

  it("disables every blank once the exercise is locked", () => {
    const prompt: FillBlankPrompt = { text: "I ___ to the shop." };
    render(<FillBlankExercise prompt={prompt} disabled onChange={vi.fn()} />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});

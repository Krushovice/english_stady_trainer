import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { MultipleChoicePrompt } from "../../api/types";
import { MultipleChoiceExercise } from "./MultipleChoiceExercise";

const prompt: MultipleChoicePrompt = {
  question: "This is ___ sister.",
  options: [
    { id: "a", text: "my" },
    { id: "b", text: "me" },
    { id: "c", text: "I" },
  ],
};

describe("MultipleChoiceExercise", () => {
  it("renders the question and every option", () => {
    render(<MultipleChoiceExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);
    expect(screen.getByText(prompt.question)).toBeInTheDocument();
    for (const option of prompt.options) {
      expect(screen.getByLabelText(option.text)).toBeInTheDocument();
    }
  });

  it("reports the chosen option's id, not its label", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<MultipleChoiceExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.click(screen.getByLabelText("my"));

    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("a");
  });

  it("only reports the most recently picked option when the learner changes their mind", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<MultipleChoiceExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.click(screen.getByLabelText("my"));
    await user.click(screen.getByLabelText("me"));

    expect(onChange).toHaveBeenLastCalledWith("b");
  });

  it("disables every option once the exercise is locked", () => {
    render(<MultipleChoiceExercise prompt={prompt} disabled onChange={vi.fn()} />);
    for (const option of prompt.options) {
      expect(screen.getByLabelText(option.text)).toBeDisabled();
    }
  });
});

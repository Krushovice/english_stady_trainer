import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ListeningComprehensionPrompt } from "../../api/types";
import { ListeningComprehensionExercise } from "./ListeningComprehensionExercise";

const prompt: ListeningComprehensionPrompt = {
  audio_url: "/audio/introducing-yourself.mp3",
  transcript: "A: Hi! What's your name? B: I'm Marco.",
  questions: [
    {
      id: "q1",
      text: "What is the man's name?",
      options: [
        { id: "a", text: "Marco" },
        { id: "b", text: "Mark" },
      ],
    },
  ],
};

describe("ListeningComprehensionExercise", () => {
  it("renders the audio player and questions, with the transcript collapsed by default", () => {
    render(<ListeningComprehensionExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);

    expect(document.querySelector("audio")).toHaveAttribute(
      "src",
      expect.stringContaining("/audio/introducing-yourself.mp3"),
    );
    expect(screen.getByText("What is the man's name?")).toBeInTheDocument();
    expect(document.querySelector("details")).not.toHaveAttribute("open");
  });

  it("reveals the transcript once the spoiler is opened", async () => {
    const user = userEvent.setup();
    render(<ListeningComprehensionExercise prompt={prompt} disabled={false} onChange={vi.fn()} />);

    await user.click(screen.getByText("Показать текст"));

    expect(screen.getByText(prompt.transcript)).toBeInTheDocument();
  });

  it("reports the chosen option for a question", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<ListeningComprehensionExercise prompt={prompt} disabled={false} onChange={onChange} />);

    await user.click(screen.getByLabelText("Marco"));

    expect(onChange).toHaveBeenLastCalledWith({ q1: "a" });
  });

  it("disables every answer input when disabled", () => {
    render(<ListeningComprehensionExercise prompt={prompt} disabled={true} onChange={vi.fn()} />);

    expect(screen.getByLabelText("Marco")).toBeDisabled();
    expect(screen.getByLabelText("Mark")).toBeDisabled();
  });
});

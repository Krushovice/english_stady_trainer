import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import type { LessonBlock } from "../api/types";
import { LessonBlockView } from "./LessonBlockView";

function renderBlock(block: LessonBlock) {
  return render(
    <MemoryRouter>
      <LessonBlockView block={block} lessonSlug="making-small-talk" />
    </MemoryRouter>,
  );
}

describe("LessonBlockView — speaking block", () => {
  it("shows the prompt and a start link into the Speaking flow for this lesson", () => {
    renderBlock({
      id: "b1",
      block_type: "speaking",
      order_index: 9,
      content: { prompt: "Introduce yourself to a new colleague." },
    });

    screen.getByText("Introduce yourself to a new colleague.");
    const link = screen.getByRole("link", { name: "Начать" });
    expect(link).toHaveAttribute("href", "/speaking?lessonSlug=making-small-talk");
  });
});

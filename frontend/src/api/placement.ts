import { apiRequest } from "./client";
import type { Exercise, PlacementResult, SubmittedAnswer } from "./types";

export function getPlacementItems(): Promise<Exercise[]> {
  return apiRequest<Exercise[]>("/placement-test/items");
}

export function submitPlacementTest(
  answers: { exercise_id: string; submitted_answer: SubmittedAnswer }[],
): Promise<PlacementResult> {
  return apiRequest<PlacementResult>("/placement-test/submit", {
    method: "POST",
    body: { answers },
  });
}

export function getPlacementResult(): Promise<PlacementResult> {
  return apiRequest<PlacementResult>("/placement-test/result");
}

export function chooseStartingPoint(choice: "review" | "assessed"): Promise<void> {
  return apiRequest<void>("/placement-test/choose-starting-point", {
    method: "POST",
    body: { choice },
  });
}

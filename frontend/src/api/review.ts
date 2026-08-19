import { apiRequest } from "./client";
import type { ReviewItem } from "./types";

export function listDueReviews(): Promise<ReviewItem[]> {
  return apiRequest<ReviewItem[]>("/review/due");
}

export function completeReview(reviewItemId: string, isCorrect: boolean): Promise<ReviewItem> {
  return apiRequest<ReviewItem>(`/review/${reviewItemId}/complete`, {
    method: "POST",
    body: { is_correct: isCorrect },
  });
}

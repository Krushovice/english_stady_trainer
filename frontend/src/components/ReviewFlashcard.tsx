import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { completeReview } from "../api/review";
import type { ReviewItem } from "../api/types";

export function ReviewFlashcard({ item }: { item: ReviewItem }) {
  const queryClient = useQueryClient();
  const [revealed, setRevealed] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const front = item.vocabulary ? item.vocabulary.headword : item.grammar_topic!.title;
  const back = item.vocabulary
    ? item.vocabulary.translation
    : item.grammar_topic!.description;
  const label = item.vocabulary ? "Vocabulary" : "Grammar";

  async function rate(isCorrect: boolean) {
    setSubmitting(true);
    try {
      await completeReview(item.id, isCorrect);
      queryClient.invalidateQueries({ queryKey: ["review-due"] });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="exercise-card">
      <div className="exercise-meta">
        <span className="badge">{label}</span>
      </div>
      <p className="flashcard-front">{front}</p>
      {revealed ? (
        <>
          <p className="flashcard-back">{back}</p>
          <div className="flashcard-actions">
            <button type="button" onClick={() => rate(false)} disabled={submitting}>
              Forgot
            </button>
            <button type="button" onClick={() => rate(true)} disabled={submitting}>
              Remembered
            </button>
          </div>
        </>
      ) : (
        <button type="button" onClick={() => setRevealed(true)}>
          Show answer
        </button>
      )}
    </div>
  );
}

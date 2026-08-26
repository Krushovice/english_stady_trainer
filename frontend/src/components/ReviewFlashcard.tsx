import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { completeReview } from "../api/review";
import type { ReviewItem } from "../api/types";

// Vocabulary translations are authored as free Russian text, sometimes with
// several synonyms ("справляться с, разбираться с") or a parenthetical
// clarification ("неизбежно, обязательно (произойдёт)") — split on commas/
// semicolons and drop parentheticals so a learner typing any one accepted
// synonym still matches, per CLAUDE.md's "known translation -> deterministic,
// normalised matching" rule.
function normalizeTranslation(text: string): string {
  return text
    .toLowerCase()
    .replace(/\([^)]*\)/g, "")
    .replace(/[.!?]+$/g, "")
    .trim()
    .replace(/\s+/g, " ");
}

function acceptableTranslations(translation: string): string[] {
  return translation
    .split(/[,;]/)
    .map(normalizeTranslation)
    .filter(Boolean);
}

export function ReviewFlashcard({ item }: { item: ReviewItem }) {
  const queryClient = useQueryClient();
  const [revealed, setRevealed] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [checked, setChecked] = useState<boolean | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const front = item.vocabulary ? item.vocabulary.headword : item.grammar_topic!.title;
  const back = item.vocabulary
    ? item.vocabulary.translation
    : item.grammar_topic!.description;
  const label = item.vocabulary ? "Лексика" : "Грамматика";

  async function rate(isCorrect: boolean) {
    setSubmitting(true);
    try {
      await completeReview(item.id, isCorrect);
      queryClient.invalidateQueries({ queryKey: ["review-due"] });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCheckTranslation() {
    const isCorrect = acceptableTranslations(item.vocabulary!.translation).includes(
      normalizeTranslation(inputValue),
    );
    setChecked(isCorrect);
    await rate(isCorrect);
  }

  return (
    <div className="exercise-card">
      <div className="exercise-meta">
        <span className="badge">{label}</span>
      </div>
      <p className="flashcard-front">{front}</p>

      {item.vocabulary ? (
        checked === null ? (
          <form
            className="flashcard-translate"
            onSubmit={(e) => {
              e.preventDefault();
              if (inputValue.trim()) handleCheckTranslation();
            }}
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Перевод на русский"
              disabled={submitting}
              aria-label="Перевод на русский"
            />
            <button type="submit" disabled={submitting || !inputValue.trim()}>
              Проверить
            </button>
          </form>
        ) : (
          <div className="exercise-result">
            <p className="result-verdict">{checked ? "Верно" : "Не совсем."}</p>
            <p className="flashcard-back">{back}</p>
          </div>
        )
      ) : revealed ? (
        <>
          <p className="flashcard-back">{back}</p>
          <div className="flashcard-actions">
            <button type="button" onClick={() => rate(false)} disabled={submitting}>
              Забыл(а)
            </button>
            <button type="button" onClick={() => rate(true)} disabled={submitting}>
              Помню
            </button>
          </div>
        </>
      ) : (
        <button type="button" onClick={() => setRevealed(true)}>
          Показать ответ
        </button>
      )}
    </div>
  );
}

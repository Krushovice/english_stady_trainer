import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { submitAttempt } from "../../api/exercises";
import type { AttemptResult, Exercise, SubmittedAnswer } from "../../api/types";
import { FillBlankExercise } from "./FillBlankExercise";
import { MultipleChoiceExercise } from "./MultipleChoiceExercise";
import { ReadingComprehensionExercise } from "./ReadingComprehensionExercise";
import { SentenceOrderingExercise } from "./SentenceOrderingExercise";

const SKILL_LABELS: Record<string, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

export function ExerciseCard({ exercise }: { exercise: Exercise }) {
  const queryClient = useQueryClient();
  const [answer, setAnswer] = useState<SubmittedAnswer | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Bumped on retry to force the per-type input component to remount —
  // it holds its own uncontrolled-ish local state (selected option, chosen
  // words, blank text) that a plain result/answer reset wouldn't clear.
  const [attemptKey, setAttemptKey] = useState(0);

  async function handleSubmit() {
    if (!answer) return;
    setSubmitting(true);
    setError(null);
    try {
      setResult(await submitAttempt(exercise.id, answer));
      // An attempt changes the per-skill breakdown, the pool the daily quiz
      // draws from, and (for an exercise-type review item) reschedules it
      // out of the due queue — without this, those pages/lists would keep
      // showing pre-attempt data for the rest of `staleTime`.
      queryClient.invalidateQueries({ queryKey: ["progress"] });
      queryClient.invalidateQueries({ queryKey: ["daily-quiz"] });
      queryClient.invalidateQueries({ queryKey: ["review-due"] });
    } catch {
      setError("Couldn't submit your answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  function handleRetry() {
    setResult(null);
    setAnswer(null);
    setError(null);
    setAttemptKey((k) => k + 1);
  }

  return (
    <div
      className={
        "exercise-card" + (result ? (result.is_correct ? " correct" : " incorrect") : "")
      }
    >
      <div className="exercise-meta">
        <span className="badge">{SKILL_LABELS[exercise.skill] ?? exercise.skill}</span>
        <span className="badge badge-muted">{exercise.difficulty}</span>
      </div>

      {exercise.exercise_type === "multiple_choice" && (
        <MultipleChoiceExercise
          key={attemptKey}
          prompt={exercise.prompt}
          disabled={!!result}
          onChange={(optionId) => setAnswer({ option_id: optionId })}
        />
      )}
      {exercise.exercise_type === "fill_blank" && (
        <FillBlankExercise
          key={attemptKey}
          prompt={exercise.prompt}
          disabled={!!result}
          onChange={(blanks) => setAnswer({ blanks })}
        />
      )}
      {exercise.exercise_type === "sentence_ordering" && (
        <SentenceOrderingExercise
          key={attemptKey}
          prompt={exercise.prompt}
          disabled={!!result}
          onChange={(order) => setAnswer({ order })}
        />
      )}
      {exercise.exercise_type === "reading_comprehension" && (
        <ReadingComprehensionExercise
          key={attemptKey}
          prompt={exercise.prompt}
          disabled={!!result}
          onChange={(answers) => setAnswer({ answers })}
        />
      )}

      {error && <p className="form-error">{error}</p>}

      {!result ? (
        <button type="button" onClick={handleSubmit} disabled={!answer || submitting}>
          {submitting ? "Checking..." : "Check"}
        </button>
      ) : (
        <div className="exercise-result">
          <p className="result-verdict">{result.is_correct ? "Correct!" : "Not quite."}</p>
          <p className="result-explanation">{result.explanation}</p>
          <button type="button" className="link-button" onClick={handleRetry}>
            Try again
          </button>
        </div>
      )}
    </div>
  );
}

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getExamStatus, startExamAttempt, submitExamAttempt } from "../api/levelExam";
import type { CEFRLevel, Exercise, ExamResult, Skill, SubmittedAnswer } from "../api/types";
import { FillBlankExercise } from "../components/exercises/FillBlankExercise";
import { MultipleChoiceExercise } from "../components/exercises/MultipleChoiceExercise";
import { ReadingComprehensionExercise } from "../components/exercises/ReadingComprehensionExercise";
import { SentenceOrderingExercise } from "../components/exercises/SentenceOrderingExercise";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

function ExamItem({
  exercise,
  onAnswer,
}: {
  exercise: Exercise;
  onAnswer: (answer: SubmittedAnswer) => void;
}) {
  switch (exercise.exercise_type) {
    case "multiple_choice":
      return (
        <MultipleChoiceExercise
          prompt={exercise.prompt}
          disabled={false}
          onChange={(optionId) => onAnswer({ option_id: optionId })}
        />
      );
    case "fill_blank":
      return (
        <FillBlankExercise
          prompt={exercise.prompt}
          disabled={false}
          onChange={(blanks) => onAnswer({ blanks })}
        />
      );
    case "sentence_ordering":
      return (
        <SentenceOrderingExercise
          prompt={exercise.prompt}
          disabled={false}
          onChange={(order) => onAnswer({ order })}
        />
      );
    case "reading_comprehension":
      return (
        <ReadingComprehensionExercise
          prompt={exercise.prompt}
          disabled={false}
          onChange={(answers) => onAnswer({ answers })}
        />
      );
  }
}

function formatClock(seconds: number): string {
  const clamped = Math.max(0, seconds);
  const m = Math.floor(clamped / 60);
  const s = clamped % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString();
}

function ResultView({ level, result }: { level: CEFRLevel; result: ExamResult }) {
  return (
    <div className="exam-result">
      <p className="exam-result-verdict">
        {result.passed ? "✅ Passed!" : "❌ Not this time."}
      </p>
      <p className="exam-result-score">
        {result.correct_count}/{result.total_count} correct ({Math.round(result.score * 100)}%)
      </p>
      {result.passed ? (
        <p>The next level after {level} is now unlocked.</p>
      ) : (
        <p>70% is needed to pass. Review the lessons and try again.</p>
      )}
      <Link to="/levels" className="btn-primary">
        Back to levels
      </Link>
    </div>
  );
}

export function ExamPage() {
  const { levelCode } = useParams<{ levelCode: string }>();
  const level = levelCode as CEFRLevel;
  const queryClient = useQueryClient();

  const [items, setItems] = useState<Exercise[] | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, SubmittedAnswer>>({});
  const [result, setResult] = useState<ExamResult | null>(null);
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submittedRef = useRef(false);

  const status = useQuery({
    queryKey: ["exam-status", level],
    queryFn: () => getExamStatus(level),
    enabled: !!level && !result,
  });

  async function handleSubmit(currentAnswers: Record<string, SubmittedAnswer>) {
    if (!attemptId || submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await submitExamAttempt(
        level,
        attemptId,
        Object.entries(currentAnswers).map(([exercise_id, submitted_answer]) => ({
          exercise_id,
          submitted_answer,
        })),
      );
      setResult(submitted);
      queryClient.invalidateQueries({ queryKey: ["levels"] });
    } catch (err) {
      submittedRef.current = false;
      setError(err instanceof ApiError ? err.message : "Couldn't submit the exam.");
    } finally {
      setSubmitting(false);
    }
  }

  // Countdown tick, and auto-submit once the timer reaches zero.
  useEffect(() => {
    if (!expiresAt || result) return;
    const tick = () => {
      const secondsLeft = Math.round((new Date(expiresAt).getTime() - Date.now()) / 1000);
      setRemainingSeconds(secondsLeft);
      if (secondsLeft <= 0) {
        handleSubmit(answers);
      }
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expiresAt, result]);

  async function handleStart() {
    setError(null);
    setStarting(true);
    try {
      const attempt = await startExamAttempt(level);
      setItems(attempt.exercises);
      setAttemptId(attempt.attempt_id);
      setExpiresAt(attempt.expires_at);
      submittedRef.current = false;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't start the exam.");
    } finally {
      setStarting(false);
    }
  }

  // A refreshed page with an unsubmitted attempt still running resumes it
  // automatically instead of making the learner click "Start" again —
  // startExamAttempt() is idempotent and returns the same attempt.
  useEffect(() => {
    if (status.data?.in_progress_attempt_id && !items && !starting) {
      handleStart();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status.data?.in_progress_attempt_id]);

  if (result) {
    return (
      <div className="page">
        <h1>{level} exit exam</h1>
        <ResultView level={level} result={result} />
      </div>
    );
  }

  if (items && attemptId) {
    return (
      <div className="page">
        <h1>{level} exit exam</h1>
        <p className="exam-timer">
          Time left: <strong>{formatClock(remainingSeconds ?? 0)}</strong>
        </p>
        <p className="status">
          {Object.keys(answers).length}/{items.length} answered
        </p>
        {items.map((exercise, i) => (
          <div key={exercise.id} className="exercise-card">
            <div className="exercise-meta">
              <span className="badge">{i + 1}</span>
              <span className="badge badge-muted">{SKILL_LABELS[exercise.skill]}</span>
            </div>
            <ExamItem
              exercise={exercise}
              onAnswer={(answer) => setAnswers((prev) => ({ ...prev, [exercise.id]: answer }))}
            />
          </div>
        ))}
        {error && <p className="form-error">{error}</p>}
        <button
          type="button"
          className="btn-primary"
          onClick={() => handleSubmit(answers)}
          disabled={submitting}
        >
          {submitting ? "Submitting..." : "Submit exam"}
        </button>
      </div>
    );
  }

  if (status.isLoading) return <p className="status">Loading...</p>;
  if (status.error) return <p className="status status-error">Couldn't load exam status.</p>;
  const data = status.data!;

  if (!data.exam_available) {
    return (
      <div className="page">
        <h1>{level} exit exam</h1>
        <p className="status">
          There's no lesson content for {level} yet, so there's nothing to test.
        </p>
        <Link to="/levels" className="back-link">
          &larr; Levels
        </Link>
      </div>
    );
  }

  if (data.passed) {
    return (
      <div className="page">
        <h1>{level} exit exam</h1>
        <p className="status">You've already passed this exam. The next level is unlocked.</p>
        <Link to="/levels" className="btn-primary">
          Back to levels
        </Link>
      </div>
    );
  }

  if (data.cooldown_until) {
    return (
      <div className="page">
        <h1>{level} exit exam</h1>
        <p className="status status-error">
          {data.attempts_used_in_window} failed attempts in a row. Next attempt available at{" "}
          {formatWhen(data.cooldown_until)}.
        </p>
        <Link to="/levels" className="back-link">
          &larr; Levels
        </Link>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>{level} exit exam</h1>
      <p>
        20 questions covering everything in {level}, 70% to pass, {15} minutes on the clock. Up
        to {data.attempts_per_window} attempts before a 24-hour cooldown.
      </p>
      <p className="status">
        Attempts used: {data.attempts_used_in_window}/{data.attempts_per_window}
      </p>
      {error && <p className="form-error">{error}</p>}
      <div className="placement-actions">
        <button type="button" className="btn-primary" onClick={handleStart} disabled={starting}>
          {starting ? "Loading..." : "Start exam"}
        </button>
        <Link to="/levels" className="link-button">
          Not now
        </Link>
      </div>
    </div>
  );
}

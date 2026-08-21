import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError } from "../api/client";
import {
  getCourseExamStatus,
  startCourseExamAttempt,
  submitCourseExamAttempt,
} from "../api/courseExam";
import type { ExamResult, Exercise, Skill, SubmittedAnswer } from "../api/types";
import { ExerciseItem } from "../components/exercises/ExerciseItem";
import { formatClock, formatWhen } from "./ExamPage";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

function ResultView({ result }: { result: ExamResult }) {
  return (
    <div className="exam-result">
      <p className="exam-result-verdict">
        {result.passed ? "✅ Passed!" : "❌ Not this time."}
      </p>
      <p className="exam-result-score">
        {result.correct_count}/{result.total_count} correct ({Math.round(result.score * 100)}%)
      </p>
      {result.passed ? (
        <p>Your certificate is now available.</p>
      ) : (
        <p>70% is needed to pass. Review your weak topics and try again.</p>
      )}
      <Link to={result.passed ? "/certificate" : "/levels"} className="btn-primary">
        {result.passed ? "View certificate" : "Back to levels"}
      </Link>
    </div>
  );
}

export function CourseExamPage() {
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
    queryKey: ["course-exam-status"],
    queryFn: getCourseExamStatus,
    enabled: !result,
  });

  async function handleSubmit(currentAnswers: Record<string, SubmittedAnswer>) {
    if (!attemptId || submittedRef.current) return;
    submittedRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const submitted = await submitCourseExamAttempt(
        attemptId,
        Object.entries(currentAnswers).map(([exercise_id, submitted_answer]) => ({
          exercise_id,
          submitted_answer,
        })),
      );
      setResult(submitted);
      queryClient.invalidateQueries({ queryKey: ["course-exam-status"] });
    } catch (err) {
      submittedRef.current = false;
      setError(err instanceof ApiError ? err.message : "Couldn't submit the exam.");
    } finally {
      setSubmitting(false);
    }
  }

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
      const attempt = await startCourseExamAttempt();
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

  useEffect(() => {
    if (status.data?.in_progress_attempt_id && !items && !starting) {
      handleStart();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status.data?.in_progress_attempt_id]);

  if (result) {
    return (
      <div className="page">
        <h1>Final exam</h1>
        <ResultView result={result} />
      </div>
    );
  }

  if (items && attemptId) {
    return (
      <div className="page">
        <h1>Final exam</h1>
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
            <ExerciseItem
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
        <h1>Final exam</h1>
        <p className="status">
          Pass the B2 exit exam first — the final exam covers the whole course, so it only makes
          sense once you've finished all four levels.
        </p>
        <Link to="/levels/B2/exam" className="btn-primary">
          Go to the B2 exam
        </Link>
      </div>
    );
  }

  if (data.passed) {
    return (
      <div className="page">
        <h1>Final exam</h1>
        <p className="status">You've already passed the final exam. Your certificate is ready.</p>
        <Link to="/certificate" className="btn-primary">
          View certificate
        </Link>
      </div>
    );
  }

  if (data.cooldown_until) {
    return (
      <div className="page">
        <h1>Final exam</h1>
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
      <h1>Final exam</h1>
      <p>
        44 questions across all four levels, ordered from easy to hard, 70% to pass, 15 minutes
        on the clock. Up to {data.attempts_per_window} attempts before a 24-hour cooldown. Passing
        unlocks your completion certificate.
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

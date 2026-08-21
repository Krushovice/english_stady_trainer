import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { getPlacementItems, getPlacementResult, submitPlacementTest } from "../api/placement";
import type { Exercise, PlacementResult, Skill, SubmittedAnswer } from "../api/types";
import { ExerciseItem } from "../components/exercises/ExerciseItem";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

function ResultView({ result }: { result: PlacementResult }) {
  const navigate = useNavigate();
  return (
    <div className="placement-result">
      <p className="placement-overall">
        Estimated level: <strong>{result.overall_level ?? "not enough data"}</strong>
      </p>
      <div className="placement-skill-rows">
        {result.skills.map((row) => (
          <div key={row.skill} className="placement-skill-row">
            <span>{SKILL_LABELS[row.skill]}</span>
            <span>
              {row.level ?? "not assessed"}
              {row.total != null && (
                <span className="status"> ({row.correct}/{row.total})</span>
              )}
            </span>
          </div>
        ))}
      </div>
      {result.recommended_modules.length > 0 && (
        <>
          <h2>Recommended starting modules</h2>
          <div className="card-grid">
            {result.recommended_modules.map((module) => (
              <Link
                key={module.id}
                to={`/levels/${module.level_code}/modules`}
                className="card"
              >
                <span className="card-title">{module.title}</span>
                <span className="status">{module.level_code}</span>
              </Link>
            ))}
          </div>
        </>
      )}
      <button type="button" className="btn-primary" onClick={() => navigate("/levels")}>
        Continue to lessons
      </button>
    </div>
  );
}

export function PlacementTestPage() {
  const [phase, setPhase] = useState<"intro" | "taking" | "result">("intro");
  const [items, setItems] = useState<Exercise[]>([]);
  const [answers, setAnswers] = useState<Record<string, SubmittedAnswer>>({});
  const [freshResult, setFreshResult] = useState<PlacementResult | null>(null);
  const [loadingItems, setLoadingItems] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const existingResult = useQuery({
    queryKey: ["placement-result"],
    queryFn: getPlacementResult,
  });

  async function startTest() {
    setError(null);
    setLoadingItems(true);
    try {
      setItems(await getPlacementItems());
      setPhase("taking");
    } catch {
      setError("Couldn't load the test. Please try again.");
    } finally {
      setLoadingItems(false);
    }
  }

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      const result = await submitPlacementTest(
        Object.entries(answers).map(([exercise_id, submitted_answer]) => ({
          exercise_id,
          submitted_answer,
        })),
      );
      setFreshResult(result);
      setPhase("result");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't submit the test.");
    } finally {
      setSubmitting(false);
    }
  }

  if (existingResult.isLoading) return <p className="status">Loading...</p>;

  if (phase !== "result" && existingResult.data?.placement_completed_at) {
    return (
      <div className="page">
        <h1>Placement test</h1>
        <p className="status">You've already taken this. Here's your result:</p>
        <ResultView result={existingResult.data} />
      </div>
    );
  }

  if (phase === "result" && freshResult) {
    return (
      <div className="page">
        <h1>Your result</h1>
        <ResultView result={freshResult} />
      </div>
    );
  }

  if (phase === "intro") {
    return (
      <div className="page">
        <h1>Placement test</h1>
        <p>
          About 24 questions covering grammar, vocabulary, reading, and listening. Takes
          10-15 minutes and estimates your level per skill — not just one number.
        </p>
        {error && <p className="form-error">{error}</p>}
        <div className="placement-actions">
          <button type="button" className="btn-primary" onClick={startTest} disabled={loadingItems}>
            {loadingItems ? "Loading..." : "Start test"}
          </button>
          <Link to="/levels" className="link-button">
            Skip for now
          </Link>
        </div>
      </div>
    );
  }

  // phase === "taking"
  return (
    <div className="page">
      <h1>Placement test</h1>
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
            onAnswer={(answer) =>
              setAnswers((prev) => ({ ...prev, [exercise.id]: answer }))
            }
          />
        </div>
      ))}
      {error && <p className="form-error">{error}</p>}
      <button type="button" className="btn-primary" onClick={handleSubmit} disabled={submitting}>
        {submitting ? "Submitting..." : "Submit test"}
      </button>
    </div>
  );
}

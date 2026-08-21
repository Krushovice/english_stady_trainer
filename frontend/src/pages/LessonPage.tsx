import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getLesson } from "../api/course";
import {
  getLessonCompletion,
  getMiniTest,
  listLessonExercises,
  submitAttempt,
} from "../api/exercises";
import type { AttemptResult, SubmittedAnswer } from "../api/types";
import { ExerciseCard } from "../components/exercises/ExerciseCard";
import { ExerciseItem } from "../components/exercises/ExerciseItem";
import { LessonBlockView } from "../components/LessonBlockView";

const SKILL_LABELS: Record<string, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

export function LessonPage() {
  const { lessonSlug } = useParams<{ lessonSlug: string }>();
  const queryClient = useQueryClient();

  const lessonQuery = useQuery({
    queryKey: ["lesson", lessonSlug],
    queryFn: () => getLesson(lessonSlug!),
    enabled: !!lessonSlug,
  });
  const exercisesQuery = useQuery({
    queryKey: ["lesson-exercises", lessonSlug],
    queryFn: () => listLessonExercises(lessonSlug!),
    enabled: !!lessonSlug,
  });
  const completionQuery = useQuery({
    queryKey: ["lesson-completion", lessonSlug],
    queryFn: () => getLessonCompletion(lessonSlug!),
    enabled: !!lessonSlug,
  });
  const miniTestQuery = useQuery({
    queryKey: ["mini-test", lessonSlug],
    queryFn: () => getMiniTest(lessonSlug!),
    enabled: !!lessonSlug,
  });

  const [answers, setAnswers] = useState<Record<string, SubmittedAnswer>>({});
  const [results, setResults] = useState<Record<string, AttemptResult>>({});
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);

  // An exercise counts as resolved either because it was just checked
  // correct in this session, or because the server already knows it's
  // correct from an earlier visit (not in the last attempt's wrong list).
  function isResolved(exerciseId: string): boolean {
    if (results[exerciseId]?.is_correct) return true;
    const completion = completionQuery.data;
    return !!completion?.attempted && !completion.wrong_exercise_ids.includes(exerciseId);
  }

  async function handleCheck() {
    const exercises = exercisesQuery.data ?? [];
    const pending = exercises.filter((exercise) => answers[exercise.id] && !isResolved(exercise.id));
    if (pending.length === 0) return;
    setChecking(true);
    setCheckError(null);
    // Sequential, not Promise.all: a single failed submission must not
    // discard the results of the others that already succeeded.
    let hadError = false;
    for (const exercise of pending) {
      try {
        const result = await submitAttempt(exercise.id, answers[exercise.id]);
        setResults((prev) => ({ ...prev, [exercise.id]: result }));
      } catch {
        hadError = true;
      }
    }
    // Mirrors ExerciseCard's invalidations, plus this lesson's completion
    // (unlock state) and the module list (locked/passed badges).
    queryClient.invalidateQueries({ queryKey: ["lesson-completion", lessonSlug] });
    queryClient.invalidateQueries({ queryKey: ["modules"] });
    queryClient.invalidateQueries({ queryKey: ["progress"] });
    queryClient.invalidateQueries({ queryKey: ["daily-quiz"] });
    queryClient.invalidateQueries({ queryKey: ["review-due"] });
    if (hadError) setCheckError("Couldn't check some of your answers. Please try again.");
    setChecking(false);
  }

  if (lessonQuery.isLoading) return <p className="status">Loading lesson...</p>;
  if (lessonQuery.error || !lessonQuery.data)
    return <p className="status status-error">Couldn't load this lesson.</p>;

  const lesson = lessonQuery.data;
  const exercises = exercisesQuery.data ?? [];
  const completion = completionQuery.data;
  const resolvedCount = exercises.filter((exercise) => isResolved(exercise.id)).length;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Levels
      </Link>
      <h1>
        {completion?.passed ? "✅ " : ""}
        {lesson.title}
      </h1>

      {lesson.blocks
        .slice()
        .sort((a, b) => a.order_index - b.order_index)
        .map((block) => (
          <LessonBlockView key={block.id} block={block} />
        ))}

      {lesson.vocabulary.length > 0 && (
        <section className="lesson-block">
          <h2>Vocabulary</h2>
          <dl className="vocabulary-list">
            {lesson.vocabulary.map((word) => (
              <div key={word.id} className="vocabulary-item">
                <dt>{word.headword}</dt>
                <dd>{word.translation}</dd>
                <dd className="example">{word.example_sentence}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {lesson.grammar_topics.length > 0 && (
        <section className="lesson-block">
          <h2>Grammar</h2>
          {lesson.grammar_topics.map((topic) => (
            <div key={topic.id} className="grammar-topic">
              <h3>{topic.title}</h3>
              <p>{topic.description}</p>
            </div>
          ))}
        </section>
      )}

      <section className="lesson-block">
        <h2>Exercises</h2>

        {completion?.attempted && !completion.passed && completion.wrong_exercise_ids.length > 0 && (
          <p className="status status-error">
            {completion.wrong_exercise_ids.length} exercise
            {completion.wrong_exercise_ids.length === 1 ? "" : "s"} from your last attempt still
            need{completion.wrong_exercise_ids.length === 1 ? "s" : ""} fixing — 70% correct
            unlocks the next lesson.
          </p>
        )}

        {exercisesQuery.isLoading && <p className="status">Loading exercises...</p>}
        {exercisesQuery.error && <p className="status status-error">Couldn't load exercises.</p>}
        {exercises.length === 0 && !exercisesQuery.isLoading && (
          <p className="status">No exercises for this lesson yet.</p>
        )}

        {exercises.length > 0 && (
          <>
            <p className="status">
              {resolvedCount}/{exercises.length} correct
            </p>
            {exercises.map((exercise, i) => {
              const resolved = isResolved(exercise.id);
              const result = results[exercise.id];
              return (
                <div
                  key={exercise.id}
                  className={
                    "exercise-card" +
                    (resolved ? " correct" : result && !result.is_correct ? " incorrect" : "")
                  }
                >
                  <div className="exercise-meta">
                    <span className="badge">{i + 1}</span>
                    <span className="badge badge-muted">
                      {SKILL_LABELS[exercise.skill] ?? exercise.skill}
                    </span>
                  </div>
                  <ExerciseItem
                    exercise={exercise}
                    disabled={resolved}
                    onAnswer={(answer) =>
                      setAnswers((prev) => ({ ...prev, [exercise.id]: answer }))
                    }
                  />
                  {resolved && (
                    <div className="exercise-result">
                      <p className="result-verdict">✅ Correct</p>
                      {result?.explanation && (
                        <p className="result-explanation">{result.explanation}</p>
                      )}
                    </div>
                  )}
                  {!resolved && result && !result.is_correct && (
                    <div className="exercise-result">
                      <p className="result-verdict">Not quite.</p>
                      <p className="result-explanation">{result.explanation}</p>
                    </div>
                  )}
                </div>
              );
            })}
            {checkError && <p className="form-error">{checkError}</p>}
            <button type="button" className="btn-primary" onClick={handleCheck} disabled={checking}>
              {checking ? "Checking..." : "Check"}
            </button>
          </>
        )}
      </section>

      {miniTestQuery.data && miniTestQuery.data.exercises.length > 0 && (
        <section className="lesson-block mini-test">
          <h2>🔁 Quick review: {miniTestQuery.data.previous_lesson_title}</h2>
          <p className="status">
            Five questions on the previous topic before you move on.
          </p>
          {miniTestQuery.data.exercises.map((exercise) => (
            <ExerciseCard key={exercise.id} exercise={exercise} />
          ))}
        </section>
      )}
    </div>
  );
}

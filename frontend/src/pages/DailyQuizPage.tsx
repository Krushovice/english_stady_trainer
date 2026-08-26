import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { getDailyQuiz, submitAttempt } from "../api/exercises";
import type { AttemptResult, SubmittedAnswer } from "../api/types";
import { ExerciseItem } from "../components/exercises/ExerciseItem";

const SKILL_LABELS: Record<string, string> = {
  grammar: "Грамматика",
  vocabulary: "Лексика",
  reading: "Чтение",
  listening: "Аудирование",
  writing: "Письмо",
  speaking: "Говорение",
};

export function DailyQuizPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["daily-quiz"],
    queryFn: getDailyQuiz,
  });

  const [answers, setAnswers] = useState<Record<string, SubmittedAnswer>>({});
  const [results, setResults] = useState<Record<string, AttemptResult>>({});
  const [checking, setChecking] = useState(false);
  const [checkError, setCheckError] = useState<string | null>(null);

  const exercises = data ?? [];
  const allAnswered = exercises.length > 0 && exercises.every((exercise) => answers[exercise.id]);
  const allChecked = exercises.length > 0 && exercises.every((exercise) => results[exercise.id]);
  const correctCount = exercises.filter((exercise) => results[exercise.id]?.is_correct).length;

  async function handleCheck() {
    setChecking(true);
    setCheckError(null);
    let hadError = false;
    // Sequential, not Promise.all: a single failed submission must not
    // discard the results of the others that already succeeded.
    for (const exercise of exercises) {
      try {
        const result = await submitAttempt(exercise.id, answers[exercise.id]);
        setResults((prev) => ({ ...prev, [exercise.id]: result }));
      } catch {
        hadError = true;
      }
    }
    queryClient.invalidateQueries({ queryKey: ["progress"] });
    queryClient.invalidateQueries({ queryKey: ["daily-quiz"] });
    queryClient.invalidateQueries({ queryKey: ["review-due"] });
    if (hadError) setCheckError("Не удалось проверить некоторые ответы. Попробуйте ещё раз.");
    setChecking(false);
  }

  if (isLoading) return <p className="status">Загрузка сегодняшнего теста...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить ежедневный тест.</p>;

  return (
    <div className="page">
      <h1>Ежедневный тест</h1>
      <p className="status">Подборка из уже изученных уроков — новая каждый день.</p>

      {exercises.length === 0 ? (
        <p className="status">
          Пока нечего тестировать — сначала выполните упражнения в{" "}
          <Link to="/levels">уроке</Link>.
        </p>
      ) : (
        <>
          {allChecked && (
            <div className="exam-result">
              <p
                className={
                  "exam-result-verdict" +
                  (correctCount / exercises.length >= 0.7 ? " is-pass" : " is-fail")
                }
              >
                {correctCount === exercises.length
                  ? "Отлично, всё верно!"
                  : correctCount / exercises.length >= 0.7
                    ? "Хороший результат"
                    : "Есть над чем поработать"}
              </p>
              <p className="exam-result-score">
                Верно: {correctCount}/{exercises.length}
              </p>
              {correctCount < exercises.length && (
                <p>Посмотрите объяснения под заданиями ниже и повторите похожие упражнения.</p>
              )}
            </div>
          )}

          {exercises.map((exercise, i) => {
            const result = results[exercise.id];
            return (
              <div
                key={exercise.id}
                className={
                  "exercise-card" +
                  (result ? (result.is_correct ? " correct" : " incorrect") : "")
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
                  disabled={!!result}
                  onAnswer={(answer) => setAnswers((prev) => ({ ...prev, [exercise.id]: answer }))}
                />
                {result && (
                  <div className="exercise-result">
                    <p className="result-verdict">{result.is_correct ? "Верно" : "Не совсем."}</p>
                    <p className="result-explanation">{result.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}

          {checkError && <p className="form-error">{checkError}</p>}
          {!allChecked && (
            <button
              type="button"
              className="btn-primary"
              onClick={handleCheck}
              disabled={!allAnswered || checking}
            >
              {checking ? "Проверка..." : "Проверить"}
            </button>
          )}
        </>
      )}
    </div>
  );
}

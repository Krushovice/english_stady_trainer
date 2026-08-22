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
  grammar: "Грамматика",
  vocabulary: "Лексика",
  reading: "Чтение",
  listening: "Аудирование",
  writing: "Письмо",
  speaking: "Говорение",
};

function ResultView({ result }: { result: ExamResult }) {
  return (
    <div className="exam-result">
      <p className={"exam-result-verdict" + (result.passed ? " is-pass" : " is-fail")}>
        {result.passed ? "Сдано" : "Не в этот раз"}
      </p>
      <p className="exam-result-score">
        Верно: {result.correct_count}/{result.total_count} ({Math.round(result.score * 100)}%)
      </p>
      {result.passed ? (
        <p>Ваш сертификат теперь доступен.</p>
      ) : (
        <p>Для сдачи нужно 70%. Повторите слабые темы и попробуйте снова.</p>
      )}
      <Link to={result.passed ? "/certificate" : "/levels"} className="btn-primary">
        {result.passed ? "Посмотреть сертификат" : "Назад к уровням"}
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
      setError(err instanceof ApiError ? err.message : "Не удалось отправить экзамен.");
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
      setError(err instanceof ApiError ? err.message : "Не удалось начать экзамен.");
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
        <h1>Финальный экзамен</h1>
        <ResultView result={result} />
      </div>
    );
  }

  if (items && attemptId) {
    return (
      <div className="page">
        <h1>Финальный экзамен</h1>
        <p className="exam-timer">
          Осталось времени: <strong>{formatClock(remainingSeconds ?? 0)}</strong>
        </p>
        <p className="status">
          Отвечено: {Object.keys(answers).length}/{items.length}
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
          {submitting ? "Отправка..." : "Отправить экзамен"}
        </button>
      </div>
    );
  }

  if (status.isLoading) return <p className="status">Загрузка...</p>;
  if (status.error) return <p className="status status-error">Не удалось загрузить статус экзамена.</p>;
  const data = status.data!;

  if (!data.exam_available) {
    return (
      <div className="page">
        <h1>Финальный экзамен</h1>
        <p className="status">
          Сначала сдайте выходной экзамен B2 — финальный экзамен охватывает весь курс, поэтому
          имеет смысл только после завершения всех четырёх уровней.
        </p>
        <Link to="/levels/B2/exam" className="btn-primary">
          К экзамену уровня B2
        </Link>
      </div>
    );
  }

  if (data.passed) {
    return (
      <div className="page">
        <h1>Финальный экзамен</h1>
        <p className="status">Вы уже сдали финальный экзамен. Ваш сертификат готов.</p>
        <Link to="/certificate" className="btn-primary">
          Посмотреть сертификат
        </Link>
      </div>
    );
  }

  if (data.cooldown_until) {
    return (
      <div className="page">
        <h1>Финальный экзамен</h1>
        <p className="status status-error">
          Неудачных попыток подряд: {data.attempts_used_in_window}. Следующая попытка будет доступна{" "}
          {formatWhen(data.cooldown_until)}.
        </p>
        <Link to="/levels" className="back-link">
          &larr; Уровни
        </Link>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Финальный экзамен</h1>
      <p>
        44 вопроса по всем четырём уровням, от лёгких к сложным, для сдачи нужно 70%, на
        выполнение 15 минут. До {data.attempts_per_window} попыток, затем 24-часовая пауза.
        Сдача открывает сертификат о завершении курса.
      </p>
      <p className="status">
        Использовано попыток: {data.attempts_used_in_window}/{data.attempts_per_window}
      </p>
      {error && <p className="form-error">{error}</p>}
      <div className="placement-actions">
        <button type="button" className="btn-primary" onClick={handleStart} disabled={starting}>
          {starting ? "Загрузка..." : "Начать экзамен"}
        </button>
        <Link to="/levels" className="link-button">
          Не сейчас
        </Link>
      </div>
    </div>
  );
}

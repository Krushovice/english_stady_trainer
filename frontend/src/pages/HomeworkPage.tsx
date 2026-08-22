import { useEffect, useState } from "react";
import { generateHomework, getHomework, submitHomeworkTask } from "../api/homework";
import { ApiError } from "../api/client";
import type { Homework } from "../api/types";
import { WritingFeedbackCard } from "../components/WritingFeedbackCard";

const STORAGE_KEY = "et_homework_id";

function HomeworkTaskView({
  homework,
  taskId,
  instruction,
  onSubmitted,
}: {
  homework: Homework;
  taskId: string;
  instruction: string;
  onSubmitted: (homework: Homework) => void;
}) {
  const attempt = homework.attempts.find((a) => a.task_id === taskId);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!text.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const newAttempt = await submitHomeworkTask(homework.id, taskId, text);
      onSubmitted({ ...homework, attempts: [...homework.attempts, newAttempt] });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось отправить это задание.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="homework-task">
      <p className="homework-instruction">{instruction}</p>
      {attempt ? (
        <>
          <p className="homework-submitted-text">{attempt.submitted_text}</p>
          <WritingFeedbackCard feedback={attempt.feedback} />
        </>
      ) : (
        <>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="Напишите свой ответ здесь..."
            disabled={submitting}
          />
          {error && <p className="status status-error">{error}</p>}
          <button type="button" className="btn-primary" onClick={handleSubmit} disabled={submitting || !text.trim()}>
            {submitting ? "Отправка..." : "Отправить"}
          </button>
        </>
      )}
    </div>
  );
}

export function HomeworkPage() {
  const [homework, setHomework] = useState<Homework | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (!storedId) return;
    setLoading(true);
    getHomework(storedId)
      .then(setHomework)
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const newHomework = await generateHomework();
      setHomework(newHomework);
      localStorage.setItem(STORAGE_KEY, newHomework.id);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Не удалось создать домашнее задание. Попробуйте ещё раз.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <h1>Домашнее задание</h1>
      <p className="status">
        Персонализированные письменные задания на основе последнего изученного урока,
        с AI-фидбеком на каждый отправленный ответ.
      </p>

      {error && <p className="status status-error">{error}</p>}

      {homework && (
        <>
          <h2>{homework.lesson_title}</h2>
          {homework.tasks.map((task) => (
            <HomeworkTaskView
              key={task.id}
              homework={homework}
              taskId={task.id}
              instruction={task.instruction}
              onSubmitted={setHomework}
            />
          ))}
        </>
      )}

      <button type="button" className="btn-primary" onClick={handleGenerate} disabled={loading}>
        {loading ? "Создание..." : homework ? "Создать новое задание" : "Создать домашнее задание"}
      </button>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ApiError } from "../api/client";
import {
  generateSpeakingPrompt,
  getSpeakingAttempt,
  startLessonSpeakingAttempt,
  submitSpeakingAttempt,
} from "../api/speaking";
import type { SpeakingAttempt } from "../api/types";
import { AudioRecorder } from "../components/AudioRecorder";
import { WritingFeedbackCard } from "../components/WritingFeedbackCard";

const STORAGE_KEY = "et_speaking_attempt_id";

export function SpeakingPage() {
  const [searchParams] = useSearchParams();
  const lessonSlug = searchParams.get("lessonSlug");

  const [attempt, setAttempt] = useState<SpeakingAttempt | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGeneratePrompt() {
    setLoading(true);
    setError(null);
    try {
      const newAttempt = lessonSlug
        ? await startLessonSpeakingAttempt(lessonSlug)
        : await generateSpeakingPrompt();
      setAttempt(newAttempt);
      localStorage.setItem(STORAGE_KEY, newAttempt.id);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось создать задание для говорения.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Arrived from a lesson's own speaking block: start that lesson's task
    // right away instead of making the learner click twice.
    if (lessonSlug) {
      handleGeneratePrompt();
      return;
    }
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (!storedId) return;
    setLoading(true);
    getSpeakingAttempt(storedId)
      .then(setAttempt)
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lessonSlug]);

  async function handleSubmit(audio: Blob, filename: string) {
    if (!attempt) return;
    setSubmitting(true);
    setError(null);
    try {
      setAttempt(await submitSpeakingAttempt(attempt.id, audio, filename));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось отправить запись.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page">
      <h1>Тренировка речи</h1>
      <p className="status">
        {lessonSlug
          ? "Задание этого урока — запишите ответ и получите AI-фидбек по грамматике, лексике и естественности речи."
          : "Персонализированное задание для говорения на основе последнего изученного урока — запишите ответ и получите AI-фидбек по грамматике, лексике и естественности речи."}
      </p>

      {error && <p className="status status-error">{error}</p>}
      {loading && !attempt && <p className="status">Загрузка задания...</p>}

      {attempt && (
        <div className="speaking-prompt">
          <h2>{attempt.lesson_title}</h2>
          <p className="speaking-prompt-text">{attempt.prompt}</p>

          {attempt.submitted_at ? (
            <>
              {attempt.transcript && (
                <div className="speaking-transcript">
                  <h3>Мы услышали</h3>
                  <p>{attempt.transcript}</p>
                </div>
              )}
              {attempt.feedback && <WritingFeedbackCard feedback={attempt.feedback} />}
            </>
          ) : (
            <AudioRecorder onSubmit={handleSubmit} submitting={submitting} />
          )}
        </div>
      )}

      {!(lessonSlug && !attempt) && (
        <button
          type="button"
          className="btn-primary"
          onClick={handleGeneratePrompt}
          disabled={loading}
        >
          {loading ? "Создание..." : attempt ? "Получить новое задание" : "Получить задание для говорения"}
        </button>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { generateSpeakingPrompt, getSpeakingAttempt, submitSpeakingAttempt } from "../api/speaking";
import type { SpeakingAttempt } from "../api/types";
import { AudioRecorder } from "../components/AudioRecorder";
import { WritingFeedbackCard } from "../components/WritingFeedbackCard";

const STORAGE_KEY = "et_speaking_attempt_id";

export function SpeakingPage() {
  const [attempt, setAttempt] = useState<SpeakingAttempt | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (!storedId) return;
    setLoading(true);
    getSpeakingAttempt(storedId)
      .then(setAttempt)
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
  }, []);

  async function handleGeneratePrompt() {
    setLoading(true);
    setError(null);
    try {
      const newAttempt = await generateSpeakingPrompt();
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
      <h1>Говорение</h1>
      <p className="status">
        Персонализированное задание для говорения на основе последнего изученного урока —
        запишите ответ и получите AI-фидбек по грамматике, лексике и естественности речи.
      </p>

      {error && <p className="status status-error">{error}</p>}

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

      <button type="button" className="btn-primary" onClick={handleGeneratePrompt} disabled={loading}>
        {loading ? "Создание..." : attempt ? "Получить новое задание" : "Получить задание для говорения"}
      </button>
    </div>
  );
}

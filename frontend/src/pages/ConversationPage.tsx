import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import {
  endConversation,
  getConversation,
  sendConversationMessage,
  startConversation,
} from "../api/conversation";
import type { ConversationSession } from "../api/types";

const STORAGE_KEY = "et_conversation_id";

const ANALYSIS_SECTIONS: { key: keyof NonNullable<ConversationSession["analysis"]>; label: string }[] = [
  { key: "recurring_mistakes", label: "Повторяющиеся ошибки" },
  { key: "useful_vocabulary", label: "Полезная лексика" },
  { key: "natural_alternatives", label: "Более естественные варианты" },
  { key: "grammar_topics_to_review", label: "Грамматика для повторения" },
  { key: "recommended_practice", label: "Рекомендуемая практика" },
];

export function ConversationPage() {
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [topic, setTopic] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const storedId = localStorage.getItem(STORAGE_KEY);
    if (!storedId) return;
    setLoading(true);
    getConversation(storedId)
      .then(setSession)
      .catch(() => localStorage.removeItem(STORAGE_KEY))
      .finally(() => setLoading(false));
  }, []);

  async function handleStart() {
    setLoading(true);
    setError(null);
    try {
      const newSession = await startConversation(topic);
      setSession(newSession);
      localStorage.setItem(STORAGE_KEY, newSession.id);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось начать разговор.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    if (!session || !message.trim()) return;
    setSending(true);
    setError(null);
    const text = message;
    setMessage("");
    try {
      const reply = await sendConversationMessage(session.id, text);
      setSession({
        ...session,
        messages: [
          ...session.messages,
          {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
            created_at: new Date().toISOString(),
          },
          reply,
        ],
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось отправить сообщение.");
      setMessage(text);
    } finally {
      setSending(false);
    }
  }

  async function handleEnd() {
    if (!session) return;
    setEnding(true);
    setError(null);
    try {
      setSession(await endConversation(session.id));
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось завершить разговор.",
      );
    } finally {
      setEnding(false);
    }
  }

  function handleStartNew() {
    setSession(null);
    setTopic("");
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
  }

  return (
    <div className="page">
      <h1>Разговор</h1>
      <p className="status">
        Потренируйте живой разговор с AI-собеседником — после завершения сессии
        вы получите разбор ваших ошибок и полезную лексику.
      </p>

      {error && <p className="status status-error">{error}</p>}

      {!session && (
        <div className="conversation-start">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Тема (необязательно) — например, путешествия, хобби, работа"
            disabled={loading}
          />
          <button type="button" className="btn-primary" onClick={handleStart} disabled={loading}>
            {loading ? "Начинаем..." : "Начать разговор"}
          </button>
        </div>
      )}

      {session && (
        <>
          <div className="chat-messages">
            {session.messages.map((m) => (
              <p key={m.id} className={`chat-message chat-message-${m.role}`}>
                {m.content}
              </p>
            ))}
          </div>

          {!session.ended_at ? (
            <div className="chat-input-row">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Введите ответ..."
                disabled={sending}
              />
              <button type="button" className="btn-primary" onClick={handleSend} disabled={sending || !message.trim()}>
                Отправить
              </button>
              <button type="button" onClick={handleEnd} disabled={ending || sending}>
                {ending ? "Завершение..." : "Завершить разговор"}
              </button>
            </div>
          ) : (
            <>
              {session.analysis && (
                <div className="conversation-analysis">
                  {ANALYSIS_SECTIONS.map(({ key, label }) => (
                    <div key={key} className="feedback-section">
                      <h4>{label}</h4>
                      <p>{session.analysis![key]}</p>
                    </div>
                  ))}
                </div>
              )}
              <button type="button" onClick={handleStartNew}>
                Начать новый разговор
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}

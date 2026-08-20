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
  { key: "recurring_mistakes", label: "Recurring mistakes" },
  { key: "useful_vocabulary", label: "Useful vocabulary" },
  { key: "natural_alternatives", label: "Natural alternatives" },
  { key: "grammar_topics_to_review", label: "Grammar topics to review" },
  { key: "recommended_practice", label: "Recommended practice" },
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
        err instanceof ApiError ? err.message : "Couldn't start a conversation.",
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
      setError(err instanceof ApiError ? err.message : "Couldn't send your message.");
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
        err instanceof ApiError ? err.message : "Couldn't end the conversation.",
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
      <h1>Talk</h1>
      <p className="status">
        Practise a natural conversation with an AI partner — after you end the
        session, you'll get an analysis of your mistakes and useful vocabulary.
      </p>

      {error && <p className="status status-error">{error}</p>}

      {!session && (
        <div className="conversation-start">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Topic (optional) — e.g. travel, hobbies, work"
            disabled={loading}
          />
          <button type="button" onClick={handleStart} disabled={loading}>
            {loading ? "Starting..." : "Start conversation"}
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
                placeholder="Type your reply..."
                disabled={sending}
              />
              <button type="button" onClick={handleSend} disabled={sending || !message.trim()}>
                Send
              </button>
              <button type="button" onClick={handleEnd} disabled={ending || sending}>
                {ending ? "Ending..." : "End conversation"}
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
                Start new conversation
              </button>
            </>
          )}
        </>
      )}
    </div>
  );
}

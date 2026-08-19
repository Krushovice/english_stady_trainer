import type { LessonBlock } from "../api/types";

// Only `vocabulary`/`grammar` blocks have a validated shape server-side
// (app/schemas/content.py) — they're rendered separately from the lesson's
// top-level `vocabulary`/`grammar_topics` fields, so this component skips
// those two block types entirely rather than showing the same content twice.
// `exercises` is skipped too: real exercises come from a dedicated fetch
// with proper submit/feedback UI, not from this read-only block content.
const SKIPPED_TYPES = new Set(["vocabulary", "grammar", "exercises"]);

// Immersion is graded by level in content authoring (A1-A2 blocks author
// in Russian directly, B2 drops this field) — this is only the B1 middle
// ground: the English text stays primary, a short Russian gloss is a click
// away instead of shown inline, so it's a safety net, not a crutch. See
// docs/decisions.md.
function RuSummary({ text }: { text: string }) {
  if (!text) return null;
  return (
    <details className="ru-summary">
      <summary>Кратко на русском</summary>
      <p>{text}</p>
    </details>
  );
}

export function LessonBlockView({ block }: { block: LessonBlock }) {
  if (SKIPPED_TYPES.has(block.block_type)) return null;

  const content = block.content;

  switch (block.block_type) {
    case "learning_goals": {
      const goals = asStringArray(content.goals);
      return (
        <section className="lesson-block">
          <h2>Learning goals</h2>
          <ul>
            {goals.map((goal, i) => (
              <li key={i}>{goal}</li>
            ))}
          </ul>
        </section>
      );
    }

    case "context":
      return (
        <section className="lesson-block">
          <h2>Context</h2>
          <p>{asString(content.text)}</p>
          <RuSummary text={asString(content.summary_ru)} />
        </section>
      );

    case "examples": {
      const dialogues = asArray<{
        title?: string;
        lines?: { speaker: string; text: string }[];
      }>(content.dialogues);
      return (
        <section className="lesson-block">
          <h2>Examples</h2>
          {dialogues.map((dialogue, i) => (
            <div key={i} className="dialogue">
              {dialogue.title && <h3>{dialogue.title}</h3>}
              {(dialogue.lines ?? []).map((line, j) => (
                <p key={j} className="dialogue-line">
                  <strong>{line.speaker}:</strong> {line.text}
                </p>
              ))}
            </div>
          ))}
        </section>
      );
    }

    case "reading":
      return (
        <section className="lesson-block">
          <h2>{asString(content.title) || "Reading"}</h2>
          <p>{asString(content.text)}</p>
          <RuSummary text={asString(content.summary_ru)} />
        </section>
      );

    case "listening": {
      const note = asString(content.note);
      const transcript = asString(content.transcript);
      return (
        <section className="lesson-block">
          <h2>Listening</h2>
          {note && <p className="note">{note}</p>}
          {transcript && <p className="transcript">{transcript}</p>}
        </section>
      );
    }

    case "speaking":
      return (
        <section className="lesson-block">
          <h2>Speaking</h2>
          <p>{asString(content.prompt)}</p>
        </section>
      );

    case "homework": {
      const tasks = asArray<{ type?: string; instructions?: string }>(content.tasks);
      return (
        <section className="lesson-block">
          <h2>Homework</h2>
          <ul>
            {tasks.map((task, i) => (
              <li key={i}>{task.instructions}</li>
            ))}
          </ul>
        </section>
      );
    }

    case "review":
      return content.note ? (
        <section className="lesson-block">
          <h2>Review</h2>
          <p className="note">{asString(content.note)}</p>
        </section>
      ) : null;

    default:
      // Unknown block type — show it rather than silently dropping content.
      return (
        <section className="lesson-block">
          <h2>{block.block_type}</h2>
          <pre className="raw-content">{JSON.stringify(content, null, 2)}</pre>
        </section>
      );
  }
}

function asString(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

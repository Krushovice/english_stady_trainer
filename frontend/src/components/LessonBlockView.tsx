import { assetUrl } from "../api/client";
import type { LessonBlock } from "../api/types";

// Only `vocabulary`/`grammar` blocks have a validated shape server-side
// (app/schemas/content.py) — they're rendered separately from the lesson's
// top-level `vocabulary`/`grammar_topics` fields, so this component skips
// those two block types entirely rather than showing the same content twice.
// `exercises` and `mini_test` are skipped too: both are raw exercise-authoring
// data, not display content — real exercises and the mini-test come from
// dedicated fetches with proper submit/feedback UI (`LessonPage`'s own
// mini-test section), not from this read-only block renderer. `review` is
// skipped as well — its `note` is an authoring reminder ("review items are
// generated automatically, nothing to author here"), never learner-facing
// content, so it has nothing to render.
const SKIPPED_TYPES = new Set(["vocabulary", "grammar", "exercises", "mini_test", "review"]);

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
          <h2>Цели урока</h2>
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
          <h2>Контекст</h2>
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
          <h2>Примеры</h2>
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
          <h2>{asString(content.title) || "Чтение"}</h2>
          <p>{asString(content.text)}</p>
          <RuSummary text={asString(content.summary_ru)} />
        </section>
      );

    case "listening": {
      const note = asString(content.note);
      const transcript = asString(content.transcript);
      const audioUrl = asString(content.audio_url);
      return (
        <section className="lesson-block">
          <h2>Аудирование</h2>
          {audioUrl && (
            <audio controls src={assetUrl(audioUrl)} className="listening-player">
              Ваш браузер не поддерживает воспроизведение аудио.
            </audio>
          )}
          {note && <p className="note">{note}</p>}
          {transcript && (
            <details className="ru-summary">
              <summary>Показать текст</summary>
              <p className="transcript">{transcript}</p>
            </details>
          )}
        </section>
      );
    }

    case "speaking":
      return (
        <section className="lesson-block">
          <h2>Говорение</h2>
          <p>{asString(content.prompt)}</p>
        </section>
      );

    case "homework": {
      const tasks = asArray<{ type?: string; instructions?: string }>(content.tasks);
      return (
        <section className="lesson-block">
          <h2>Домашнее задание</h2>
          <ul>
            {tasks.map((task, i) => (
              <li key={i}>{task.instructions}</li>
            ))}
          </ul>
        </section>
      );
    }

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

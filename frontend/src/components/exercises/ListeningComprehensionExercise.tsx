import { useId, useState } from "react";
import { assetUrl } from "../../api/client";
import type { ListeningComprehensionPrompt } from "../../api/types";

export function ListeningComprehensionExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: ListeningComprehensionPrompt;
  disabled: boolean;
  onChange: (answers: Record<string, string>) => void;
}) {
  const groupId = useId();
  const [answers, setAnswers] = useState<Record<string, string>>({});

  function pick(questionId: string, optionId: string) {
    const next = { ...answers, [questionId]: optionId };
    setAnswers(next);
    onChange(next);
  }

  return (
    <div className="exercise-prompt listening-comprehension">
      <audio controls src={assetUrl(prompt.audio_url)} className="listening-player">
        Ваш браузер не поддерживает воспроизведение аудио.
      </audio>
      {prompt.questions.map((question) => (
        <fieldset key={question.id} disabled={disabled}>
          <legend>{question.text}</legend>
          {question.options.map((option) => (
            <label key={option.id} className="option-row">
              <input
                type="radio"
                name={`${groupId}-${question.id}`}
                onChange={() => pick(question.id, option.id)}
              />
              {option.text}
            </label>
          ))}
        </fieldset>
      ))}
      {/* Collapsed by default — reading it before answering would defeat the
          point of a listening exercise. See docs/decisions.md. */}
      <details className="ru-summary">
        <summary>Показать текст</summary>
        <p>{prompt.transcript}</p>
      </details>
    </div>
  );
}

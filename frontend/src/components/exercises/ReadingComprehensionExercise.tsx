import { useId, useState } from "react";
import type { ReadingComprehensionPrompt } from "../../api/types";

export function ReadingComprehensionExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: ReadingComprehensionPrompt;
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
    <div className="exercise-prompt reading-comprehension">
      <p className="passage">{prompt.passage}</p>
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
    </div>
  );
}

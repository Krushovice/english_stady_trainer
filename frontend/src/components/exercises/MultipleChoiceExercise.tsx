import { useId } from "react";
import type { MultipleChoicePrompt } from "../../api/types";

export function MultipleChoiceExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: MultipleChoicePrompt;
  disabled: boolean;
  onChange: (optionId: string) => void;
}) {
  const name = useId();

  return (
    <fieldset className="exercise-prompt" disabled={disabled}>
      <legend>{prompt.question}</legend>
      {prompt.options.map((option) => (
        <label key={option.id} className="option-row">
          <input type="radio" name={name} value={option.id} onChange={() => onChange(option.id)} />
          {option.text}
        </label>
      ))}
    </fieldset>
  );
}

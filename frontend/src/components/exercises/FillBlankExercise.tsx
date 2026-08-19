import { useState } from "react";
import type { FillBlankPrompt } from "../../api/types";

export function FillBlankExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: FillBlankPrompt;
  disabled: boolean;
  onChange: (blanks: string[]) => void;
}) {
  const parts = prompt.text.split("___");
  const blankCount = parts.length - 1;
  const [values, setValues] = useState<string[]>(() => Array(blankCount).fill(""));

  function updateBlank(index: number, value: string) {
    const next = [...values];
    next[index] = value;
    setValues(next);
    onChange(next);
  }

  return (
    <div className="exercise-prompt fill-blank">
      {parts.map((part, i) => (
        <span key={i}>
          {part}
          {i < blankCount && (
            <input
              type="text"
              className="blank-input"
              value={values[i]}
              disabled={disabled}
              onChange={(e) => updateBlank(i, e.target.value)}
              size={Math.max(4, values[i].length || 6)}
            />
          )}
        </span>
      ))}
    </div>
  );
}

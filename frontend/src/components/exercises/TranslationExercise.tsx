import { useState } from "react";
import type { TranslationPrompt } from "../../api/types";

export function TranslationExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: TranslationPrompt;
  disabled: boolean;
  onChange: (text: string) => void;
}) {
  const [value, setValue] = useState("");

  return (
    <div className="exercise-prompt">
      <p className="translation-source">{prompt.text}</p>
      <input
        type="text"
        className="translation-input"
        value={value}
        disabled={disabled}
        placeholder="Переведите на английский"
        onChange={(e) => {
          setValue(e.target.value);
          onChange(e.target.value);
        }}
      />
    </div>
  );
}

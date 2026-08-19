import { useState } from "react";
import type { SentenceOrderingPrompt } from "../../api/types";

interface Word {
  word: string;
  key: number;
}

export function SentenceOrderingExercise({
  prompt,
  disabled,
  onChange,
}: {
  prompt: SentenceOrderingPrompt;
  disabled: boolean;
  onChange: (order: string[]) => void;
}) {
  const [available, setAvailable] = useState<Word[]>(
    prompt.words.map((word, key) => ({ word, key })),
  );
  const [chosen, setChosen] = useState<Word[]>([]);

  function pick(item: Word) {
    const nextAvailable = available.filter((w) => w.key !== item.key);
    const nextChosen = [...chosen, item];
    setAvailable(nextAvailable);
    setChosen(nextChosen);
    onChange(nextChosen.map((w) => w.word));
  }

  function unpick(item: Word) {
    const nextChosen = chosen.filter((w) => w.key !== item.key);
    const nextAvailable = [...available, item];
    setChosen(nextChosen);
    setAvailable(nextAvailable);
    onChange(nextChosen.map((w) => w.word));
  }

  return (
    <div className="exercise-prompt sentence-ordering">
      <div className="word-slot-row">
        {chosen.length === 0 && <span className="placeholder">Tap words below, in order</span>}
        {chosen.map((item) => (
          <button
            key={item.key}
            type="button"
            className="word-chip chosen"
            disabled={disabled}
            onClick={() => unpick(item)}
          >
            {item.word}
          </button>
        ))}
      </div>
      <div className="word-bank">
        {available.map((item) => (
          <button
            key={item.key}
            type="button"
            className="word-chip"
            disabled={disabled}
            onClick={() => pick(item)}
          >
            {item.word}
          </button>
        ))}
      </div>
    </div>
  );
}

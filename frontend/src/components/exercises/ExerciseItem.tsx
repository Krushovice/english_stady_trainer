import type { Exercise, SubmittedAnswer } from "../../api/types";
import { FillBlankExercise } from "./FillBlankExercise";
import { ListeningComprehensionExercise } from "./ListeningComprehensionExercise";
import { MultipleChoiceExercise } from "./MultipleChoiceExercise";
import { ReadingComprehensionExercise } from "./ReadingComprehensionExercise";
import { SentenceOrderingExercise } from "./SentenceOrderingExercise";
import { TranslationExercise } from "./TranslationExercise";

// Pure "collect one answer" switch over the scoreable exercise types — no
// submit button, no result display. Shared by any flow that gathers several
// answers before a single batch check (exam, placement test, lesson).
export function ExerciseItem({
  exercise,
  disabled = false,
  onAnswer,
}: {
  exercise: Exercise;
  disabled?: boolean;
  onAnswer: (answer: SubmittedAnswer) => void;
}) {
  switch (exercise.exercise_type) {
    case "multiple_choice":
      return (
        <MultipleChoiceExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(optionId) => onAnswer({ option_id: optionId })}
        />
      );
    case "fill_blank":
      return (
        <FillBlankExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(blanks) => onAnswer({ blanks })}
        />
      );
    case "sentence_ordering":
      return (
        <SentenceOrderingExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(order) => onAnswer({ order })}
        />
      );
    case "reading_comprehension":
      return (
        <ReadingComprehensionExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(answers) => onAnswer({ answers })}
        />
      );
    case "listening_comprehension":
      return (
        <ListeningComprehensionExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(answers) => onAnswer({ answers })}
        />
      );
    case "translation":
      return (
        <TranslationExercise
          prompt={exercise.prompt}
          disabled={disabled}
          onChange={(text) => onAnswer({ text })}
        />
      );
  }
}

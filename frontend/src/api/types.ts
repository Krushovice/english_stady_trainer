// Mirrors app/schemas/*.py — kept hand-in-sync with the backend response
// shapes rather than generated, since the API surface is still small.

export type CEFRLevel = "A1" | "A2" | "B1" | "B2";

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Level {
  id: string;
  code: CEFRLevel;
  order_index: number;
}

export interface Module {
  id: string;
  slug: string;
  title: string;
  order_index: number;
}

export interface LessonSummary {
  id: string;
  slug: string;
  title: string;
  order_index: number;
}

export type BlockType =
  | "learning_goals"
  | "context"
  | "vocabulary"
  | "grammar"
  | "examples"
  | "exercises"
  | "reading"
  | "listening"
  | "speaking"
  | "homework"
  | "review";

export interface LessonBlock {
  id: string;
  block_type: BlockType;
  order_index: number;
  content: Record<string, unknown>;
}

export interface Vocabulary {
  id: string;
  headword: string;
  translation: string;
  example_sentence: string;
  audio_url: string | null;
}

export interface GrammarTopic {
  id: string;
  slug: string;
  title: string;
  description: string;
}

export interface LessonDetail {
  id: string;
  slug: string;
  title: string;
  order_index: number;
  blocks: LessonBlock[];
  vocabulary: Vocabulary[];
  grammar_topics: GrammarTopic[];
}

export type Skill = "grammar" | "vocabulary" | "reading" | "listening" | "writing" | "speaking";

// --- Exercises: only the four types the backend can score (SupportedExerciseType) ---

export interface MultipleChoiceOption {
  id: string;
  text: string;
}

export interface MultipleChoicePrompt {
  question: string;
  options: MultipleChoiceOption[];
}

export interface FillBlankPrompt {
  text: string;
}

export interface SentenceOrderingPrompt {
  words: string[];
}

export interface ReadingComprehensionQuestion {
  id: string;
  text: string;
  options: MultipleChoiceOption[];
}

export interface ReadingComprehensionPrompt {
  passage: string;
  questions: ReadingComprehensionQuestion[];
}

interface ExerciseBase {
  id: string;
  slug: string;
  skill: Skill;
  difficulty: CEFRLevel;
}

export type Exercise =
  | (ExerciseBase & { exercise_type: "multiple_choice"; prompt: MultipleChoicePrompt })
  | (ExerciseBase & { exercise_type: "fill_blank"; prompt: FillBlankPrompt })
  | (ExerciseBase & { exercise_type: "sentence_ordering"; prompt: SentenceOrderingPrompt })
  | (ExerciseBase & {
      exercise_type: "reading_comprehension";
      prompt: ReadingComprehensionPrompt;
    });

export type SubmittedAnswer =
  | { option_id: string }
  | { blanks: string[] }
  | { order: string[] }
  | { answers: Record<string, string> };

export interface AttemptResult {
  id: string;
  is_correct: boolean;
  score: number;
  explanation: string;
  answer_key: Record<string, unknown>;
  attempted_at: string;
}

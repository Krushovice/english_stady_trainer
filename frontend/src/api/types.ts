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
  unlocked: boolean;
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
  | "mini_test"
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

export interface SkillProgress {
  skill: Skill;
  attempts_count: number;
  correct_count: number;
  accuracy: number;
}

export interface Title {
  title: string;
  cefr_grade: CEFRLevel | null;
  days_practiced: number;
  mistakes_mastered: number;
  mistakes_total: number;
  review_count: number;
}

// --- Placement test ---

export interface SkillLevelResult {
  skill: Skill;
  level: CEFRLevel | null;
  correct: number | null;
  total: number | null;
}

export interface RecommendedModule {
  id: string;
  slug: string;
  title: string;
  level_code: CEFRLevel;
}

export interface PlacementResult {
  overall_level: CEFRLevel | null;
  skills: SkillLevelResult[];
  recommended_modules: RecommendedModule[];
  placement_completed_at: string | null;
}

// --- Review ---

export type ReviewItemType = "vocabulary" | "grammar_topic" | "exercise";

export interface ReviewItem {
  id: string;
  item_type: ReviewItemType;
  due_at: string;
  interval_days: number;
  review_count: number;
  vocabulary: Vocabulary | null;
  grammar_topic: GrammarTopic | null;
  exercise: Exercise | null;
}

// --- Mini-test (post-lesson reinforcement of the previous topic) ---

export interface MiniTest {
  previous_lesson_title: string | null;
  exercises: Exercise[];
}

// --- Level exit exam ---

export interface ExamStatus {
  level: CEFRLevel;
  exam_available: boolean;
  passed: boolean;
  attempts_used_in_window: number;
  attempts_per_window: number;
  cooldown_until: string | null;
  in_progress_attempt_id: string | null;
  in_progress_expires_at: string | null;
}

export interface ExamAttempt {
  attempt_id: string;
  expires_at: string;
  exercises: Exercise[];
}

export interface ExamResult {
  attempt_id: string;
  score: number;
  passed: boolean;
  correct_count: number;
  total_count: number;
}

// --- AI feedback (shared by Homework and Speaking) ---

export interface WritingFeedback {
  good: string;
  grammar: string;
  vocabulary: string;
  natural_version: string;
  try_again: string;
}

// --- Homework ---

export interface HomeworkTask {
  id: string;
  instruction: string;
}

export interface HomeworkAttempt {
  id: string;
  task_id: string;
  submitted_text: string;
  feedback: WritingFeedback;
  submitted_at: string;
}

export interface Homework {
  id: string;
  lesson_title: string;
  tasks: HomeworkTask[];
  attempts: HomeworkAttempt[];
  generated_at: string;
}

// --- Speaking ---

export interface SpeakingAttempt {
  id: string;
  lesson_title: string;
  prompt: string;
  transcript: string | null;
  feedback: WritingFeedback | null;
  generated_at: string;
  submitted_at: string | null;
}

// --- AI Conversation ---

export type ConversationRole = "user" | "assistant";

export interface ConversationMessage {
  id: string;
  role: ConversationRole;
  content: string;
  created_at: string;
}

export interface ConversationAnalysis {
  recurring_mistakes: string;
  useful_vocabulary: string;
  natural_alternatives: string;
  grammar_topics_to_review: string;
  recommended_practice: string;
}

export interface ConversationSession {
  id: string;
  topic: string | null;
  started_at: string;
  ended_at: string | null;
  messages: ConversationMessage[];
  analysis: ConversationAnalysis | null;
}

import type { WritingFeedback } from "../api/types";

export function WritingFeedbackCard({ feedback }: { feedback: WritingFeedback }) {
  return (
    <div className="feedback-card">
      <div className="feedback-section feedback-good">
        <h4>Хорошо</h4>
        <p>{feedback.good}</p>
      </div>
      <div className="feedback-section">
        <h4>Грамматика</h4>
        <p>{feedback.grammar}</p>
      </div>
      <div className="feedback-section">
        <h4>Лексика</h4>
        <p>{feedback.vocabulary}</p>
      </div>
      <div className="feedback-section">
        <h4>Как сказать правильно</h4>
        <p>{feedback.natural_version}</p>
      </div>
      <div className="feedback-section feedback-try-again">
        <h4>Попробуйте снова</h4>
        <p>{feedback.try_again}</p>
      </div>
    </div>
  );
}

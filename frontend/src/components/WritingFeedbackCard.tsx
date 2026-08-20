import type { WritingFeedback } from "../api/types";

export function WritingFeedbackCard({ feedback }: { feedback: WritingFeedback }) {
  return (
    <div className="feedback-card">
      <div className="feedback-section feedback-good">
        <h4>Good</h4>
        <p>{feedback.good}</p>
      </div>
      <div className="feedback-section">
        <h4>Grammar</h4>
        <p>{feedback.grammar}</p>
      </div>
      <div className="feedback-section">
        <h4>Vocabulary</h4>
        <p>{feedback.vocabulary}</p>
      </div>
      <div className="feedback-section">
        <h4>Natural version</h4>
        <p>{feedback.natural_version}</p>
      </div>
      <div className="feedback-section feedback-try-again">
        <h4>Try again</h4>
        <p>{feedback.try_again}</p>
      </div>
    </div>
  );
}

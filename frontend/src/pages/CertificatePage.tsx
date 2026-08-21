import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCourseExamStatus } from "../api/courseExam";
import { getProgress } from "../api/exercises";
import type { Skill } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
};

export function CertificatePage() {
  const { user } = useAuth();
  const status = useQuery({ queryKey: ["course-exam-status"], queryFn: getCourseExamStatus });
  const progress = useQuery({ queryKey: ["progress"], queryFn: getProgress });

  if (status.isLoading) return <p className="status">Loading...</p>;
  if (status.error) return <p className="status status-error">Couldn't load certificate status.</p>;

  const data = status.data!;

  if (!data.certificate_available) {
    return (
      <div className="page">
        <h1>Certificate</h1>
        <p className="status">
          Not earned yet — pass the course-wide final exam to unlock your certificate.
        </p>
        <Link to="/course-exam" className="btn-primary">
          Go to the final exam
        </Link>
      </div>
    );
  }

  const earnedDate = data.earned_at ? new Date(data.earned_at).toLocaleDateString() : "";

  return (
    <div className="page">
      <h1>Certificate</h1>
      <div className="certificate-print">
        <p className="certificate-heading">Certificate of Completion</p>
        <p className="certificate-name">{user?.email}</p>
        <p className="certificate-detail">has completed the full A1–B2 English course</p>
        <p className="certificate-detail">Level reached: B2</p>
        <p className="certificate-detail">Earned on {earnedDate}</p>
        {progress.data && (
          <table className="certificate-table">
            <thead>
              <tr>
                <th>Skill</th>
                <th>Attempts</th>
                <th>Correct</th>
                <th>Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {progress.data.map((row) => (
                <tr key={row.skill}>
                  <td>{SKILL_LABELS[row.skill]}</td>
                  <td>{row.attempts_count}</td>
                  <td>{row.correct_count}</td>
                  <td>{Math.round(row.accuracy * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <p className="status">Press Ctrl+P (or Cmd+P) to print or save as PDF.</p>
    </div>
  );
}

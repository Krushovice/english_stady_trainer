import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDailyQuiz, getProgress } from "../api/exercises";
import { listMistakes } from "../api/mistakes";
import { listDueReviews } from "../api/review";

export function DashboardPage() {
  const reviews = useQuery({ queryKey: ["review-due"], queryFn: listDueReviews });
  const mistakes = useQuery({ queryKey: ["mistakes"], queryFn: () => listMistakes() });
  const progress = useQuery({ queryKey: ["progress"], queryFn: getProgress });
  const dailyQuiz = useQuery({ queryKey: ["daily-quiz"], queryFn: getDailyQuiz });

  const isLoading =
    reviews.isLoading || mistakes.isLoading || progress.isLoading || dailyQuiz.isLoading;
  const hasError = reviews.error || mistakes.error || progress.error || dailyQuiz.error;

  if (isLoading) return <p className="status">Loading dashboard...</p>;
  if (hasError) return <p className="status status-error">Couldn't load your dashboard.</p>;

  const dueCount = reviews.data!.length;
  const weakTopics = mistakes.data!.filter(
    (m) => m.status === "new" || m.status === "repeated",
  );
  const improvedTopics = mistakes.data!.filter(
    (m) => m.status === "improving" || m.status === "mastered",
  );
  const hasQuiz = dailyQuiz.data!.length > 0;

  let doNow: { text: string; to: string; label: string };
  if (dueCount > 0) {
    doNow = {
      text: `You have ${dueCount} review${dueCount === 1 ? "" : "s"} due.`,
      to: "/review",
      label: "Go to review",
    };
  } else if (weakTopics.length > 0) {
    doNow = {
      text: `You have ${weakTopics.length} weak topic${weakTopics.length === 1 ? "" : "s"} to practice.`,
      to: "/daily-quiz",
      label: "Practice now",
    };
  } else if (hasQuiz) {
    doNow = { text: "Try today's daily quiz.", to: "/daily-quiz", label: "Start quiz" };
  } else {
    doNow = { text: "Start a lesson to begin practicing.", to: "/levels", label: "Go to lessons" };
  }

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <div className="dashboard-card dashboard-do-now">
        <h2>Do now</h2>
        <p>{doNow.text}</p>
        <Link to={doNow.to} className="btn-primary">
          {doNow.label}
        </Link>
      </div>

      <div className="card-grid">
        <div className="dashboard-card">
          <h2>Weak at</h2>
          {weakTopics.length === 0 ? (
            <p className="status">No weak topics right now.</p>
          ) : (
            <ul>
              {weakTopics.slice(0, 5).map((m) => (
                <li key={m.id}>{m.grammar_topic.title}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Improved</h2>
          {improvedTopics.length === 0 ? (
            <p className="status">Nothing improving yet.</p>
          ) : (
            <ul>
              {improvedTopics.slice(0, 5).map((m) => (
                <li key={m.id}>{m.grammar_topic.title}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Due for review</h2>
          {dueCount === 0 ? (
            <p className="status">Nothing due right now.</p>
          ) : (
            <p>
              {dueCount} item{dueCount === 1 ? "" : "s"} waiting.{" "}
              <Link to="/review">Go to review →</Link>
            </p>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Progress</h2>
          {progress.data!.length === 0 ? (
            <p className="status">No attempts yet.</p>
          ) : (
            <p>
              Tracked across {progress.data!.length} skill{progress.data!.length === 1 ? "" : "s"}.{" "}
              <Link to="/progress">See full progress →</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

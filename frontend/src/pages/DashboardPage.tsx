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

  if (isLoading) return <p className="status">Загрузка панели...</p>;
  if (hasError) return <p className="status status-error">Не удалось загрузить панель.</p>;

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
      text: `У вас ${dueCount} элемент${dueCount === 1 ? "" : "ов"} на повторение.`,
      to: "/review",
      label: "К повторению",
    };
  } else if (weakTopics.length > 0) {
    doNow = {
      text: `У вас ${weakTopics.length} слаб${weakTopics.length === 1 ? "ая тема" : "ых темы"} для практики.`,
      to: "/daily-quiz",
      label: "Практиковаться",
    };
  } else if (hasQuiz) {
    doNow = { text: "Пройдите сегодняшний ежедневный тест.", to: "/daily-quiz", label: "Начать тест" };
  } else {
    doNow = { text: "Начните урок, чтобы приступить к практике.", to: "/levels", label: "К урокам" };
  }

  return (
    <div className="page">
      <h1>Панель</h1>

      <div className="dashboard-card dashboard-do-now">
        <h2>Сделать сейчас</h2>
        <p>{doNow.text}</p>
        <Link to={doNow.to} className="btn-primary">
          {doNow.label}
        </Link>
      </div>

      <div className="card-grid">
        <div className="dashboard-card">
          <h2>Слабые места</h2>
          {weakTopics.length === 0 ? (
            <p className="status">Слабых тем сейчас нет.</p>
          ) : (
            <ul>
              {weakTopics.slice(0, 5).map((m) => (
                <li key={m.id}>{m.grammar_topic.title}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Улучшения</h2>
          {improvedTopics.length === 0 ? (
            <p className="status">Пока ничего не улучшилось.</p>
          ) : (
            <ul>
              {improvedTopics.slice(0, 5).map((m) => (
                <li key={m.id}>{m.grammar_topic.title}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="dashboard-card">
          <h2>На повторении</h2>
          {dueCount === 0 ? (
            <p className="status">Сейчас ничего не ждёт повторения.</p>
          ) : (
            <p>
              Ждут: {dueCount}.{" "}
              <Link to="/review">К повторению →</Link>
            </p>
          )}
        </div>

        <div className="dashboard-card">
          <h2>Прогресс</h2>
          {progress.data!.length === 0 ? (
            <p className="status">Попыток ещё не было.</p>
          ) : (
            <p>
              Учитывается по {progress.data!.length} навык{progress.data!.length === 1 ? "у" : "ам"}.{" "}
              <Link to="/progress">Весь прогресс →</Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

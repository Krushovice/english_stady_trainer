import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDailyQuiz, getProgress } from "../api/exercises";
import { listMistakes } from "../api/mistakes";
import { listDueReviews } from "../api/review";
import { getMyTitle } from "../api/titles";
import type { Skill } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { AlertIcon, FlameIcon, RotateIcon, TargetIcon } from "../components/icons";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Грамматика",
  vocabulary: "Лексика",
  reading: "Чтение",
  listening: "Аудирование",
  writing: "Письмо",
  speaking: "Говорение",
};

const SKILL_ORDER: Skill[] = [
  "grammar",
  "vocabulary",
  "reading",
  "listening",
  "writing",
  "speaking",
];

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 5) return "Доброй ночи";
  if (hour < 12) return "Доброе утро";
  if (hour < 18) return "Добрый день";
  return "Добрый вечер";
}

export function DashboardPage() {
  const { user } = useAuth();
  const reviews = useQuery({ queryKey: ["review-due"], queryFn: listDueReviews });
  const mistakes = useQuery({ queryKey: ["mistakes"], queryFn: () => listMistakes() });
  const progress = useQuery({ queryKey: ["progress"], queryFn: getProgress });
  const dailyQuiz = useQuery({ queryKey: ["daily-quiz"], queryFn: getDailyQuiz });
  const title = useQuery({ queryKey: ["title"], queryFn: getMyTitle });

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
  const quizCount = dailyQuiz.data!.length;
  // Backfilled pre-existing accounts (registered before the `name` field
  // existed) may still have an empty name — fall back to the email's local
  // part rather than showing a bare comma.
  const displayName = user?.name || user?.email?.split("@")[0] || "";

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
  } else if (quizCount > 0) {
    doNow = { text: "Пройдите сегодняшний ежедневный тест.", to: "/daily-quiz", label: "Начать тест" };
  } else {
    doNow = { text: "Начните урок, чтобы приступить к практике.", to: "/levels", label: "К урокам" };
  }

  return (
    <div className="page">
      <div className="dashboard-hero">
        <div>
          <h1 className="dashboard-greeting">
            {greeting()}
            {displayName ? `, ${displayName}` : ""}.
          </h1>
          <p className="dashboard-greeting-sub">Ваш английский сегодня</p>
        </div>
        {title.data && (
          <div className="dashboard-title-chip">
            <span className="title-value">
              {title.data.title}
              {title.data.cefr_grade ? ` · ${title.data.cefr_grade}` : ""}
            </span>
            <span className="title-meta">Дней практики: {title.data.days_practiced}</span>
          </div>
        )}
      </div>

      <div className="dashboard-do-now">
        <div>
          <span className="dashboard-do-now-label">Сделать сейчас</span>
          <p className="dashboard-do-now-text">{doNow.text}</p>
        </div>
        <Link to={doNow.to} className="btn-primary">
          {doNow.label}
        </Link>
      </div>

      <div className="stat-strip">
        <Link to="/review" className="stat-tile">
          <RotateIcon className="stat-tile-icon" width={20} height={20} />
          <span className="stat-tile-value">{dueCount}</span>
          <span className="stat-tile-label">На повторении</span>
        </Link>
        <Link to="/daily-quiz" className="stat-tile">
          <TargetIcon className="stat-tile-icon" width={20} height={20} />
          <span className="stat-tile-value">{quizCount}</span>
          <span className="stat-tile-label">Ежедневный тест</span>
        </Link>
        <div className="stat-tile">
          <AlertIcon className="stat-tile-icon" width={20} height={20} />
          <span className="stat-tile-value">{weakTopics.length}</span>
          <span className="stat-tile-label">Слабых тем</span>
        </div>
        <div className="stat-tile">
          <FlameIcon className="stat-tile-icon" width={20} height={20} />
          <span className="stat-tile-value">{improvedTopics.length}</span>
          <span className="stat-tile-label">Улучшений</span>
        </div>
      </div>

      <div className="dashboard-split">
        <div className="dashboard-split-col">
          <h2>Слабые места</h2>
          {weakTopics.length === 0 ? (
            <p className="status">Слабых тем сейчас нет.</p>
          ) : (
            <div className="topic-list">
              {weakTopics.slice(0, 5).map((m) => (
                <div key={m.id} className="topic-row">
                  <span>{m.grammar_topic.title}</span>
                  <span className="badge badge-muted">{Math.round(m.error_rate * 100)}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="dashboard-split-col">
          <h2>Улучшения</h2>
          {improvedTopics.length === 0 ? (
            <p className="status">Пока ничего не улучшилось.</p>
          ) : (
            <div className="topic-list">
              {improvedTopics.slice(0, 5).map((m) => (
                <div key={m.id} className="topic-row">
                  <span>{m.grammar_topic.title}</span>
                  <span className="badge">{m.status === "mastered" ? "Освоено" : "Улучшается"}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {progress.data!.length > 0 && (
        <div className="skill-snapshot">
          <div className="skill-snapshot-header">
            <h2>Прогресс по навыкам</h2>
            <Link to="/progress" className="link-button">
              Весь прогресс →
            </Link>
          </div>
          <div className="skill-bar-grid">
            {SKILL_ORDER.map((skill) => {
              const row = progress.data!.find((r) => r.skill === skill);
              const pct = row ? Math.round(row.accuracy * 100) : 0;
              return (
                <div key={skill} className="skill-bar-row">
                  <div className="skill-bar-top">
                    <strong>{SKILL_LABELS[skill]}</strong>
                    <span>{row ? `${pct}%` : "—"}</span>
                  </div>
                  <div className="skill-bar-track">
                    <div className="skill-bar-fill" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

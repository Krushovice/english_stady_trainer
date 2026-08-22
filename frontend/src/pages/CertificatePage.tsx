import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCourseExamStatus } from "../api/courseExam";
import { getProgress } from "../api/exercises";
import type { Skill } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Грамматика",
  vocabulary: "Лексика",
  reading: "Чтение",
  listening: "Аудирование",
  writing: "Письмо",
  speaking: "Говорение",
};

export function CertificatePage() {
  const { user } = useAuth();
  const status = useQuery({ queryKey: ["course-exam-status"], queryFn: getCourseExamStatus });
  const progress = useQuery({ queryKey: ["progress"], queryFn: getProgress });

  if (status.isLoading) return <p className="status">Загрузка...</p>;
  if (status.error) return <p className="status status-error">Не удалось загрузить статус сертификата.</p>;

  const data = status.data!;

  if (!data.certificate_available) {
    return (
      <div className="page">
        <h1>Сертификат</h1>
        <p className="status">
          Пока не получен — сдайте финальный экзамен по всему курсу, чтобы открыть сертификат.
        </p>
        <Link to="/course-exam" className="btn-primary">
          К финальному экзамену
        </Link>
      </div>
    );
  }

  const earnedDate = data.earned_at ? new Date(data.earned_at).toLocaleDateString() : "";

  return (
    <div className="page">
      <h1>Сертификат</h1>
      <div className="certificate-print">
        <p className="certificate-heading">Сертификат о прохождении курса</p>
        <p className="certificate-name">{user?.email}</p>
        <p className="certificate-detail">завершил(а) полный курс английского языка A1–B2</p>
        <p className="certificate-detail">Достигнутый уровень: B2</p>
        <p className="certificate-detail">Дата получения: {earnedDate}</p>
        {progress.data && (
          <table className="certificate-table">
            <thead>
              <tr>
                <th>Навык</th>
                <th>Попыток</th>
                <th>Верно</th>
                <th>Точность</th>
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
      <p className="status">Нажмите Ctrl+P (или Cmd+P), чтобы распечатать или сохранить в PDF.</p>
    </div>
  );
}

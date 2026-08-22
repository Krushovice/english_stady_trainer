import { useQuery } from "@tanstack/react-query";
import { getProgress } from "../api/exercises";
import { getMyTitle } from "../api/titles";
import type { Skill } from "../api/types";

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

export function ProgressPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["progress"],
    queryFn: getProgress,
  });
  const title = useQuery({
    queryKey: ["title"],
    queryFn: getMyTitle,
  });

  if (isLoading) return <p className="status">Загрузка прогресса...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить прогресс.</p>;

  const bySkill = new Map(data!.map((row) => [row.skill, row]));

  return (
    <div className="page">
      <h1>Прогресс</h1>
      {title.data && (
        <div className="title-card">
          <h2>
            {title.data.title}
            {title.data.cefr_grade ? ` · ${title.data.cefr_grade}` : ""}
          </h2>
          <p className="status">
            Дней с практикой: {title.data.days_practiced} ·{" "}
            Ошибок исправлено: {title.data.mistakes_mastered}/{title.data.mistakes_total} ·{" "}
            Повторений завершено: {title.data.review_count}
          </p>
        </div>
      )}
      <p className="status">Учитывается отдельно по каждому навыку — без единой общей оценки.</p>
      <div className="progress-grid">
        {SKILL_ORDER.map((skill) => {
          const row = bySkill.get(skill);
          const attempts = row?.attempts_count ?? 0;
          const accuracyPct = row ? Math.round(row.accuracy * 100) : 0;
          return (
            <div key={skill} className="progress-card">
              <div className="progress-card-header">
                <span className="progress-skill">{SKILL_LABELS[skill]}</span>
                <span className="progress-count">
                  {attempts === 0 ? "попыток ещё не было" : `попыток: ${attempts}`}
                </span>
              </div>
              {attempts > 0 && (
                <>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${accuracyPct}%` }} />
                  </div>
                  <span className="progress-accuracy">
                    Верно: {row!.correct_count}/{attempts} ({accuracyPct}%)
                  </span>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

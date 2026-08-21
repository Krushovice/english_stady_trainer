import { useQuery } from "@tanstack/react-query";
import { getProgress } from "../api/exercises";
import { getMyTitle } from "../api/titles";
import type { Skill } from "../api/types";

const SKILL_LABELS: Record<Skill, string> = {
  grammar: "Grammar",
  vocabulary: "Vocabulary",
  reading: "Reading",
  listening: "Listening",
  writing: "Writing",
  speaking: "Speaking",
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

  if (isLoading) return <p className="status">Loading progress...</p>;
  if (error) return <p className="status status-error">Couldn't load progress.</p>;

  const bySkill = new Map(data!.map((row) => [row.skill, row]));

  return (
    <div className="page">
      <h1>Progress</h1>
      {title.data && (
        <div className="title-card">
          <h2>
            {title.data.title}
            {title.data.cefr_grade ? ` · ${title.data.cefr_grade}` : ""}
          </h2>
          <p className="status">
            {title.data.days_practiced} day{title.data.days_practiced === 1 ? "" : "s"} practiced ·{" "}
            {title.data.mistakes_mastered}/{title.data.mistakes_total} mistakes mastered ·{" "}
            {title.data.review_count} review{title.data.review_count === 1 ? "" : "s"} completed
          </p>
        </div>
      )}
      <p className="status">Tracked separately per skill — not one overall score.</p>
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
                  {attempts === 0
                    ? "no attempts yet"
                    : `${attempts} attempt${attempts === 1 ? "" : "s"}`}
                </span>
              </div>
              {attempts > 0 && (
                <>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${accuracyPct}%` }} />
                  </div>
                  <span className="progress-accuracy">
                    {row!.correct_count}/{attempts} correct ({accuracyPct}%)
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

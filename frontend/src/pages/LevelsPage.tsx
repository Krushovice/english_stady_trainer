import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listLevels } from "../api/course";
import { getPlacementResult } from "../api/placement";
import type { CEFRLevel } from "../api/types";

// Mirrors app/services/placement_scoring.py's LEVEL_ORDER — used only to
// name which level's exam unlocks a locked one, not to drive any scoring.
const LEVEL_ORDER: CEFRLevel[] = ["A1", "A2", "B1", "B2"];

function precedingLevel(level: CEFRLevel): CEFRLevel | null {
  const index = LEVEL_ORDER.indexOf(level);
  return index > 0 ? LEVEL_ORDER[index - 1] : null;
}

// Display-only placeholders — deliberately not part of CEFRLevel (CLAUDE.md
// excludes C1/C2 from MVP scope; these never become real, clickable levels).
const COMING_SOON_LEVELS = ["C1", "C2"] as const;

export function LevelsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["levels"],
    queryFn: listLevels,
  });
  const placement = useQuery({
    queryKey: ["placement-result"],
    queryFn: getPlacementResult,
  });

  if (isLoading) return <p className="status">Загрузка уровней...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить уровни.</p>;

  return (
    <div className="page">
      <h1>Уровни</h1>
      {placement.data && !placement.data.placement_completed_at && (
        <Link to="/placement-test" className="banner">
          Пройдите тест на уровень, чтобы определить свой уровень →
        </Link>
      )}
      <div className="card-grid">
        {data!.map((level) => {
          if (level.unlocked) {
            return (
              <Link key={level.id} to={`/levels/${level.code}/modules`} className="card">
                <span className="card-title">{level.code}</span>
              </Link>
            );
          }
          const gate = precedingLevel(level.code);
          return (
            <Link
              key={level.id}
              to={gate ? `/levels/${gate}/exam` : "/levels"}
              className="card card-locked"
            >
              <span className="card-title">🔒 {level.code}</span>
              <span className="status">Сдайте экзамен уровня {gate}, чтобы открыть</span>
            </Link>
          );
        })}
        {COMING_SOON_LEVELS.map((code) => (
          <div key={code} className="card card-locked">
            <span className="card-title">🔒 {code}</span>
            <span className="status">Скоро</span>
          </div>
        ))}
      </div>
    </div>
  );
}

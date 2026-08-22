import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listLevels } from "../api/course";
import { getPlacementResult } from "../api/placement";
import type { CEFRLevel } from "../api/types";
import { ChevronRightIcon, LockIcon } from "../components/icons";

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
      <span className="page-eyebrow">Курс</span>
      <h1>Уровни</h1>
      {placement.data && !placement.data.placement_completed_at && (
        <Link to="/placement-test" className="banner">
          Пройдите тест на уровень, чтобы определить свой уровень →
        </Link>
      )}
      <ul className="entry-list">
        {data!.map((level, i) => {
          if (level.unlocked) {
            return (
              <li key={level.id} className="entry-list-item">
                <Link to={`/levels/${level.code}/modules`} className="entry-row">
                  <span className="entry-index">{String(i + 1).padStart(2, "0")}</span>
                  <span className="entry-body">
                    <span className="entry-title">{level.code}</span>
                  </span>
                  <span className="entry-status">
                    <ChevronRightIcon className="chevron" />
                  </span>
                </Link>
              </li>
            );
          }
          const gate = precedingLevel(level.code);
          return (
            <li key={level.id} className="entry-list-item">
              <Link
                to={gate ? `/levels/${gate}/exam` : "/levels"}
                className="entry-row is-locked is-locked-linkable"
              >
                <span className="entry-index">{String(i + 1).padStart(2, "0")}</span>
                <span className="entry-body">
                  <span className="entry-title">{level.code}</span>
                  <span className="entry-meta">
                    {gate
                      ? `Сдайте экзамен уровня ${gate}, чтобы открыть`
                      : "Сдайте экзамен предыдущего уровня, чтобы открыть"}
                  </span>
                </span>
                <span className="entry-status">
                  <LockIcon width={16} height={16} />
                </span>
              </Link>
            </li>
          );
        })}
        {COMING_SOON_LEVELS.map((code, i) => (
          <li key={code} className="entry-list-item">
            <div className="entry-row is-locked">
              <span className="entry-index">{String(data!.length + i + 1).padStart(2, "0")}</span>
              <span className="entry-body">
                <span className="entry-title">{code}</span>
                <span className="entry-meta">Скоро</span>
              </span>
              <span className="entry-status">
                <LockIcon width={16} height={16} />
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

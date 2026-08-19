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

export function LevelsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["levels"],
    queryFn: listLevels,
  });
  const placement = useQuery({
    queryKey: ["placement-result"],
    queryFn: getPlacementResult,
  });

  if (isLoading) return <p className="status">Loading levels...</p>;
  if (error) return <p className="status status-error">Couldn't load levels.</p>;

  return (
    <div className="page">
      <h1>Levels</h1>
      {placement.data && !placement.data.placement_completed_at && (
        <Link to="/placement-test" className="banner">
          Take the placement test to find your level →
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
              <span className="status">Pass the {gate} exam to unlock</span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

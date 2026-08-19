import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { listModules } from "../api/course";
import type { CEFRLevel } from "../api/types";

const LEVEL_ORDER: CEFRLevel[] = ["A1", "A2", "B1", "B2"];

function precedingLevel(level: CEFRLevel): CEFRLevel | null {
  const index = LEVEL_ORDER.indexOf(level);
  return index > 0 ? LEVEL_ORDER[index - 1] : null;
}

export function ModulesPage() {
  const { levelCode } = useParams<{ levelCode: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["modules", levelCode],
    queryFn: () => listModules(levelCode as CEFRLevel),
    enabled: !!levelCode,
    retry: false,
  });

  if (isLoading) return <p className="status">Loading modules...</p>;
  if (error instanceof ApiError && error.status === 403) {
    const gate = precedingLevel(levelCode as CEFRLevel);
    return (
      <div className="page">
        <Link to="/levels" className="back-link">
          &larr; Levels
        </Link>
        <h1>{levelCode} modules</h1>
        <p className="status status-error">
          🔒 This level is locked.{" "}
          {gate ? (
            <Link to={`/levels/${gate}/exam`}>Pass the {gate} exam to unlock it</Link>
          ) : (
            "Pass the previous level's exam to unlock it."
          )}
        </p>
      </div>
    );
  }
  if (error) return <p className="status status-error">Couldn't load modules.</p>;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Levels
      </Link>
      <h1>{levelCode} modules</h1>
      {data!.length === 0 ? (
        <p className="status">No modules yet for this level.</p>
      ) : (
        <div className="card-grid">
          {data!.map((module) => (
            <Link key={module.id} to={`/modules/${module.slug}/lessons`} className="card">
              <span className="card-title">{module.title}</span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

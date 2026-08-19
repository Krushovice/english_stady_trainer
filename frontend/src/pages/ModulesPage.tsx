import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { listModules } from "../api/course";
import type { CEFRLevel } from "../api/types";

export function ModulesPage() {
  const { levelCode } = useParams<{ levelCode: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["modules", levelCode],
    queryFn: () => listModules(levelCode as CEFRLevel),
    enabled: !!levelCode,
  });

  if (isLoading) return <p className="status">Loading modules...</p>;
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

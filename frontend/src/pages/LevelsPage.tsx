import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listLevels } from "../api/course";
import { getPlacementResult } from "../api/placement";

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
        {data!.map((level) => (
          <Link key={level.id} to={`/levels/${level.code}/modules`} className="card">
            <span className="card-title">{level.code}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

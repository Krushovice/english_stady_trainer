import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { listLessons } from "../api/course";

export function LessonsPage() {
  const { moduleSlug } = useParams<{ moduleSlug: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["lessons", moduleSlug],
    queryFn: () => listLessons(moduleSlug!),
    enabled: !!moduleSlug,
  });

  if (isLoading) return <p className="status">Loading lessons...</p>;
  if (error) return <p className="status status-error">Couldn't load lessons.</p>;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Levels
      </Link>
      <h1>Lessons</h1>
      <div className="card-grid">
        {data!.map((lesson) => (
          <Link key={lesson.id} to={`/lessons/${lesson.slug}`} className="card">
            <span className="card-title">{lesson.title}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}

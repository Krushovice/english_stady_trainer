import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { listLessons } from "../api/course";
import { ChevronRightIcon } from "../components/icons";

export function LessonsPage() {
  const { moduleSlug } = useParams<{ moduleSlug: string }>();
  const { data, isLoading, error } = useQuery({
    queryKey: ["lessons", moduleSlug],
    queryFn: () => listLessons(moduleSlug!),
    enabled: !!moduleSlug,
  });

  if (isLoading) return <p className="status">Загрузка уроков...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить уроки.</p>;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Уровни
      </Link>
      <h1>Уроки</h1>
      <ul className="entry-list">
        {data!.map((lesson, i) => (
          <li key={lesson.id} className="entry-list-item">
            <Link to={`/lessons/${lesson.slug}`} className="entry-row">
              <span className="entry-index">{String(i + 1).padStart(2, "0")}</span>
              <span className="entry-body">
                <span className="entry-title">{lesson.title}</span>
              </span>
              <span className="entry-status">
                <ChevronRightIcon className="chevron" />
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

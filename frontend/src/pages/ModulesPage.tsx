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

  if (isLoading) return <p className="status">Загрузка модулей...</p>;
  if (error instanceof ApiError && error.status === 403) {
    const gate = precedingLevel(levelCode as CEFRLevel);
    return (
      <div className="page">
        <Link to="/levels" className="back-link">
          &larr; Уровни
        </Link>
        <h1>Модули уровня {levelCode}</h1>
        <p className="status status-error">
          🔒 Этот уровень заблокирован.{" "}
          {gate ? (
            <Link to={`/levels/${gate}/exam`}>Сдайте экзамен уровня {gate}, чтобы открыть его</Link>
          ) : (
            "Сдайте экзамен предыдущего уровня, чтобы открыть его."
          )}
        </p>
      </div>
    );
  }
  if (error) return <p className="status status-error">Не удалось загрузить модули.</p>;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Уровни
      </Link>
      <h1>Модули уровня {levelCode}</h1>
      {data!.length === 0 ? (
        <p className="status">Для этого уровня пока нет модулей.</p>
      ) : (
        <div className="card-grid">
          {data!.map((module, i) => {
            if (!module.unlocked) {
              const previousTitle = data![i - 1]?.title;
              return (
                <div key={module.id} className="card card-locked">
                  <span className="card-title">🔒 {module.title}</span>
                  <span className="status">
                    {previousTitle
                      ? `Пройдите «${previousTitle}» (70%+), чтобы открыть`
                      : "Заблокировано"}
                  </span>
                </div>
              );
            }
            return (
              <Link key={module.id} to={`/modules/${module.slug}/lessons`} className="card">
                <span className="card-title">
                  {module.passed ? "✅ " : ""}
                  {module.title}
                </span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

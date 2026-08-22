import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { listModules } from "../api/course";
import type { CEFRLevel } from "../api/types";
import { CheckIcon, ChevronRightIcon, LockIcon } from "../components/icons";

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
          Этот уровень заблокирован.{" "}
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
      <span className="page-eyebrow">Уровень {levelCode}</span>
      <h1>Модули</h1>
      {data!.length === 0 ? (
        <p className="status">Для этого уровня пока нет модулей.</p>
      ) : (
        <ul className="entry-list">
          {data!.map((module, i) => {
            if (!module.unlocked) {
              const previousTitle = data![i - 1]?.title;
              return (
                <li key={module.id} className="entry-list-item">
                  <div className="entry-row is-locked">
                    <span className="entry-index">{String(i + 1).padStart(2, "0")}</span>
                    <span className="entry-body">
                      <span className="entry-title">{module.title}</span>
                      <span className="entry-meta">
                        {previousTitle
                          ? `Пройдите «${previousTitle}» (70%+), чтобы открыть`
                          : "Заблокировано"}
                      </span>
                    </span>
                    <span className="entry-status">
                      <LockIcon width={16} height={16} />
                    </span>
                  </div>
                </li>
              );
            }
            return (
              <li key={module.id} className="entry-list-item">
                <Link to={`/modules/${module.slug}/lessons`} className="entry-row">
                  <span className="entry-index">{String(i + 1).padStart(2, "0")}</span>
                  <span className="entry-body">
                    <span className="entry-title">{module.title}</span>
                  </span>
                  <span className={"entry-status" + (module.passed ? " is-done" : "")}>
                    {module.passed ? (
                      <CheckIcon width={16} height={16} />
                    ) : (
                      <ChevronRightIcon className="chevron" />
                    )}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

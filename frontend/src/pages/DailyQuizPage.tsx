import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDailyQuiz } from "../api/exercises";
import { ExerciseCard } from "../components/exercises/ExerciseCard";

export function DailyQuizPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["daily-quiz"],
    queryFn: getDailyQuiz,
  });

  if (isLoading) return <p className="status">Загрузка сегодняшнего теста...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить ежедневный тест.</p>;

  return (
    <div className="page">
      <h1>Ежедневный тест</h1>
      <p className="status">
        Подборка из уже изученных уроков — новая каждый день.
      </p>
      {data!.length === 0 ? (
        <p className="status">
          Пока нечего тестировать — сначала выполните упражнения в{" "}
          <Link to="/levels">уроке</Link>.
        </p>
      ) : (
        data!.map((exercise) => <ExerciseCard key={exercise.id} exercise={exercise} />)
      )}
    </div>
  );
}

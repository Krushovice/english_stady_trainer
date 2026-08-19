import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getDailyQuiz } from "../api/exercises";
import { ExerciseCard } from "../components/exercises/ExerciseCard";

export function DailyQuizPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["daily-quiz"],
    queryFn: getDailyQuiz,
  });

  if (isLoading) return <p className="status">Loading today's quiz...</p>;
  if (error) return <p className="status status-error">Couldn't load the daily quiz.</p>;

  return (
    <div className="page">
      <h1>Daily quiz</h1>
      <p className="status">
        A mix pulled from lessons you've already studied — new pick every day.
      </p>
      {data!.length === 0 ? (
        <p className="status">
          Nothing to quiz yet — finish some exercises in a{" "}
          <Link to="/levels">lesson</Link> first.
        </p>
      ) : (
        data!.map((exercise) => <ExerciseCard key={exercise.id} exercise={exercise} />)
      )}
    </div>
  );
}

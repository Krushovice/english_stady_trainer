import { useQuery } from "@tanstack/react-query";
import { listDueReviews } from "../api/review";
import { ExerciseCard } from "../components/exercises/ExerciseCard";
import { ReviewFlashcard } from "../components/ReviewFlashcard";

export function ReviewPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["review-due"],
    queryFn: listDueReviews,
  });

  if (isLoading) return <p className="status">Загрузка повторения...</p>;
  if (error) return <p className="status status-error">Не удалось загрузить элементы повторения.</p>;

  return (
    <div className="page">
      <h1>Повторение</h1>
      <p className="status">
        Слова, грамматические конструкции и упражнения по расписанию интервального повторения —
        каждый элемент появляется здесь, когда реально пора его повторить, а не по фиксированной норме в день.
      </p>
      {data!.length === 0 ? (
        <p className="status">
          Сейчас повторять нечего. Элементы появляются здесь минимум через день после
          первой практики, раньше — если был неверный ответ.
        </p>
      ) : (
        data!.map((item) =>
          item.exercise ? (
            <ExerciseCard key={item.id} exercise={item.exercise} />
          ) : (
            <ReviewFlashcard key={item.id} item={item} />
          ),
        )
      )}
    </div>
  );
}

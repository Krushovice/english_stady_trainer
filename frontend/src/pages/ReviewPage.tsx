import { useQuery } from "@tanstack/react-query";
import { listDueReviews } from "../api/review";
import { ExerciseCard } from "../components/exercises/ExerciseCard";
import { ReviewFlashcard } from "../components/ReviewFlashcard";

export function ReviewPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["review-due"],
    queryFn: listDueReviews,
  });

  if (isLoading) return <p className="status">Loading review...</p>;
  if (error) return <p className="status status-error">Couldn't load review items.</p>;

  return (
    <div className="page">
      <h1>Review</h1>
      <p className="status">
        Words, grammar patterns, and exercises scheduled for spaced-repetition review —
        each item reappears here once it's actually due, not on a fixed daily amount.
      </p>
      {data!.length === 0 ? (
        <p className="status">
          Nothing due right now. Items show up here at least a day after you first
          practice them, sooner if you got them wrong.
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

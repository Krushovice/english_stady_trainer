import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getLesson } from "../api/course";
import { getMiniTest, listLessonExercises } from "../api/exercises";
import { ExerciseCard } from "../components/exercises/ExerciseCard";
import { LessonBlockView } from "../components/LessonBlockView";

export function LessonPage() {
  const { lessonSlug } = useParams<{ lessonSlug: string }>();

  const lessonQuery = useQuery({
    queryKey: ["lesson", lessonSlug],
    queryFn: () => getLesson(lessonSlug!),
    enabled: !!lessonSlug,
  });
  const exercisesQuery = useQuery({
    queryKey: ["lesson-exercises", lessonSlug],
    queryFn: () => listLessonExercises(lessonSlug!),
    enabled: !!lessonSlug,
  });
  const miniTestQuery = useQuery({
    queryKey: ["mini-test", lessonSlug],
    queryFn: () => getMiniTest(lessonSlug!),
    enabled: !!lessonSlug,
  });

  if (lessonQuery.isLoading) return <p className="status">Loading lesson...</p>;
  if (lessonQuery.error || !lessonQuery.data)
    return <p className="status status-error">Couldn't load this lesson.</p>;

  const lesson = lessonQuery.data;

  return (
    <div className="page">
      <Link to="/levels" className="back-link">
        &larr; Levels
      </Link>
      <h1>{lesson.title}</h1>

      {lesson.blocks
        .slice()
        .sort((a, b) => a.order_index - b.order_index)
        .map((block) => (
          <LessonBlockView key={block.id} block={block} />
        ))}

      {lesson.vocabulary.length > 0 && (
        <section className="lesson-block">
          <h2>Vocabulary</h2>
          <dl className="vocabulary-list">
            {lesson.vocabulary.map((word) => (
              <div key={word.id} className="vocabulary-item">
                <dt>{word.headword}</dt>
                <dd>{word.translation}</dd>
                <dd className="example">{word.example_sentence}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {lesson.grammar_topics.length > 0 && (
        <section className="lesson-block">
          <h2>Grammar</h2>
          {lesson.grammar_topics.map((topic) => (
            <div key={topic.id} className="grammar-topic">
              <h3>{topic.title}</h3>
              <p>{topic.description}</p>
            </div>
          ))}
        </section>
      )}

      <section className="lesson-block">
        <h2>Exercises</h2>
        {exercisesQuery.isLoading && <p className="status">Loading exercises...</p>}
        {exercisesQuery.error && (
          <p className="status status-error">Couldn't load exercises.</p>
        )}
        {exercisesQuery.data?.length === 0 && (
          <p className="status">No exercises for this lesson yet.</p>
        )}
        {exercisesQuery.data?.map((exercise) => (
          <ExerciseCard key={exercise.id} exercise={exercise} />
        ))}
      </section>

      {miniTestQuery.data && miniTestQuery.data.exercises.length > 0 && (
        <section className="lesson-block mini-test">
          <h2>🔁 Quick review: {miniTestQuery.data.previous_lesson_title}</h2>
          <p className="status">
            Five questions on the previous topic before you move on.
          </p>
          {miniTestQuery.data.exercises.map((exercise) => (
            <ExerciseCard key={exercise.id} exercise={exercise} />
          ))}
        </section>
      )}
    </div>
  );
}

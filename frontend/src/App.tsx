import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { useAuth } from "./auth/AuthContext";
import { Header } from "./components/layout/Header";
import { DailyQuizPage } from "./pages/DailyQuizPage";
import { LessonPage } from "./pages/LessonPage";
import { LessonsPage } from "./pages/LessonsPage";
import { LevelsPage } from "./pages/LevelsPage";
import { LoginPage } from "./pages/LoginPage";
import { ModulesPage } from "./pages/ModulesPage";
import { PlacementTestPage } from "./pages/PlacementTestPage";
import { ProgressPage } from "./pages/ProgressPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReviewPage } from "./pages/ReviewPage";

function App() {
  const { user, loading } = useAuth();

  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/levels"
            element={
              <ProtectedRoute>
                <LevelsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/levels/:levelCode/modules"
            element={
              <ProtectedRoute>
                <ModulesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/modules/:moduleSlug/lessons"
            element={
              <ProtectedRoute>
                <LessonsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lessons/:lessonSlug"
            element={
              <ProtectedRoute>
                <LessonPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/daily-quiz"
            element={
              <ProtectedRoute>
                <DailyQuizPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review"
            element={
              <ProtectedRoute>
                <ReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/progress"
            element={
              <ProtectedRoute>
                <ProgressPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/placement-test"
            element={
              <ProtectedRoute>
                <PlacementTestPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              loading ? null : <Navigate to={user ? "/levels" : "/login"} replace />
            }
          />
        </Routes>
      </main>
    </>
  );
}

export default App;

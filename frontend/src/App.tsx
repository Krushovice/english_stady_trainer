import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Sidebar } from "./components/layout/Sidebar";
import { CertificatePage } from "./pages/CertificatePage";
import { ConversationPage } from "./pages/ConversationPage";
import { CourseExamPage } from "./pages/CourseExamPage";
import { DailyQuizPage } from "./pages/DailyQuizPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ExamPage } from "./pages/ExamPage";
import { HomeworkPage } from "./pages/HomeworkPage";
import { LessonPage } from "./pages/LessonPage";
import { LessonsPage } from "./pages/LessonsPage";
import { LevelsPage } from "./pages/LevelsPage";
import { LoginPage } from "./pages/LoginPage";
import { ModulesPage } from "./pages/ModulesPage";
import { PlacementTestPage } from "./pages/PlacementTestPage";
import { ProgressPage } from "./pages/ProgressPage";
import { RegisterPage } from "./pages/RegisterPage";
import { ReviewPage } from "./pages/ReviewPage";
import { SpeakingPage } from "./pages/SpeakingPage";

function App() {
  const { user, loading } = useAuth();

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={loading ? null : <Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-content">
        <main>
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/levels" element={<LevelsPage />} />
            <Route path="/levels/:levelCode/modules" element={<ModulesPage />} />
            <Route path="/levels/:levelCode/exam" element={<ExamPage />} />
            <Route path="/modules/:moduleSlug/lessons" element={<LessonsPage />} />
            <Route path="/lessons/:lessonSlug" element={<LessonPage />} />
            <Route path="/daily-quiz" element={<DailyQuizPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/course-exam" element={<CourseExamPage />} />
            <Route path="/certificate" element={<CertificatePage />} />
            <Route path="/progress" element={<ProgressPage />} />
            <Route path="/placement-test" element={<PlacementTestPage />} />
            <Route path="/homework" element={<HomeworkPage />} />
            <Route path="/speaking" element={<SpeakingPage />} />
            <Route path="/conversation" element={<ConversationPage />} />
            <Route path="/login" element={<Navigate to="/levels" replace />} />
            <Route path="/register" element={<Navigate to="/levels" replace />} />
            <Route path="/" element={<Navigate to="/levels" replace />} />
            <Route path="*" element={<Navigate to="/levels" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;

import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout } = useAuth();

  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="site-header">
      <NavLink to="/levels" className="brand">
        <span className="brand-mark" aria-hidden="true">ET</span>
        <span className="brand-name">English Trainer</span>
      </NavLink>
      {user && (
        <>
          <nav className="site-nav">
            <NavLink to="/dashboard" className="site-nav-link">
              Панель
            </NavLink>
            <NavLink to="/levels" className="site-nav-link">
              Уроки
            </NavLink>
            <NavLink to="/daily-quiz" className="site-nav-link">
              Ежедневный тест
            </NavLink>
            <NavLink to="/review" className="site-nav-link">
              Повторение
            </NavLink>
            <NavLink to="/homework" className="site-nav-link">
              Домашнее задание
            </NavLink>
            <NavLink to="/speaking" className="site-nav-link">
              Говорение
            </NavLink>
            <NavLink to="/conversation" className="site-nav-link">
              Разговор
            </NavLink>
            <NavLink to="/progress" className="site-nav-link">
              Прогресс
            </NavLink>
            <NavLink to="/course-exam" className="site-nav-link">
              Финальный экзамен
            </NavLink>
            <NavLink to="/certificate" className="site-nav-link">
              Сертификат
            </NavLink>
          </nav>
          <div className="site-header-user">
            <span className="user-chip">
              <span className="user-avatar" aria-hidden="true">{initial}</span>
              <span className="user-email">{user.email}</span>
            </span>
            <button type="button" className="btn-logout" onClick={logout}>
              Выйти
            </button>
          </div>
        </>
      )}
    </header>
  );
}

import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <NavLink to="/levels" className="brand">
        English Trainer
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
            <span>{user.email}</span>
            <button type="button" className="link-button" onClick={logout}>
              Выйти
            </button>
          </div>
        </>
      )}
    </header>
  );
}

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
            <NavLink to="/levels" className="site-nav-link">
              Lessons
            </NavLink>
            <NavLink to="/daily-quiz" className="site-nav-link">
              Daily quiz
            </NavLink>
            <NavLink to="/review" className="site-nav-link">
              Review
            </NavLink>
            <NavLink to="/homework" className="site-nav-link">
              Homework
            </NavLink>
            <NavLink to="/speaking" className="site-nav-link">
              Speaking
            </NavLink>
            <NavLink to="/conversation" className="site-nav-link">
              Talk
            </NavLink>
            <NavLink to="/progress" className="site-nav-link">
              Progress
            </NavLink>
          </nav>
          <div className="site-header-user">
            <span>{user.email}</span>
            <button type="button" className="link-button" onClick={logout}>
              Log out
            </button>
          </div>
        </>
      )}
    </header>
  );
}

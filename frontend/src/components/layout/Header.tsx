import { Link } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="site-header">
      <Link to="/levels" className="brand">
        English Trainer
      </Link>
      {user && (
        <div className="site-header-user">
          <span>{user.email}</span>
          <button type="button" className="link-button" onClick={logout}>
            Log out
          </button>
        </div>
      )}
    </header>
  );
}

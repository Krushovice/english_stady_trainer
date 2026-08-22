import type { ComponentType } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";
import {
  AwardIcon,
  BookIcon,
  CertificateIcon,
  ChatIcon,
  ChartIcon,
  HomeIcon,
  LogoutIcon,
  MicIcon,
  PenIcon,
  RotateIcon,
  TargetIcon,
} from "../icons";

const GROUPS: {
  label: string;
  links: { to: string; label: string; icon: ComponentType<{ width?: number; height?: number }> }[];
}[] = [
  {
    label: "Учиться",
    links: [
      { to: "/dashboard", label: "Панель", icon: HomeIcon },
      { to: "/levels", label: "Уроки", icon: BookIcon },
    ],
  },
  {
    label: "Практика",
    links: [
      { to: "/daily-quiz", label: "Ежедневный тест", icon: TargetIcon },
      { to: "/review", label: "Повторение", icon: RotateIcon },
      { to: "/homework", label: "Домашнее задание", icon: PenIcon },
      { to: "/speaking", label: "Тренировка речи", icon: MicIcon },
      { to: "/conversation", label: "Разговор", icon: ChatIcon },
    ],
  },
  {
    label: "Прогресс",
    links: [
      { to: "/progress", label: "Прогресс", icon: ChartIcon },
      { to: "/course-exam", label: "Финальный экзамен", icon: AwardIcon },
      { to: "/certificate", label: "Сертификат", icon: CertificateIcon },
    ],
  },
];

export function Sidebar() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const initial = user.name?.[0]?.toUpperCase() ?? "?";

  return (
    <aside className="sidebar">
      <NavLink to="/dashboard" className="sidebar-brand">
        <img src="/logo.png" alt="" className="sidebar-brand-mark" />
        <span className="sidebar-brand-text">
          <span className="sidebar-brand-name">KrushEnglish</span>
          <span className="sidebar-brand-caption">Английский — это просто</span>
        </span>
      </NavLink>

      <nav className="sidebar-nav">
        {GROUPS.map((group) => (
          <div key={group.label}>
            <span className="sidebar-group-label">{group.label}</span>
            <div className="sidebar-group-links">
              {group.links.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) => "sidebar-link" + (isActive ? " active" : "")}
                >
                  <Icon width={17} height={17} />
                  <span>{label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <span className="user-avatar" aria-hidden="true">
            {initial}
          </span>
          <span className="user-email" title={user.email}>
            {user.name}
          </span>
        </div>
        <button type="button" className="btn-logout" onClick={logout}>
          <LogoutIcon width={16} height={16} />
          <span>Выйти</span>
        </button>
      </div>
    </aside>
  );
}

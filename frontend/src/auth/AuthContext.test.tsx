import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { User } from "../api/types";
import { AuthProvider, useAuth } from "./AuthContext";

vi.mock("../api/auth", () => ({
  login: vi.fn(),
  register: vi.fn(),
  me: vi.fn(),
}));

import * as authApi from "../api/auth";

const user: User = {
  id: "u1",
  email: "anna@example.com",
  name: "Anna",
  created_at: "2026-08-22T00:00:00Z",
};

function Probe() {
  const { user, loading, login, register, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(loading)}</span>
      <span data-testid="user">{user ? user.email : "none"}</span>
      <button onClick={() => login("anna@example.com", "password123")}>login</button>
      <button onClick={() => register("anna@example.com", "password123", "Anna")}>
        register
      </button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.mocked(authApi.login).mockReset();
  vi.mocked(authApi.register).mockReset();
  vi.mocked(authApi.me).mockReset();
});

describe("AuthProvider", () => {
  it("finishes loading with no user when there is no stored token", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(authApi.me).not.toHaveBeenCalled();
  });

  it("restores the session from a stored token on mount", async () => {
    localStorage.setItem("et_token", "stored-token");
    vi.mocked(authApi.me).mockResolvedValue(user);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent(user.email));
  });

  it("clears an invalid stored token instead of leaving a broken session", async () => {
    localStorage.setItem("et_token", "stale-token");
    vi.mocked(authApi.me).mockRejectedValue(new Error("401"));

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(localStorage.getItem("et_token")).toBeNull();
  });

  it("logs in: persists the token and loads the current user", async () => {
    const userEventSession = userEvent.setup();
    vi.mocked(authApi.login).mockResolvedValue({ access_token: "fresh-token", token_type: "bearer" });
    vi.mocked(authApi.me).mockResolvedValue(user);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));

    await userEventSession.click(screen.getByText("login"));

    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent(user.email));
    expect(authApi.login).toHaveBeenCalledWith("anna@example.com", "password123");
    expect(localStorage.getItem("et_token")).toBe("fresh-token");
  });

  it("registers with the name field, then logs in", async () => {
    const userEventSession = userEvent.setup();
    vi.mocked(authApi.register).mockResolvedValue(user);
    vi.mocked(authApi.login).mockResolvedValue({ access_token: "fresh-token", token_type: "bearer" });
    vi.mocked(authApi.me).mockResolvedValue(user);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("loading")).toHaveTextContent("false"));

    await userEventSession.click(screen.getByText("register"));

    expect(authApi.register).toHaveBeenCalledWith("anna@example.com", "password123", "Anna");
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent(user.email));
  });

  it("logs out: clears both the token and the in-memory user", async () => {
    const userEventSession = userEvent.setup();
    localStorage.setItem("et_token", "stored-token");
    vi.mocked(authApi.me).mockResolvedValue(user);

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent(user.email));

    await userEventSession.click(screen.getByText("logout"));

    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(localStorage.getItem("et_token")).toBeNull();
  });
});

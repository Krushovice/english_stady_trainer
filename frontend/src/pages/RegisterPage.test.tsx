import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { RegisterPage } from "./RegisterPage";

const navigateMock = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => navigateMock };
});

const registerMock = vi.fn();
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ register: registerMock, login: vi.fn(), logout: vi.fn(), user: null, loading: false }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <RegisterPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  navigateMock.mockReset();
  registerMock.mockReset();
});

describe("RegisterPage", () => {
  it("asks for a name alongside email and password", () => {
    renderPage();
    expect(screen.getByLabelText("Имя")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Пароль")).toBeInTheDocument();
  });

  it("submits the entered name, email, and password, then goes to the placement test", async () => {
    const user = userEvent.setup();
    registerMock.mockResolvedValue(undefined);
    renderPage();

    await user.type(screen.getByLabelText("Имя"), "Анна");
    await user.type(screen.getByLabelText("Email"), "anna@example.com");
    await user.type(screen.getByLabelText("Пароль"), "password123");
    await user.click(screen.getByRole("button", { name: "Зарегистрироваться" }));

    expect(registerMock).toHaveBeenCalledWith("anna@example.com", "password123", "Анна");
    expect(navigateMock).toHaveBeenCalledWith("/placement-test");
  });

  it("shows the API's own error message instead of navigating away", async () => {
    const user = userEvent.setup();
    registerMock.mockRejectedValue(new ApiError(409, "A user with this email already exists"));
    renderPage();

    await user.type(screen.getByLabelText("Имя"), "Анна");
    await user.type(screen.getByLabelText("Email"), "anna@example.com");
    await user.type(screen.getByLabelText("Пароль"), "password123");
    await user.click(screen.getByRole("button", { name: "Зарегистрироваться" }));

    expect(await screen.findByText("A user with this email already exists")).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });
});

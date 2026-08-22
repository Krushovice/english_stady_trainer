import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  ReviewItem,
  SkillProgress,
  Title,
  User,
  UserMistake,
} from "../api/types";
import { DashboardPage } from "./DashboardPage";

vi.mock("../api/exercises", () => ({
  getDailyQuiz: vi.fn(),
  getProgress: vi.fn(),
}));
vi.mock("../api/mistakes", () => ({ listMistakes: vi.fn() }));
vi.mock("../api/review", () => ({ listDueReviews: vi.fn() }));
vi.mock("../api/titles", () => ({ getMyTitle: vi.fn() }));
vi.mock("../auth/AuthContext", () => ({ useAuth: vi.fn() }));

import { getDailyQuiz, getProgress } from "../api/exercises";
import { listMistakes } from "../api/mistakes";
import { listDueReviews } from "../api/review";
import { getMyTitle } from "../api/titles";
import { useAuth } from "../auth/AuthContext";

const baseUser: User = {
  id: "u1",
  email: "anna@example.com",
  name: "Анна",
  created_at: "2026-08-22T00:00:00Z",
};

const noTitle: Title = {
  title: "Новичок",
  cefr_grade: null,
  days_practiced: 0,
  mistakes_mastered: 0,
  mistakes_total: 0,
  review_count: 0,
};

function mistake(id: string, status: UserMistake["status"]): UserMistake {
  return {
    id,
    grammar_topic: { id: `g-${id}`, slug: `g-${id}`, title: `Topic ${id}`, description: "" },
    status,
    total_attempts: 5,
    incorrect_attempts: 2,
    last_attempt_at: "2026-08-22T00:00:00Z",
    error_rate: 0.4,
  };
}

function reviewItem(id: string): ReviewItem {
  return {
    id,
    item_type: "vocabulary",
    due_at: "2026-08-22T00:00:00Z",
    interval_days: 2,
    review_count: 1,
    vocabulary: { id: `v-${id}`, headword: "word", translation: "слово", example_sentence: "", audio_url: null },
    grammar_topic: null,
    exercise: null,
  };
}

interface Scenario {
  reviews?: ReviewItem[];
  mistakes?: UserMistake[];
  progress?: SkillProgress[];
  dailyQuiz?: unknown[];
  title?: Title | null;
  user?: User | null;
}

function renderDashboard(scenario: Scenario = {}) {
  vi.mocked(listDueReviews).mockResolvedValue(scenario.reviews ?? []);
  vi.mocked(listMistakes).mockResolvedValue(scenario.mistakes ?? []);
  vi.mocked(getProgress).mockResolvedValue(scenario.progress ?? []);
  vi.mocked(getDailyQuiz).mockResolvedValue((scenario.dailyQuiz ?? []) as never);
  if (scenario.title === undefined || scenario.title === null) {
    vi.mocked(getMyTitle).mockRejectedValue(new Error("no title yet"));
  } else {
    vi.mocked(getMyTitle).mockResolvedValue(scenario.title);
  }
  vi.mocked(useAuth).mockReturnValue({
    user: scenario.user === undefined ? baseUser : scenario.user,
    loading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  });

  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(getDailyQuiz).mockReset();
  vi.mocked(getProgress).mockReset();
  vi.mocked(listMistakes).mockReset();
  vi.mocked(listDueReviews).mockReset();
  vi.mocked(getMyTitle).mockReset();
  vi.mocked(useAuth).mockReset();
});

describe("DashboardPage — 'do now' priority", () => {
  it("prioritizes due reviews above everything else", async () => {
    renderDashboard({ reviews: [reviewItem("r1"), reviewItem("r2")], mistakes: [mistake("m1", "new")] });
    expect(await screen.findByText("У вас 2 элементов на повторение.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "К повторению" })).toHaveAttribute("href", "/review");
  });

  it("uses singular grammar for exactly one due review", async () => {
    renderDashboard({ reviews: [reviewItem("r1")] });
    expect(await screen.findByText("У вас 1 элемент на повторение.")).toBeInTheDocument();
  });

  it("falls back to weak topics when nothing is due for review", async () => {
    renderDashboard({ mistakes: [mistake("m1", "repeated"), mistake("m2", "new")] });
    expect(await screen.findByText("У вас 2 слабых темы для практики.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Практиковаться" })).toHaveAttribute(
      "href",
      "/daily-quiz",
    );
  });

  it("falls back to the daily quiz when there are no due reviews or weak topics", async () => {
    renderDashboard({ dailyQuiz: [{}, {}] });
    expect(await screen.findByText("Пройдите сегодняшний ежедневный тест.")).toBeInTheDocument();
  });

  it("nudges toward starting a lesson when the learner has nothing pending at all", async () => {
    renderDashboard({});
    expect(await screen.findByText("Начните урок, чтобы приступить к практике.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "К урокам" })).toHaveAttribute("href", "/levels");
  });

  it("does not count mastered/improving mistakes as weak topics", async () => {
    renderDashboard({ mistakes: [mistake("m1", "improving"), mistake("m2", "mastered")] });
    expect(await screen.findByText("Начните урок, чтобы приступить к практике.")).toBeInTheDocument();
  });
});

describe("DashboardPage — greeting name", () => {
  it("greets the learner by name", async () => {
    renderDashboard({ user: { ...baseUser, name: "Анна" } });
    expect(await screen.findByText(/Анна\.$/)).toBeInTheDocument();
  });

  it("falls back to the email's local part for a pre-migration account with a blank name", async () => {
    renderDashboard({ user: { ...baseUser, name: "", email: "user2@mail.ru" } });
    expect(await screen.findByText(/user2\.$/)).toBeInTheDocument();
  });
});

describe("DashboardPage — loading and error states", () => {
  it("shows a loading message while the core queries are pending", () => {
    vi.mocked(listDueReviews).mockReturnValue(new Promise(() => {}));
    vi.mocked(listMistakes).mockReturnValue(new Promise(() => {}));
    vi.mocked(getProgress).mockReturnValue(new Promise(() => {}));
    vi.mocked(getDailyQuiz).mockReturnValue(new Promise(() => {}));
    vi.mocked(getMyTitle).mockReturnValue(new Promise(() => {}));
    vi.mocked(useAuth).mockReturnValue({
      user: baseUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByText("Загрузка панели...")).toBeInTheDocument();
  });

  it("shows an error message if a core query fails", async () => {
    vi.mocked(listDueReviews).mockRejectedValue(new Error("boom"));
    vi.mocked(listMistakes).mockResolvedValue([]);
    vi.mocked(getProgress).mockResolvedValue([]);
    vi.mocked(getDailyQuiz).mockResolvedValue([]);
    vi.mocked(getMyTitle).mockResolvedValue(noTitle);
    vi.mocked(useAuth).mockReturnValue({
      user: baseUser,
      loading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    });

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Не удалось загрузить панель.")).toBeInTheDocument();
  });
});

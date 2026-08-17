# English Trainer

Personal interactive English-learning platform. Product rules, architecture, and the phase-by-phase plan are kept locally (`CLAUDE.md`, `ARCHITECTURE.md`, `docs/`) and are not tracked in this repository.

## Status

Phases 0–4 are done: authentication, DB, test infrastructure, the course tree (levels/modules/lessons/blocks + vocabulary/grammar) with a YAML content loader, a deterministic exercise engine (multiple choice, fill-in-the-blank, sentence ordering, reading comprehension) with attempt history and per-skill progress, a placement test that estimates a CEFR level per skill and recommends starting modules, and learning intelligence — automatic grammar-mistake classification and spaced-repetition review scheduling on every practice attempt. No frontend exists yet — Phase 2's course pages, Phase 3's exercise UI, the placement test screen, and a review/mistakes dashboard are all deferred to Phase 6, alongside scaffolding the frontend project itself. Phase 5 (AI) is in progress: the provider abstraction and a local LM Studio adapter are wired up and verified end to end (see "AI (local model)" below); the `AIService` business layer and actual AI-powered features (writing feedback, homework, conversation) come next.

## Stack

Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose. Dependencies are managed with [uv](https://docs.astral.sh/uv/) into a local `.venv` — never installed system-wide.

## Running it

```bash
cp .env.example .env   # then edit JWT_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

This brings up PostgreSQL, Redis, and the API, applies migrations, syncs course content from `content/` into the database, and serves the API at `http://localhost:8000` (docs at `/docs`, health check at `/health`).

## Development (outside Docker)

```bash
uv sync                 # installs into .venv/, never system-wide
docker compose up -d db redis
uv run alembic upgrade head
uv run python -m scripts.sync_content
uv run uvicorn app.main:app --reload
```

## Content

Lessons live as YAML files under `content/` (one file per lesson, containing its level/module/lesson metadata and all eleven lesson blocks), validated against `app/schemas/content.py`. Adding or editing a lesson is a content change, not a code change — re-run `uv run python -m scripts.sync_content` (or restart the `api` container) to load it. The loader upserts by natural key (level code, module/lesson slug, vocabulary headword, grammar topic slug), so re-running it after an edit updates existing rows instead of duplicating them. `content/b1/small-talk/making-small-talk.yaml` is the format reference.

## Exercises

Exercises are authored inside a lesson's `exercises` block, alongside its other content, and validated against `app/schemas/exercise.py`. Four types are implemented so far: `multiple_choice`, `fill_blank`, `sentence_ordering`, `reading_comprehension` — each has a typed prompt/answer-key shape and a deterministic scorer in `app/services/scoring.py` (no LLM involved). API: `GET /lessons/{slug}/exercises` (prompt only, no answer key), `POST /exercises/{id}/attempts` (submit and get scored feedback), `GET /exercises/{id}/attempts` (a learner's own history), `GET /progress` (per-skill attempt/accuracy counts).

## Placement test

A 24-item bank (`content/placement_test/bank.yaml`) covering grammar, vocabulary, reading, and listening across A1–B2, distinct from lesson exercises (no `lesson_id`, `is_placement_item=True`). Listening items are transcript-based `reading_comprehension` exercises tagged `skill: listening` — there's no audio pipeline yet. API: `GET /placement-test/items` (the bank, no answer keys), `POST /placement-test/submit` (grades everything, estimates a CEFR level per skill plus an overall level, persists it to the user's `learning_profile`, and returns recommended starting modules), `GET /placement-test/result` (re-reads the persisted result without retaking the test). Scoring and module recommendation are pure, DB-free functions in `app/services/placement_scoring.py`.

## Learning intelligence

Every submitted attempt (`POST /exercises/{id}/attempts`) automatically schedules its next spaced-repetition review — for the exercise itself, and for its linked vocabulary word / grammar topic if it has one — and, for grammar-topic-tagged exercises, updates that topic's mistake status (`new` → `repeated`/`improving` → `mastered`, `app/services/mistake_classification.py`). Scheduling is a simplified SM-2 (`app/services/spaced_repetition.py`), both pure and unit-tested, deliberately isolated from the API so the algorithm can change later. API: `GET /mistakes` (optionally `?status=`), `GET /review/due`, `POST /review/{id}/complete`. Placement-test answers don't feed either system — see `docs/decisions.md`.

## AI (local model)

AI features (Phase 5, in progress) run against a locally hosted model instead of a cloud API — no per-request cost, everything stays on the machine. Setup:

1. Install [LM Studio](https://lmstudio.ai), update it to the latest version
2. Download **Qwen3.5-9B** (Q4_K_M or UD-Q4_K_XL quant) from the in-app model catalog
3. Load it and start the local server (Developer tab, default port `1234`)

`app/integrations/ai/` holds the provider abstraction: `AIProvider` (protocol), `LMStudioProvider` (talks to LM Studio's OpenAI-compatible endpoint via the `openai` SDK), and `MockAIProvider` (canned responses, used by tests — no AI-dependent test hits a real model). Config is `AI_*` in `.env.example`. Outside Docker, `AI_BASE_URL` points straight at `localhost:1234`; `docker compose` overrides it to `host.docker.internal:1234` for the `api` container, since LM Studio runs natively on the host, not in a container.

Qwen3.5 is a "thinking" model and reasons before answering — LM Studio currently doesn't let the API disable that (upstream bug), so `AI_MAX_TOKENS` defaults to a generous `1500` to give it room; only the final answer (`message.content`) is ever returned to callers, the reasoning trace is discarded. See `docs/decisions.md` for the full rationale.

## Tests

```bash
docker compose up -d db redis
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Integration tests create and tear down their own `..._test` database — they never touch the dev database.

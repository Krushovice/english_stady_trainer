# English Trainer

Personal interactive English-learning platform. Product rules, architecture, and the phase-by-phase plan are kept locally (`CLAUDE.md`, `ARCHITECTURE.md`, `docs/`) and are not tracked in this repository.

## Status

Phase 0 (architecture proposal), Phase 1 (foundation), and Phase 2 (course engine) are done: authentication, DB, test infrastructure, and the course tree (levels/modules/lessons/blocks + vocabulary/grammar) with a YAML content loader are in place. Phase 3 (exercises) is next.

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

## Tests

```bash
docker compose up -d db redis
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Integration tests create and tear down their own `..._test` database — they never touch the dev database.

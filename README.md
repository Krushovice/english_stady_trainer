# English Trainer

Personal interactive English-learning platform. Product rules, architecture, and the phase-by-phase plan are kept locally (`CLAUDE.md`, `ARCHITECTURE.md`, `docs/`) and are not tracked in this repository.

## Status

Phase 0 (architecture proposal) and Phase 1 (foundation) done: authentication, DB, and test infrastructure are in place. Phase 2 (course engine) is next.

## Stack

Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose. Dependencies are managed with [uv](https://docs.astral.sh/uv/) into a local `.venv` — never installed system-wide.

## Running it

```bash
cp .env.example .env   # then edit JWT_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
```

This brings up PostgreSQL, Redis, and the API, applies migrations automatically, and serves the API at `http://localhost:8000` (docs at `/docs`, health check at `/health`).

## Development (outside Docker)

```bash
uv sync                 # installs into .venv/, never system-wide
docker compose up -d db redis
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Tests

```bash
docker compose up -d db redis
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Integration tests create and tear down their own `..._test` database — they never touch the dev database.

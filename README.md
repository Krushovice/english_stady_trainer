# English Trainer

Personal interactive English-learning platform. Product rules and phase plan live in a local `CLAUDE.md` (not tracked in this repo). Architecture decisions derived from it are in [ARCHITECTURE.md](ARCHITECTURE.md).

## Status

Phase 0 (architecture proposal) in progress. See [ARCHITECTURE.md](ARCHITECTURE.md) and `docs/` for supporting design docs.

## Stack

Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose. See ARCHITECTURE.md for the full breakdown and rationale.

## Development

Everything runs in Docker Compose locally; no host-level Python/Node installs required for running the app. Application-level dependencies (Python, JS) are installed inside the project's virtual environment / `node_modules`, never system-wide.

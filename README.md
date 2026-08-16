# English Trainer

Personal interactive English-learning platform. Architecture and product rules are defined in [CLAUDE.md](CLAUDE.md) — read that first.

## Status

Phase 0 (architecture proposal) in progress. See [ARCHITECTURE.md](ARCHITECTURE.md) once available and `docs/` for supporting design docs.

## Stack

Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose. See ARCHITECTURE.md for the full breakdown and rationale.

## Development

Everything runs in Docker Compose locally; no host-level Python/Node installs required for running the app. Application-level dependencies (Python, JS) are installed inside the project's virtual environment / `node_modules`, never system-wide.

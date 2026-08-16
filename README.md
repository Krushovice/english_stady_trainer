# English Trainer

Personal interactive English-learning platform. Product rules, architecture, and the phase-by-phase plan are kept locally (`CLAUDE.md`, `ARCHITECTURE.md`, `docs/`) and are not tracked in this repository.

## Status

Phase 0 (architecture proposal) done locally. Phase 1 (foundation) is next.

## Stack

Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose.

## Development

Everything runs in Docker Compose locally; no host-level Python/Node installs required for running the app. Application-level dependencies (Python, JS) are installed inside the project's virtual environment / `node_modules`, never system-wide.

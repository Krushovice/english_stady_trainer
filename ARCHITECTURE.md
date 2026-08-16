# Architecture Proposal — Phase 0

This document is the Phase 0 deliverable required by [CLAUDE.md](CLAUDE.md) ("First Task"): inspect, propose, agree, only then implement. It records decisions, not just intentions, so later phases can be checked against it instead of against memory of a conversation.

## 1. Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python (latest stable) | Required by CLAUDE.md |
| API framework | FastAPI | Required by CLAUDE.md; async-first, good OpenAPI story |
| Validation | Pydantic v2 | Required by CLAUDE.md |
| ORM | SQLAlchemy 2.x (2.0-style API) | Required by CLAUDE.md |
| Migrations | Alembic | Required by CLAUDE.md |
| Database | PostgreSQL | Required by CLAUDE.md |
| Cache / queues | Redis | Required by CLAUDE.md; also backs rate limiting and spaced-repetition scheduling |
| Containerization | Docker / Docker Compose | Required by CLAUDE.md |
| Frontend | React + TypeScript + Vite | **Assumption, not requested explicitly.** CLAUDE.md only asks for "a modern frontend framework suitable for highly interactive educational UI." A full SSR meta-framework (Next.js) buys nothing for a single-user app behind auth; Vite keeps the loop fast. Cheap to revisit before Phase 6 UI work scales up. |

No other runtime dependencies until a concrete problem justifies them (per CLAUDE.md: "do not introduce unnecessary technologies").

## 2. Layering

```
API (FastAPI routes)
  → Service (business logic, orchestration)
    → Repository (SQLAlchemy queries, one per aggregate)
      → Database (PostgreSQL)
```

Rules:
- Route handlers only: parse/validate request, call one service method, map result to response schema. No business logic in `api/`.
- Services own transactions and business rules. Services depend on repository interfaces, not on SQLAlchemy sessions directly, so they stay testable with fakes.
- Repositories are the only place that knows SQLAlchemy query syntax.
- External integrations (AI providers, STT/TTS) sit behind `integrations/`, called only from services — never from routes, never from repositories.

## 3. Project structure

```
app/
├── api/            # routers, request/response wiring only
├── core/           # settings, security (hashing/JWT), DI wiring
├── models/         # SQLAlchemy 2.x ORM models
├── schemas/        # Pydantic v2 request/response models
├── repositories/   # DB access, one module per aggregate root
├── services/       # business logic, transaction boundaries
├── integrations/   # AI provider adapters, STT/TTS, behind interfaces
├── workers/         # background jobs (spaced-repetition scheduling, async AI feedback)
└── main.py
content/            # course content as data (YAML/Markdown), not Python
docs/               # supporting design docs (schema, roadmap, decisions)
tests/
  unit/
  integration/
  e2e/
```

## 4. Multi-tenant-ready single-user design

The product is being built for one real user today, but CLAUDE.md requires the schema to stay clean for future users. Concretely:

- Every user-owned table carries a `user_id` foreign key from the first migration, even though exactly one row will exist in `users` for a long time.
- Nothing about "the current user" is hardcoded in application code (no singleton user id, no skipped auth checks). Auth is real from Phase 1.
- Personalization (CEFR level per skill, priority goals such as travel/conversation/listening vs. work/IT, weak topics) lives in a `learning_profile` row per user, not in config files or code. A second user gets their own profile automatically; nothing about lesson selection logic needs to change.

## 5. Content as data

Lessons, vocabulary, and grammar topics are authored as YAML/Markdown files under `content/`, versioned in git independently of application code. A content loader service parses and validates these files and syncs them into the database (`Level`/`Module`/`Lesson`/`LessonBlock`/`Vocabulary`/`GrammarTopic` tables). Adding a lesson is a content change, never a code change — required by CLAUDE.md.

## 6. AI integration boundary

`AIService` is the only interface application code talks to. A provider adapter underneath implements it (Anthropic, OpenAI, or both — decided in Phase 5, see `docs/decisions.md`). Prompts live as versioned files, not inline strings. Every AI-dependent service degrades gracefully if the provider is unavailable — the rest of the app (lessons, deterministic exercises, progress) must keep working.

## 7. Deployment model

Development and the first production deployment both run the same Docker Compose stack:

1. **Now:** Compose stack (`api`, `db`, `redis`, and later `web`) runs fully isolated on the local machine — no host services, no host Python.
2. **Later:** the identical Compose stack is deployed to a VPS. The only additions are a reverse proxy, TLS termination, and a domain — no application or architecture changes required to make that move.

## 8. Testing strategy

- **Unit**: scoring, progress calculation, review scheduling, mistake classification — pure functions/services, no DB.
- **Integration**: repositories and services against a real test PostgreSQL instance (via Compose), API endpoints via FastAPI's test client.
- **E2E**: register → placement test → lesson → exercise → result → progress → review, as one scripted path.
- AI-dependent code is tested against a mock provider implementing the `AIService` interface — no test depends on a live AI call.

## 9. Decisions already made (see `docs/decisions.md` for full log)

- Content bootstrapping starts from a placement test result, not a hardcoded A1 start, because the primary user's real level is ~B1.
- AI provider selection is deferred to Phase 5 by design — nothing before it depends on which vendor is chosen.
- Deployment: local Docker Compose during development, same stack redeployed to a VPS later.

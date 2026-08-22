# English Trainer

Personal interactive English-learning platform. Product rules, architecture, and the phase-by-phase plan are kept locally (`CLAUDE.md`, `ARCHITECTURE.md`, `docs/`) and are not tracked in this repository.

## Status

Phases 0–4 are done: authentication, DB, test infrastructure, the course tree (levels/modules/lessons/blocks + vocabulary/grammar) with a YAML content loader, a deterministic exercise engine (multiple choice, fill-in-the-blank, sentence ordering, reading comprehension) with attempt history and per-skill progress, a placement test that estimates a CEFR level per skill and recommends starting modules, and learning intelligence — automatic grammar-mistake classification and spaced-repetition review scheduling on every practice attempt. Phase 5 (AI) is done: the provider abstraction, writing feedback, homework generation, conversation mode, and the Speaking flow (prompt → recording → STT → evaluation → feedback → retry) are all built and verified end to end against real local models — see "AI (local model)", "Writing feedback and homework", "Conversation mode", "Speech-to-text (STT)", and "Speaking" below. Content authoring is also done: all 43 planned lessons across A1/A2/B1/B2 are written (see "Content" below); C1/C2 stay explicitly out of scope. Phase 6 (UX) is mostly done: the core learning loop, a real `Dashboard` (do now / weak at / improved / due for review), nav (Dashboard/Lessons/Daily quiz/Review/Homework/Speaking/Talk/Progress/Final exam/Certificate), progress screen with a computed title/grade, review center, placement test UI, level exit exams, frontend for Homework/Speaking/AI Conversation, a course-wide final exam gating a printable completion certificate, a "C1/C2 — coming soon" placeholder on `/levels`, sequential lesson unlocking with a single-check exercise flow, a placement-driven starting-point choice, real local TTS audio for every lesson/placement listening item, and a full Russian translation of the interface chrome (see "Sequential lessons and the single-check exercise flow", "Placement-driven starting point", "Listening audio (Kokoro-TTS)", and "Russian UI translation" below) are all built (as of 2026-08-22) — this closes out the live-testing-feedback round. Still open: a VPS deployment, general UI polish, and frontend automated tests (deliberately deferred, see `docs/decisions.md`).

## Stack

Backend: Python / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Alembic / PostgreSQL / Redis / Docker Compose. Dependencies are managed with [uv](https://docs.astral.sh/uv/) into a local `.venv` — never installed system-wide.

Frontend: React 19 / TypeScript / Vite, `react-router-dom` for routing, `@tanstack/react-query` for data fetching. Dependencies are managed with npm into `frontend/node_modules/` — never installed system-wide.

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

## Frontend

```bash
cd frontend
npm install       # if npm hangs at "audit bulk request", re-run with --no-audit
npm run dev        # serves at http://localhost:5173
```

Needs the API running (either `docker compose up` from the repo root, or the "Development (outside Docker)" steps above) — the API's `CORS_ORIGINS` setting already allows `http://localhost:5173` by default.

`frontend/src/`:
- `api/` — a small hand-written `fetch` wrapper (`client.ts`, handles the bearer token + typed `ApiError`, plus `apiUpload` for multipart requests) and one module per resource (`auth.ts`, `course.ts`, `exercises.ts`, `homework.ts`, `speaking.ts`, `conversation.ts`, ...) and hand-kept-in-sync TS types (`types.ts`) mirroring `app/schemas/*.py`. No codegen yet — see `docs/decisions.md`.
- `auth/` — `AuthContext` (JWT in `localStorage`, hydrated via `GET /auth/me` on load) and `ProtectedRoute`.
- `pages/` — one per route: `LoginPage`, `RegisterPage`, `DashboardPage`, `LevelsPage`, `ModulesPage`, `LessonsPage`, `LessonPage`, `ProgressPage`, `DailyQuizPage`, `PlacementTestPage`, `ReviewPage`, `ExamPage`, `CourseExamPage`, `CertificatePage`, `HomeworkPage`, `SpeakingPage`, `ConversationPage`.
- `components/layout/Header.tsx` — nav (Dashboard / Lessons / Daily quiz / Review / Homework / Speaking / Talk / Progress / Final exam / Certificate) with active-state styling via `react-router-dom`'s `NavLink`.
- `components/LessonBlockView.tsx` — renders each lesson block type (goals, context, examples, reading, listening, speaking, homework, review, ...); unknown block types fall back to a raw JSON dump instead of silently disappearing. `context`/`reading` blocks additionally render a collapsed "Кратко на русском" toggle when the block's content has a `summary_ru` key — see "Content" below. Note: a lesson's `speaking`/`homework` blocks are static author-written prompts, unrelated to the AI-driven `HomeworkPage`/`SpeakingPage` below — the two systems don't share content, only a name.
- `components/exercises/` — one input component per scored exercise type (multiple choice, fill-in-the-blank, sentence ordering, reading comprehension), each a plain controlled input that reports an answer via `onChange` with no submission logic of its own. Two things sit on top of them: `ExerciseCard` (instant per-item submit-and-feedback — Daily Quiz, Review, the post-lesson mini-test) and the shared `ExerciseItem` switch (answer-collection only, no button — `ExamPage`/`CourseExamPage`/`PlacementTestPage`'s batched-submission exams and `LessonPage`'s single-check exercises block). `ExerciseCard`'s "Try again" remounts the input component (via a bumped `key`) so old answers don't linger; a successful submit also invalidates the `progress`/`daily-quiz`/`review-due` react-query caches so those pages don't show stale data.
- `components/ReviewFlashcard.tsx` — front/back self-rated card for vocabulary and grammar-topic review items (no exercise attached to quiz on): reveal, then Remembered/Forgot calls `POST /review/{id}/complete`.
- `components/WritingFeedbackCard.tsx` — renders the 5-section AI feedback shape (Good / Grammar / Vocabulary / Natural version / Try again) shared by Homework-task and Speaking feedback.
- `components/AudioRecorder.tsx` — `getUserMedia`/`MediaRecorder` wrapper for the Speaking flow: record with a live timer → stop → preview playback with a re-record option → submit. Requires a secure context (`https:`, or `localhost`/`127.0.0.1`) per browser spec — `navigator.mediaDevices` is `undefined` otherwise.

Verified live end to end with headless-browser scripts against the real API — zero console errors: (1) register → levels → modules → lessons → lesson → submit all 4 exercise types → progress/daily quiz update → logout; (2) register → placement test intro → answer all ~24 items → submit → result → banner gone on `/levels` → revisiting `/placement-test` shows the saved result instead of the intro (the "banner gone" part needed a real fix in 2026-08-21's placement-choice round — see "Placement-driven starting point" below); (3) with review items backdated to due, `/review` renders exercise/vocabulary/grammar items correctly and rating a flashcard removes it from the list.

## Progress, Daily quiz, and Review

- `GET /progress` (existing, Phase 3) — per-skill attempt/accuracy counts, shown as a card per skill on `ProgressPage`. Deliberately not reduced to one aggregate number, per CLAUDE.md.
- `GET /practice/daily-quiz` — up to 8 exercises drawn from lessons the learner has already studied (any skill mix), stable for the whole day (seeded by user + date, nothing persisted), graded through the same `POST /exercises/{id}/attempts` as lesson exercises. Deliberately a separate feature from the spaced-repetition review queue below — see `docs/decisions.md`.
- `GET /review/due` (existing, Phase 4) — `ReviewPage` at `/review`. Nothing is due the same day an item is first studied (spaced repetition's minimum interval is 1 day even on a correct first answer), so this is expected to be empty right after finishing a fresh lesson — the empty state says so rather than looking broken. Fills in automatically from a day later onward.

## Levels page

`LevelsPage` also shows two static, non-clickable "C1 / C2 — Coming soon" cards alongside
the real A1–B2 level cards, reusing the existing locked-card style. No `Level` DB row exists
for C1/C2 — CLAUDE.md keeps them out of scope for the MVP.

## Titles and grades

`GET /titles/me` (folded into the existing `/progress` route file) — one computed "main"
title + the user's current CEFR grade (e.g. "Отладчик · B1"), shown as a card on
`ProgressPage`. Computed from three signals with no new tracking tables: distinct days
practiced, mistake-remediation ratio (mastered/total `UserMistake` topics), and lifetime
`ReviewItem.review_count`. Tier ladder and CEFR-grade choice are documented in
`app/services/title_service.py` and `docs/decisions.md`.

## Course-wide final exam and certificate

Course-wide final exam: `CourseExamPage` at `/course-exam` ("Final exam" in nav) — 44
questions spanning all four CEFR levels, ordered easy → hard (difficulty-bucketed, no
shuffle across buckets), 70%/15 min/3 attempts per 24h window — same parameters as the
per-level exit exams, reused directly rather than redefined. Only available once the B2
exit exam is passed.

`CertificatePage` at `/certificate` — unlocked once the course-wide exam is passed: email,
earned date, "B2", and a per-skill accuracy table reusing `GET /progress`. Styled for
browser print/PDF (Ctrl+P) — the first `@media print` CSS in the project.

## Dashboard

`DashboardPage` at `/dashboard` (first nav item) — "do now / weak at / improved / due for
review", composed client-side from `GET /review/due`, `GET /mistakes`, `GET /progress`, and
`GET /practice/daily-quiz` via parallel `useQuery` calls. No new backend endpoint — see
`docs/decisions.md` for why.

## Sequential lessons and the single-check exercise flow

Live-testing feedback (2026-08-21): lessons inside a level could previously be opened in
any order, and each exercise had its own "Check" button with no lesson-level pass/fail
signal. Now:

- `LessonProgressService` (`app/services/lesson_progress_service.py`) computes a lesson's
  completion from the *latest* attempt per exercise: 70% correct (`PASS_THRESHOLD`) passes
  it. A lesson unlocks only once the lesson immediately before it in the level (via the
  existing `CourseRepository.get_previous_lesson_in_level`) is passed; the level's first
  lesson is always open. `GET /levels/{code}/modules` now returns `unlocked`/`passed` per
  module (modules are 1:1 with lessons); `GET /lessons/{slug}` 403s on a locked lesson
  (`LessonLockedError`) as a direct-URL guard behind the UI's own lock. `ModulesPage` shows
  locked modules as non-clickable cards naming the lesson to pass first; `LevelsPage`'s
  existing `.card-locked` styling is reused, not reinvented.
- `GET /lessons/{slug}/completion` — accuracy, pass/fail, and which exercise ids are still
  wrong, for the "N exercises from your last attempt still need fixing" banner on revisit.
- `LessonPage`'s Exercises block dropped per-exercise "Check" buttons (`ExerciseCard`) for
  a single "Check" at the bottom that grades every answered exercise (sequentially, not
  concurrently — a single failed submission must not discard the others that already
  succeeded) and shows an aggregate `correct/total` plus a ✅/❌ per exercise. Already-passed
  exercises lock as read-only on return visits. Daily Quiz, Review Center, and the
  post-lesson mini-test deliberately keep the old per-exercise instant-feedback
  `ExerciseCard` — see `docs/decisions.md` for why those three stay out of scope.
- New shared `components/exercises/ExerciseItem.tsx` — the answer-collecting switch over
  the 4 scored exercise types, extracted from what used to be separately duplicated as
  `ExamItem` (`ExamPage`) and `PlacementItem` (`PlacementTestPage`); both exam pages and
  `LessonPage` now import the one component.
- Fixed alongside this: a lesson's `mini_test` content block was rendering as a raw JSON
  dump (`LessonBlockView`'s `SKIPPED_TYPES` didn't include it — the real mini-test UI comes
  from `LessonPage`'s own dedicated fetch, not this block); and `frontend/src/api/types.ts`
  was missing the `MistakeStatus`/`UserMistake` types that `api/mistakes.ts` (Dashboard,
  Phase 6) already imported — both went undetected because `npx tsc --noEmit` alone
  type-checks nothing in this project (the root `tsconfig.json` has an empty `files` list);
  the real check is `npx tsc --noEmit --project tsconfig.app.json`.

## Placement-driven starting point

After submitting the placement test, the result screen now offers a choice instead of a single
"Continue to lessons" button (shown only right after a fresh submission, not on a later revisit):
"Start at {assessed level}" or "Review from {a level already reachable}". New
`learning_profiles.placement_skip_credit_through: CEFRLevel | None` column — set by "start at
assessed level" to the level *below* the assessed one; `LEVEL_ORDER`-based
`placement_scoring.is_level_credited(level, credit_through)` is the single pure check reused by
both `LevelExamService.is_level_unlocked` (a credited *preceding* level unlocks the next one,
same as passing its exam) and `LessonProgressService` (a credited level's own lessons are all
auto-unlocked and auto-passed, `total=0`/`attempted=False`, honestly distinct from a real
attempt). Deliberately the assessed level itself is *not* auto-credited — only levels strictly
below it — so the learner still has to actually study the level they were placed into. "Review"
is a pure no-op server-side: the chosen lower level is already reachable under the ordinary
unlock rules, so nothing needs to change. New `POST /placement-test/choose-starting-point`.

Caught live via Docker-isolated Playwright while verifying this (both are now fixed): choosing
"assessed" didn't visibly unlock anything on `/levels` because that page's `react-query` cache
(shared key `["levels"]`) had already been populated by the result screen's own "which levels are
already reachable" lookup and was never invalidated after the choice; separately, the "take the
placement test" banner kept showing after a completed submission because `["placement-result"]`
was never invalidated either — a pre-existing gap, not new to this change.

## Homework, Speaking, and AI Conversation frontend

Frontend for the three AI-driven Phase-5 backends that previously had none:

- `HomeworkPage` at `/homework` — "Generate homework" calls `POST /homework/generate`
  (3 AI-written tasks from the user's most recently studied lesson); each task takes a
  `<textarea>` submission and shows `WritingFeedbackCard` once graded.
- `SpeakingPage` at `/speaking` — "Get a speaking prompt" calls `POST /speaking/prompts`;
  `AudioRecorder` records the answer, then `submitSpeakingAttempt` uploads it (multipart)
  and shows the STT transcript + `WritingFeedbackCard`.
- `ConversationPage` at `/conversation` (nav label "Talk") — optional topic → chat UI
  (`POST /conversation/sessions`/`/messages`) → "End conversation" → the 5-section
  end-of-session analysis (`ConversationAnalysisResponse`).

None of the three backends have a "list mine"/"current" endpoint — each `generate`/`start`
call creates a new row — so each page persists its current id in `localStorage`
(`et_homework_id` / `et_speaking_attempt_id` / `et_conversation_id`) to resume unfinished
work across a reload, the same problem `ExamPage` already solves for exit-exam attempts.

Verified live with Playwright inside an isolated Docker container against the real dev
stack (registration, nav, all three intro states, and the AI-provider-unavailable 503
error path all confirmed correct) — see `docs/decisions.md` for the exact setup and its
one known gap (recording itself couldn't be exercised through that specific test
hostname, a secure-context browser restriction unrelated to the shipped code).

## Placement test

`PlacementTestPage` at `/placement-test`: intro (skippable) → all ~24 bank items answered in one pass, no per-item feedback → single batched `POST /placement-test/submit` → result (per-skill CEFR level + overall estimate + recommended starting modules, matching CLAUDE.md's example format). New users land here right after registering (`RegisterPage` → `/placement-test` instead of `/levels`); `LevelsPage` shows a banner linking to it for anyone who skipped. Revisiting the page after completion shows the saved result (`GET /placement-test/result`) instead of the intro. Backend has existed since Phase 3.5; this was the missing UI.

## Content

Lessons live as YAML files under `content/` (one file per lesson, containing its level/module/lesson metadata and all twelve lesson blocks), validated against `app/schemas/content.py`. Adding or editing a lesson is a content change, not a code change — re-run `uv run python -m scripts.sync_content` (or restart the `api` container) to load it. The loader syncs in two passes — every file's metadata (level/module/lesson/vocabulary/grammar) first, then every file's exercises second — so an exercise can recycle a grammar topic from another lesson regardless of alphabetical file order (see `docs/decisions.md`). Upserts are by natural key (level code, module/lesson slug, vocabulary headword, grammar topic slug), so re-running after an edit updates existing rows instead of duplicating them. `content/b1/small-talk/making-small-talk.yaml` is the format reference.

**A1 is complete: all 15 topics from `CLAUDE.md`** (`content/a1/`) — Introduction, Personal Information, Family, Numbers and Time, Daily Routine, Food, Shopping, Home, City, Transport, Work, Hobbies, Weather, Travel, Revision. Each has 4 main exercises plus a 5-question `mini_test` block (see Exercises below), with grammar recycled lesson to lesson: to be → possessive adjectives → have/has → telling time → Present Simple (-s) → some/any → there is/are → prepositions of place → can → comparatives → Present Continuous → like+gerund → going to → Past Simple → mixed revision.

**A2 is also complete: 10 lessons** (`content/a2/`) — Ordering Food, Asking for Directions, Hotel Check-in, Everyday Problems, Technology, Making Plans, Past Continuous & Storytelling, Superlatives, Gaming & Free Time, Revision. Grammar arc: polite requests (Could I have/I'd like) → imperatives + movement prepositions → Present Perfect (introduction) → have to/must/should → used to → going to vs will → Past Continuous vs Past Simple → superlatives → gerund/infinitive verb patterns → mixed revision. Same structure as A1 (4 main exercises + self-contained `mini_test` per lesson, none on Revision).

**B1 is also complete: 8 lessons** (`content/b1/`) — Small Talk, Talking About Experiences, Expressing Opinions, Describing Past Events in Detail, Future Plans & Predictions, Solving Problems, Technology & Media, Revision. Grammar arc: question tags → Present Perfect for experience (ever/never/already/yet, for/since) → concession clauses (although/despite) → Past Perfect → Future Continuous + prediction modals → second conditional → passive voice → mixed revision. Unlike A1/A2, `context`/`grammar` blocks are authored in English with a collapsible `summary_ru` gloss (see the immersion convention below).

**B2 is also complete: 10 lessons** (`content/b2/`) — Reported Speech, Hypothetical Situations, Wishes and Regrets, Speculating and Deducing, Describing People and Things Precisely (relative clauses), Debating Opinions, Advanced Storytelling, Society & Abstract Topics, Talking Naturally, Revision. Grammar arc: reported speech → third/mixed conditionals → wish/if only + should have → modals of speculation (must/might/can't have) → defining/non-defining relative clauses → cleft sentences for emphasis → inversion for emphasis → passive reporting + causative (have/get something done) → discourse markers + three-part phrasal verbs → mixed revision. English-only immersion, no `summary_ru`. **This completes the full course content plan: 43 lessons across A1-B2** (C1/C2 stay explicitly out of scope, see `docs/decisions.md`).

**Language immersion convention** (see `docs/decisions.md`): A1-A2 lessons author `context`/`grammar` blocks in Russian directly. B1 keeps them in English but adds an optional `summary_ru: >` key to long text blocks (`context`, `reading`) — a short Russian gloss, not a full translation, rendered client-side as a collapsed toggle the learner opens on demand. B2 drops `summary_ru` entirely. No schema change needed for this — `context`/`reading`/`examples` blocks are free-form `content: dict` already.

## Exercises

Exercises are authored inside a lesson's `exercises` block, alongside its other content, and validated against `app/schemas/exercise.py`. Four types are implemented so far: `multiple_choice`, `fill_blank`, `sentence_ordering`, `reading_comprehension` — each has a typed prompt/answer-key shape and a deterministic scorer in `app/services/scoring.py` (no LLM involved). API: `GET /lessons/{slug}/exercises` (prompt only, no answer key), `POST /exercises/{id}/attempts` (submit and get scored feedback), `GET /exercises/{id}/attempts` (a learner's own history), `GET /progress` (per-skill attempt/accuracy counts).

**Post-lesson mini-test**: a lesson can also author a `mini_test` block — a separate, self-contained bank of 5 fresh questions testing *that lesson's own* material (`Exercise.is_mini_test_item=True`, excluded from the normal exercises listing). It surfaces automatically on the *next* lesson in the same level as a "🔁 Quick review: {previous lesson}" section (`GET /lessons/{slug}/mini-test`, `CourseRepository.get_previous_lesson_in_level`) — the immediate, same-visit reinforcement the Review Center can't provide (its 1-day minimum interval means nothing is due the same day it's studied).

## Placement test

A 24-item bank (`content/placement_test/bank.yaml`) covering grammar, vocabulary, reading, and listening across A1–B2, distinct from lesson exercises (no `lesson_id`, `is_placement_item=True`). Listening items are transcript-based `reading_comprehension` exercises tagged `skill: listening` — there's no audio pipeline yet. API: `GET /placement-test/items` (the bank, no answer keys), `POST /placement-test/submit` (grades everything, estimates a CEFR level per skill plus an overall level, persists it to the user's `learning_profile`, and returns recommended starting modules), `GET /placement-test/result` (re-reads the persisted result without retaking the test). Scoring and module recommendation are pure, DB-free functions in `app/services/placement_scoring.py`.

## Level exit exam

Finishing a level's lessons isn't enough to unlock the next one — `LevelExamService` gates progression behind a real exam. 20 questions drawn round-robin from the level's own lesson exercises (no separate exam bank to author), 70% to pass, a 15-minute timer per attempt, up to 3 attempts before a rolling 24-hour cooldown (the *last 3* attempts, so a 4th attempt after the cooldown starts a fresh window). API: `GET /levels/{level_code}/exam/status`, `POST /levels/{level_code}/exam/attempts` (idempotent while one's in progress), `POST /levels/{level_code}/exam/attempts/{attempt_id}/submit`. Passing unlocks the next `CEFRLevel`; a level is only ever gated on the *immediately preceding* one, and only if that level actually has content. A user who already has an `ExerciseAttempt` inside a level (`ExerciseRepository.has_any_attempt_in_level`) is always treated as unlocked for it, regardless of the preceding level's exam — this grandfathers anyone who started a level before its gate went live, so authoring a new level's content can never retroactively lock someone out of a level they're already using. Answers are logged as `ExerciseAttempt` rows (`source: level_exam`) for history parity with lesson practice, but — like placement-test answers — don't feed spaced repetition or mistake tracking. Frontend: `ExamPage` at `/levels/:levelCode/exam` (intro → timed batch submission → result), locked levels show on `/levels` linking to the exam that unlocks them. A separate, 5th exam spans all four levels and gates the completion certificate instead of a single level — see "Course-wide final exam and certificate" above.

## Learning intelligence

Every submitted attempt (`POST /exercises/{id}/attempts`) automatically schedules its next spaced-repetition review — for the exercise itself, and for its linked vocabulary word / grammar topic if it has one — and, for grammar-topic-tagged exercises, updates that topic's mistake status (`new` → `repeated`/`improving` → `mastered`, `app/services/mistake_classification.py`). Scheduling is a simplified SM-2 (`app/services/spaced_repetition.py`), both pure and unit-tested, deliberately isolated from the API so the algorithm can change later. API: `GET /mistakes` (optionally `?status=`), `GET /review/due`, `POST /review/{id}/complete`. Placement-test answers don't feed either system — see `docs/decisions.md`.

## AI (local model)

AI features (Phase 5, in progress) run against a locally hosted model instead of a cloud API — no per-request cost, everything stays on the machine. Setup:

1. Install [LM Studio](https://lmstudio.ai), update it to the latest version
2. Download **Qwen3.5-9B** (Q4_K_M or UD-Q4_K_XL quant) from the in-app model catalog
3. Load it and start the local server (Developer tab, default port `1234`)

`app/integrations/ai/` holds the provider abstraction: `AIProvider` (protocol), `LMStudioProvider` (talks to LM Studio's OpenAI-compatible endpoint via the `openai` SDK), and `MockAIProvider` (canned responses, used by tests — no AI-dependent test hits a real model). Config is `AI_*` in `.env.example`. Outside Docker, `AI_BASE_URL` points straight at `localhost:1234`; `docker compose` overrides it to `host.docker.internal:1234` for the `api` container, since LM Studio runs natively on the host, not in a container.

Qwen3.5 is a "thinking" model — LM Studio's API and its chat-parameters sidebar both ignore attempts to disable that, but its **My Models → (model) → Inference → Custom Fields → Enable Thinking** toggle does work. With it off, responses come back in a few seconds instead of the model exhausting its token budget on reasoning and never answering. `AI_MAX_TOKENS` (default `1500`) is still generous headroom, not a workaround. Only the final answer (`message.content`) is ever returned to callers. See `docs/decisions.md` for the full story.

## Writing feedback and homework

`AIService` (`app/services/ai_service.py`) owns prompts and response parsing on top of `AIProvider`. Prompts are versioned files under `app/integrations/ai/prompts/*_v1.md`, not inline strings.

- **Writing feedback** — `POST /api/v1/writing/feedback` takes free-text English and returns five sections (`good`/`grammar`/`vocabulary`/`natural_version`/`try_again`, per CLAUDE.md's feedback format), parsed from the model's labeled response.
- **Homework** — `POST /api/v1/homework/generate` builds 3 short writing tasks from the vocabulary/grammar of the user's most recently studied lesson (via their exercise-attempt history), respecting `learning_profiles.level_writing`. `GET /homework/{id}` reads a generated homework back with any submitted attempts. `POST /homework/{id}/tasks/{task_id}/submit` grades a submitted answer — reusing the exact same writing-feedback pipeline, since a homework answer is just English text to give feedback on.

Both are auth-gated and map AI failures to typed HTTP errors: `AIProviderUnavailableError` → 503, `AIResponseParsingError` (the model didn't follow the requested format) → 502.

## Conversation mode

Open-ended chat practice, per CLAUDE.md's "AI Conversation" flow: the AI opens with a question, the learner replies, the AI reacts naturally with no grammar corrections mid-conversation, and an analysis is generated only once the session ends.

- `POST /conversation/sessions` (optional `topic`) — AI generates the opening message.
- `POST /conversation/sessions/{id}/messages` — send a reply, get the AI's natural (uncorrected) response. 409 if the session already ended.
- `POST /conversation/sessions/{id}/end` — generates and persists the analysis (recurring mistakes, useful vocabulary, natural alternatives, grammar topics to review, recommended practice — CLAUDE.md's exact list). Idempotent: calling it again just returns the existing analysis, no second AI call.
- `GET /conversation/sessions/{id}` — the full session: messages plus analysis once ended.

Mid-conversation replies are returned as plain text, not parsed into sections — only the end-of-session analysis uses the same labeled-sections parsing as writing feedback/homework.

## Speech-to-text (STT)

The Speaking flow (CLAUDE.md's prompt → recording → STT → evaluation → feedback → retry) needs transcription; `app/integrations/stt/` mirrors the AI provider abstraction — `STTProvider` (protocol), `SpeachesProvider` (talks to [Speaches](https://github.com/speaches-ai/speaches)'s OpenAI-compatible `/v1/audio/transcriptions` endpoint via the `openai` SDK), `MockSTTProvider` (canned transcript, used by tests). Config is `STT_*` in `.env.example`.

Unlike LM Studio, Speaches is an ordinary Docker container — it's the `stt` service in `docker-compose.yml` (`ghcr.io/speaches-ai/speaches:latest-cpu`, model `Systran/faster-whisper-medium`, CPU rather than GPU to avoid contending with the LLM for the 8GB VRAM budget). `api` doesn't wait on `stt`'s health to start, only its container start — an STT outage shouldn't block the rest of the platform from booting, same principle as the typed-exception degradation on the AI side. See `docs/decisions.md` for why Speaches was chosen over Voxtral.

Speaches downloads its model on first use, not at image build time — on a fresh `speaches_models` volume, pull it once before using Speaking for real:

```bash
curl -X POST http://localhost:8001/v1/models/Systran/faster-whisper-medium
```

It's cached in the `speaches_models` volume after that, so this is a one-time step per volume, not per container restart.

## Listening audio (Kokoro-TTS)

Every lesson `listening` block and every placement-test listening item now has real synthesized
audio instead of a transcript-only placeholder — chosen over the browser's Web Speech API, which
the user tested live and rejected for quality (see `docs/decisions.md`). `app/integrations/tts/`
mirrors the STT abstraction: `TTSProvider` (protocol), `KokoroTTSProvider` (talks to
[Kokoro-FastAPI](https://github.com/remsky/Kokoro-FastAPI)'s OpenAI-compatible
`/v1/audio/speech` endpoint), `MockTTSProvider` for tests. Config is `TTS_*` in `.env.example`.
Kokoro runs as the `tts` service in `docker-compose.yml`
(`ghcr.io/remsky/kokoro-fastapi-cpu:latest`, port 8880) — an ordinary container like `stt`, same
non-health-gated `depends_on` reasoning.

Audio is generated once, offline, by `scripts/generate_audio.py` — not live per request (the
content is static between content syncs). It reads every lesson's `listening` transcript and the
placement bank's `skill: listening` items, strips speaker labels ("A: ... B: ...") into plain
narration text (Kokoro is single-voice), synthesizes each with the configured voice
(`TTS_VOICE`, default `af_bella`), and saves `content/audio/<slug>.mp3`. The resulting
`audio_url: "/audio/<slug>.mp3"` is written back into the source YAML — replacing the old "Audio
recording pending" placeholder `note` for lessons, inserted as a new `prompt` key for placement
items — the same additive-JSON-field pattern already used for `summary_ru`, so it survives the
next `sync_content` run with no schema change. A `# src-hash: <hash>` comment on that line makes
reruns idempotent: unchanged transcripts are skipped, not re-synthesized.

```bash
docker compose up -d tts
uv run python -m scripts.generate_audio          # all lessons + the placement bank
uv run python -m scripts.generate_audio --only introducing-yourself   # just one, for testing
docker compose exec api python -m scripts.sync_content   # picks up the new audio_url fields
```

Files are served by the backend at `/audio/...` (mounted via `StaticFiles` at the app root, not
under `/api/v1`, so the frontend can point an `<audio>` element straight at it) —
`frontend/src/api/client.ts`'s `assetUrl()` resolves a root-relative `audio_url` against the
backend's origin (not the full `/api/v1` base). `LessonBlockView`'s `listening` case and
`ReadingComprehensionExercise` (shared by placement-test listening items, which are
transcript-based reading-comprehension exercises tagged `skill: listening`) both render an
`<audio controls>` player when `audio_url` is present, transcript kept visible underneath as a
fallback. All 47 files (43 lessons + 4 placement items) generated and committed; verified live via
Docker-isolated Playwright — the native `<audio>` element's own `loadedmetadata` event confirmed
real, playable durations for both a lesson and all 4 placement listening items, zero console
errors.

## Russian UI translation

The interface chrome — navigation, buttons, statuses, section headings, form labels, error
messages — is in Russian throughout, as direct JSX string edits with no i18n library (no
`react-i18next`, no `t()` layer, no language toggle): this is a single-learner personal project
where the UI *is* Russian, not user-switchable, so an i18n abstraction would solve a
multi-language problem the project doesn't have (see `docs/decisions.md`). Lesson content stays
English on purpose — that's the whole point of the app — so `lesson.title`, block text, exercise
prompts, dialogue lines, vocabulary/grammar content, and AI-generated writing/speaking/conversation
feedback are all untouched. The A1/A2-Russian, B1-English-with-`RuSummary`-gloss, B2-English-only
content-immersion convention (see "Content" below) is a separate, pre-existing thing and wasn't
affected.

Translating the nav surfaced one real layout bug: Russian labels (`Ежедневный тест`, `Домашнее
задание`, `Финальный экзамен`) run longer than their English originals, and the header had no wrap
handling — the nav overflowed the viewport width and clipped the logout button off-screen. Fixed
with `flex-wrap: wrap` on `.site-header`/`.site-nav` (plus a smaller `gap`) so the nav breaks onto
a second line instead; caught live via a Docker-isolated Playwright `fullPage` screenshot coming
out wider than the configured viewport. Verified: `tsc --project tsconfig.app.json` and `oxlint`
clean, full live walkthrough (register → skip placement → dashboard → level → module → lesson →
answer all 4 exercise types → Check → logout) confirming every UI-chrome string renders in Russian
while lesson/vocabulary/dialogue content stays English and the header no longer overflows.

## Speaking

`POST /speaking/prompts` generates a short spoken-English task from the user's most recently studied lesson (same "recently studied" definition as homework), respecting `learning_profiles.level_speaking`, and creates a `SpeakingAttempt`. `POST /speaking/attempts/{id}/submit` (multipart, field `audio`) transcribes the recording via the STT provider and grades it — reusing `WritingFeedback`'s five-section shape (Good/Grammar/Vocabulary/Natural version/Try again) through a dedicated speaking prompt, since CLAUDE.md's own Speaking feedback example matches that shape exactly. `GET /speaking/attempts/{id}` reads an attempt back.

An attempt can only be submitted once — 409 on a second submit; CLAUDE.md's "retry" is a new `POST /speaking/prompts` call, not resubmitting audio. A blank/silent transcript returns 422 rather than sending empty text to the feedback prompt. Pronunciation is deliberately not assessed: a text transcript carries no pronunciation signal, and the prompt explicitly tells the model not to guess at it. Both AI and STT failures map to typed HTTP errors, same as writing feedback/homework/conversation.

Verified live end to end against real LM Studio + Speaches: a synthesized clip with deliberate past-tense mistakes ("I go to work", "I says", "she say", "We has") came back transcribed verbatim (STT doesn't "fix" the learner's grammar) and the AI feedback correctly caught and corrected all of them.

## Tests

```bash
docker compose up -d db redis
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Integration tests create and tear down their own `..._test` database — they never touch the dev database.

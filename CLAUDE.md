# CLAUDE.md — Personal English Learning Platform

## Project Mission

Build a personal interactive English-learning web application.

The application is primarily for one real user, but the architecture should remain clean enough to support multiple users later.

The main objective is NOT to build another generic language-learning website.

The objective is:

> Help the user progress from their current English level toward confident everyday reading, listening and speaking through structured lessons, interactive exercises, repetition, homework and AI-assisted conversation.

The quality of the learning experience is more important than the number of features.

---

## Core Principles

### 1. Learning effectiveness over feature count

Every feature must answer:

> How does this help the user understand, read, write or speak English better?

If there is no convincing answer, do not implement it.

### 2. Practice over passive theory

The system must not become a collection of grammar explanations and multiple-choice quizzes.

Learning flow:

```text
understand
→ see in context
→ practise
→ use
→ receive feedback
→ review later
```

### 3. Real-life English

Prefer practical situations over artificial textbook examples.

Examples:

- introducing yourself;
- talking about work;
- ordering food;
- shopping;
- travelling;
- checking into a hotel;
- asking for directions;
- talking to colleagues;
- discussing hobbies;
- gaming;
- technology;
- solving everyday problems;
- small talk;
- expressing opinions;
- talking about past events;
- making plans.

### 4. Personalisation

The system must track weaknesses instead of treating every learner identically.

If the user repeatedly makes mistakes with:

- Present Simple;
- articles;
- prepositions;
- do/does;
- irregular verbs;
- sentence structure;

those topics must influence future exercises and reviews.

---

# Technical Preferences

Use current stable versions of libraries and frameworks available when implementation starts.

Preferred stack:

- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- Docker / Docker Compose
- modern frontend framework suitable for highly interactive educational UI

Do not introduce unnecessary technologies.

Prefer simple, maintainable architecture over premature microservices.

---

# Backend Architecture

Use clear separation of concerns.

Recommended structure:

```text
app/
├── api/
├── core/
├── models/
├── schemas/
├── repositories/
├── services/
├── integrations/
├── workers/
└── main.py
```

The exact structure may evolve if a better design is justified.

Business logic must not be placed directly inside API route handlers.

Use:

```text
API → Service → Repository → Database
```

where appropriate.

External integrations belong behind dedicated integration/service abstractions.

---

# Database

Use PostgreSQL for production/development unless there is a strong reason otherwise.

Use SQLAlchemy 2.x style APIs.

Use Alembic for migrations.

Never manually modify production schema.

Potential entities:

```text
User
Course
Level
Module
Lesson
LessonBlock
Vocabulary
GrammarTopic
Exercise
ExerciseOption
ExerciseAttempt
UserProgress
UserVocabulary
UserMistake
ReviewItem
SpeakingSession
SpeakingMessage
Homework
HomeworkAttempt
```

Do not blindly create every entity.

Before implementation:

1. define responsibilities;
2. define relationships;
3. define ownership;
4. define constraints;
5. define indexes;
6. define cascade behavior;
7. then implement models.

Avoid premature over-normalisation.

---

# Course Model

Use CEFR as the conceptual framework:

```text
A1
A2
B1
B2
```

Do not implement C1/C2 during MVP.

The first content target is approximately 30–40 lessons.

Initial A1 structure:

```text
01 Introduction
02 Personal information
03 Family
04 Numbers and time
05 Daily routine
06 Food
07 Shopping
08 Home
09 City
10 Transport
11 Work
12 Hobbies
13 Weather
14 Travel
15 Revision
```

A2 should continue with increasingly complex practical situations.

---

# Lesson Model

A lesson should support blocks such as:

```text
Learning goals
Context
Vocabulary
Grammar
Examples
Exercises
Reading
Listening
Speaking
Homework
Review
```

Do not hard-code lesson content into Python.

Content must be independently editable.

Prefer a structured content format such as Markdown/YAML/JSON or a content-management layer.

The backend must not need code changes every time a new lesson is added.

---

# Exercise Engine

The system should support an extensible exercise model.

Initial types:

- multiple choice;
- single choice;
- fill in the blank;
- sentence ordering;
- matching;
- translation;
- error correction;
- reading comprehension;
- listening comprehension;
- dictation;
- writing;
- speaking.

Each exercise should have:

- unique identity;
- lesson/topic association;
- difficulty;
- expected answer or evaluation strategy;
- explanation;
- related vocabulary/grammar;
- scoring;
- attempt history.

Do not create one-off hard-coded exercise components for every exercise.

Build a reusable exercise engine.

---

# Deterministic vs AI Evaluation

Use deterministic evaluation wherever possible.

Examples:

```text
multiple choice → deterministic
fill blank → deterministic where possible
sentence ordering → deterministic
known translation → deterministic/normalised matching
```

Use AI where it adds genuine value:

```text
free writing
speaking feedback
conversation
open-ended answers
personalised explanations
additional practice generation
```

Never use an LLM for a simple deterministic answer check.

---

# Progress Tracking

Track progress separately for:

```text
Grammar
Vocabulary
Reading
Listening
Speaking
Writing
```

Also track:

- completed lessons;
- exercise attempts;
- mistakes;
- weak topics;
- vocabulary mastery;
- review history;
- speaking sessions;
- homework;
- learning time.

Do not reduce the entire learner state to one percentage.

---

# Mistake System

Implement persistent mistake tracking.

Example:

```text
Topic: Present Simple questions
Error rate: 43%
Status: weak
Next review: tomorrow
```

Repeated mistakes should influence future practice.

The system should be able to distinguish:

```text
new mistake
repeated mistake
improving
mastered
```

Avoid showing users meaningless statistics.

Statistics must lead to actionable practice.

---

# Spaced Repetition

Implement a review system for:

- vocabulary;
- phrases;
- grammar patterns;
- mistakes;
- exercises where the user performed poorly.

Do not force complete lesson repetition.

Generate targeted reviews.

The scheduling algorithm should be isolated from UI and API code so it can be changed later.

---

# Placement Test

The system should eventually provide an initial placement test.

Assess:

- grammar;
- vocabulary;
- reading;
- listening.

Speaking can be a separate diagnostic.

Example result:

```text
Estimated level: A2

Grammar: A2
Vocabulary: A2
Reading: B1
Listening: A1+
Speaking: A1+
```

Use the result to build a personalised learning path.

Do not pretend the placement test can measure everything precisely.

---

# Speaking

Speaking is a first-class learning feature, not a cosmetic AI feature.

The system should eventually support:

```text
prompt
→ user speaks
→ speech-to-text / speech analysis
→ evaluation
→ feedback
→ retry
```

Feedback should cover:

- grammar;
- vocabulary;
- completeness;
- naturalness;
- recurring mistakes;
- pronunciation where technically possible.

Avoid meaningless scores such as only:

```text
7/10
```

Prefer actionable feedback.

Example:

```text
Good:
You clearly explained your daily routine.

Grammar:
You used "do" instead of "does" twice.

Vocabulary:
Try "usually", "commute", "work from home".

Natural version:
...

Try again:
Tell me about your typical weekday in 60 seconds.
```

---

# AI Conversation

AI should behave primarily as a conversational partner during conversation mode.

Do not interrupt after every sentence with a grammar lecture.

Conversation flow:

```text
AI asks
→ user responds
→ AI reacts naturally
→ conversation continues
→ session ends
→ analysis is generated
```

After the session provide:

- recurring mistakes;
- useful vocabulary;
- natural alternatives;
- grammar topics to review;
- recommended follow-up practice.

---

# Homework

Homework should be generated or assembled from recently studied material.

Examples:

```text
Translation
Writing
Speaking
Vocabulary recall
Grammar practice
```

Homework should reinforce the current lesson rather than introduce random new material.

AI-generated homework must respect the learner's current level and recently studied vocabulary/grammar.

---

# UX

The UI should make the next learning action obvious.

Main screens:

```text
Dashboard
Course
Lesson
Exercise
Review
Vocabulary
Speaking
Homework
Progress
```

The dashboard should answer:

1. What should I do now?
2. What am I weak at?
3. What have I improved?
4. What needs review?

Avoid dashboard clutter.

---

# MVP Scope

MVP must include:

- authentication;
- course structure;
- levels;
- modules;
- lessons;
- vocabulary;
- grammar topics;
- reusable exercise engine;
- several exercise types;
- answer checking;
- attempt history;
- progress;
- mistake tracking;
- review;
- homework;
- basic AI feedback.

Do NOT build initially:

- social features;
- public leaderboards;
- marketplace;
- mobile application;
- complex gamification;
- C1/C2;
- unnecessary admin complexity;
- microservices.

---

# Development Phases

## Phase 1 — Foundation

Implement:

- repository;
- project configuration;
- Docker;
- backend;
- database;
- Alembic;
- configuration management;
- authentication;
- testing infrastructure.

Before writing large amounts of code, inspect the repository and understand the existing structure.

---

## Phase 2 — Course Engine

Implement:

- levels;
- modules;
- lessons;
- lesson blocks;
- vocabulary;
- grammar topics;
- content loading.

---

## Phase 3 — Exercises

Implement:

- exercise abstraction;
- deterministic scoring;
- exercise attempts;
- reusable frontend components;
- progress calculation.

Start with a small number of exercise types and expand only when the abstraction is stable.

---

## Phase 4 — Learning Intelligence

Implement:

- mistakes;
- weak topics;
- review items;
- spaced repetition;
- adaptive practice.

---

## Phase 5 — AI

Implement:

- writing feedback;
- homework feedback;
- conversation;
- speaking workflow.

Keep AI integrations isolated behind services/interfaces.

AI outages must not break the rest of the learning platform.

---

## Phase 6 — UX

Improve:

- dashboard;
- lesson flow;
- exercise UX;
- review center;
- progress visualization;
- speaking UI.

Do not polish every screen before the learning loop works.

---

# Testing

Tests are mandatory.

## Unit tests

Test:

- scoring;
- progress calculation;
- review scheduling;
- mistake classification;
- domain logic.

## Integration tests

Test:

- database;
- repositories;
- services;
- API endpoints.

## E2E

At minimum:

```text
register
→ placement
→ lesson
→ exercise
→ result
→ progress
→ review
```

AI-dependent functionality must be testable with mocked providers.

Do not make automated tests depend on real external AI responses.

---

# Code Quality

Follow these rules:

- type hints everywhere practical;
- clear names;
- small functions;
- explicit dependencies;
- no hidden global state;
- no duplicated business logic;
- no magic numbers without explanation;
- validation at boundaries;
- domain logic outside route handlers;
- async code where appropriate;
- proper transaction handling;
- migrations for schema changes.

Do not over-engineer.

Do not introduce abstractions until they solve an actual problem.

---

# Security

At minimum:

- secrets only through environment/configuration;
- password hashes, never plaintext passwords;
- secure authentication;
- input validation;
- authorization checks;
- rate limiting for expensive AI endpoints where appropriate;
- safe file/audio handling;
- no API keys in frontend code.

---

# Error Handling

Errors should be:

- predictable;
- typed where useful;
- logged appropriately;
- exposed to the client in safe form.

Do not leak:

- stack traces;
- secrets;
- internal database details;
- provider credentials.

---

# AI Provider Abstraction

Do not couple the whole application directly to one AI provider.

Prefer:

```text
AIService
    ↓
provider adapter
```

This should make it possible to replace the provider later.

Keep prompts versioned and inspectable.

Do not scatter huge prompts across random files.

---

# Content Quality Rules

The course content is as important as the software.

Every lesson must have:

- a clear learning objective;
- a limited vocabulary target;
- a clear grammar target when applicable;
- contextual examples;
- controlled practice;
- at least one meaningful application task.

Do not overload beginners with too many concepts in one lesson.

New vocabulary should recur in later lessons.

Grammar should be recycled rather than taught once and forgotten.

---

# Important Product Rule

The application is not successful because:

```text
the UI looks good
the database is complex
there are 500 exercise types
the AI is impressive
```

It is successful if the user can eventually:

- read English faster;
- understand more spoken English;
- formulate sentences without translating every word;
- maintain conversations;
- recognise recurring mistakes;
- communicate in real-life situations.

The product is the learning progress.

---

# Claude Code Behaviour

When working on this project:

1. First inspect the repository.
2. Read existing architecture before modifying it.
3. Check current dependency versions before adding libraries.
4. Do not rewrite working code without a reason.
5. Prefer incremental changes.
6. Run tests after meaningful changes.
7. Run linters/type checks where configured.
8. Update migrations when database models change.
9. Do not invent missing requirements silently.
10. If a requirement is ambiguous and materially affects architecture, ask before implementing.
11. If ambiguity is minor, choose the simplest reasonable implementation and document the assumption.
12. Keep the project runnable after every meaningful phase.
13. Do not add dependencies unless they solve a real problem.
14. Do not implement future phases prematurely.
15. Prioritise the smallest complete learning loop.

---

# Definition of Done

A feature is not complete merely because the code compiles.

A feature is complete when:

- implementation exists;
- relevant tests exist;
- database changes have migrations;
- API contracts are validated;
- frontend handles loading/error/success states;
- the feature works in the main user flow;
- documentation is updated when necessary;
- no obvious technical debt was introduced.

---

# First Task

Before implementing the application:

1. inspect the repository;
2. identify the existing stack;
3. identify what already exists;
4. create a concise architecture proposal;
5. propose the initial database schema;
6. propose the first MVP milestone;
7. identify risks and unresolved decisions.

Do not immediately generate hundreds of files.

After the architecture is agreed, implement Phase 1 incrementally.

The first milestone should result in a minimal but runnable application with a clean foundation for the course engine.

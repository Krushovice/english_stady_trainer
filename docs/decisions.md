# Decisions Log

Decisions made before/during Phase 0, and why. Update this file when a decision changes instead of only discussing it in chat — this is the durable record.

## Made

| Decision | Chosen | Why |
|---|---|---|
| Primary user's starting level | Not hardcoded to A1 | Self-reported B1; actual content start is computed from the Phase 3.5 placement test result, per skill. |
| Learning priorities | Travel, conversation/small talk, reading & listening comprehension prioritized; work/IT kept as a secondary, not excluded, source of topics and vocabulary | User's stated goals. Drives example/dialogue selection inside lessons (`docs/roadmap.md` → Content plan), not the underlying grammar progression, which still runs A1→A2→B1→B2. |
| AI provider | Deferred to Phase 5 | Nothing before Phase 5 depends on a specific vendor; `AIService` + adapter interface is built first, provider plugged in later. |
| Deployment | Docker Compose, fully isolated, on the local machine during development; the same stack redeployed to a VPS later | No architecture change required for the later move — only reverse proxy, TLS, and domain get added. |
| Frontend framework | React + TypeScript + Vite | **Assumption**, not explicitly requested. CLAUDE.md only specifies "a modern frontend framework suitable for highly interactive educational UI." No SSR framework needed for a single-user, auth-gated app. Cheap to change before Phase 6. |
| Dependency installation | Project virtual environment (Python) / local `node_modules` (JS) only — never system-wide | Explicit user instruction. |
| CLAUDE.md tracking | Kept local only, excluded from git | Reflects the working copy's `.gitignore`. |

## Open (deliberately not decided yet)

| Question | Decide by | Notes |
|---|---|---|
| Concrete AI provider(s) and model(s) | Phase 5 | Claude API, OpenAI, or both behind one adapter. |
| STT/TTS provider for Speaking | Phase 5 | Independent from the main AI provider decision — e.g. Anthropic has no first-party STT, so Speaking may need a second vendor regardless of who does text feedback. |
| VPS host, region, domain | Around the Phase 6 deployment step | Doesn't block any earlier phase — local Compose is provider-agnostic. |

## Risks

- **Content authoring is the real bottleneck, not code.** The exercise/lesson engine can be finished quickly; writing 30–40 good lessons with real-life examples takes much longer than building the system that renders them. Plan for this explicitly rather than treating content as an afterthought once Phase 3 is "done."
- **AI cost/latency risk deferred, not eliminated.** Because provider selection moves to Phase 5, there's no early signal on per-request cost for writing/speaking feedback. Revisit rate-limit defaults once a provider is chosen instead of guessing now.
- **Speaking (STT + pronunciation feedback) is the most technically uncertain feature** in the whole spec — latency, accuracy, and provider cost are all open. Treat it as the highest-risk item in Phase 5, not something to bolt on last-minute.
- **Scope creep.** CLAUDE.md is exhaustive; the phase plan (`docs/roadmap.md`) exists specifically so "do not implement future phases prematurely" has a concrete checklist to point back to, not just a principle to remember.

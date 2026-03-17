# Project State: MINIAS Refactor

## Status
**Current Phase:** Phase 1 — Plan 01 complete
**Current Plan:** 1 of 1 (Phase 1)
**Overall Progress:** ██░░░░░░░░ ~5%

## Session Log
- 2025-03-17: Phase 1 context gathered → `.planning/phases/01-package-scaffold-leaf-models/01-CONTEXT.md`
- 2026-03-17: Phase 1 Plan 01 executed — minias/ package created, 5 dataclasses extracted
- Resume: Next phase/plan execution

## Project Reference
See: .planning/PROJECT.md (updated 2025-03-17)
**Core value:** Navigable, maintainable codebase — identical behavior and appearance
**Current focus:** Phase 1 — Package Scaffold & Leaf Models

## Phase Status
| Phase | Name | Status | Plans |
|-------|------|--------|-------|
| 1 | Package Scaffold & Leaf Models | In Progress | 1/1 |
| 2 | Service Module Extraction | Pending | 0/0 |
| 3 | Dialogs, App Shell & Entry Point | Pending | 0/0 |
| 4 | Bug Fixes & Dead Code Removal | Pending | 0/0 |
| 5 | Deduplication & Code Quality | Pending | 0/0 |
| 6 | Method Decomposition | Pending | 0/0 |

## Requirement Coverage
- **Total v1 requirements:** 28
- **Mapped to phases:** 28
- **Unmapped:** 0

| Category | Count | Phase(s) |
|----------|-------|----------|
| STRUCT (1-11) | 11 | 1, 2, 3 |
| BUGF (1-4) | 4 | 4 |
| DEAD (1-4) | 4 | 4 |
| DEDUP (1-3) | 3 | 5 |
| QUAL (1-3) | 3 | 5 |
| METH (1-3) | 3 | 6 |

## Key Context

Critical information for any agent picking up this project:

1. **No test suite exists.** Manual smoke testing after every extraction is the only safety net. The 8-point smoke test: launch app, open limits dialog, browse results, test serial panel, export Excel, generate PDF, change COM settings, verify INI save.

2. **Two-pass discipline.** Phases 1-3 are pure structural moves (copy-paste + import). No logic changes, no bug fixes, no deduplication during extraction. Phases 4-6 are the cleanup pass.

3. **Bottom-up order.** Models first (no deps), then services (depend on models), then dialogs (depend on services), then app (depends on everything). This prevents circular imports and keeps the app working at every step.

4. **Entry point change is the critical moment.** Phase 3 changes `pyproject.toml` — must run `uv sync` and verify `uv run minias` immediately.

5. **The old monolith `minias_app.py` stays working until Phase 3 is complete.** During Phases 1-2, the monolith imports from extracted modules but remains the entry point.

6. **SQLite threading is unsafe but must not be changed.** `check_same_thread=False` with no locking. Document it, don't fix it — it's out of scope (ARCH-01 is v2).

7. **File paths are relative to CWD.** `minias.db`, `resources/form.xlsx`, `MINIAS.INI` — these must not change. No `__file__`-relative path rewrites.

## Decisions Log

| Phase | Decision | Rationale |
|-------|----------|-----------|
| 01-01 | Removed `from dataclasses import dataclass, field` from monolith | `@dataclass` no longer used anywhere in monolith after extraction |
| 01-01 | Placed local import after third-party try/except blocks | Follows project import ordering convention (stdlib → third-party → local) |

## Performance Metrics

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 01-01 | 4min | 3 | 4 |

---
*Last updated: 2026-03-17 after Phase 1 Plan 01 execution*

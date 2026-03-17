---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 4
current_plan: 2 of 2
status: in-progress
last_updated: "2026-03-17T05:18:00Z"
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 8
  completed_plans: 7
---

# Project State: MINIAS Refactor

## Status
**Current Phase:** 4
**Current Plan:** 2 of 2 (04-02 complete, 04-01 pending)
**Overall Progress:** ███████░░░ ~70%

## Session Log
- 2025-03-17: Phase 1 context gathered → `.planning/phases/01-package-scaffold-leaf-models/01-CONTEXT.md`
- 2026-03-17: Phase 1 Plan 01 executed — minias/ package created, 5 dataclasses extracted
- 2026-03-17: Phase 2 Plan 01 executed — SerialCommunicator + TestCalculator extracted to minias/
- 2026-03-17: Phase 2 Plan 02 executed — MiniasDatabase extracted to minias/database.py
- 2026-03-17: Phase 2 Plan 03 executed — ExcelExporter + CertificateGenerator extracted; Phase 2 complete
- 2026-03-17: Phase 3 Plan 01 executed — LimitsDialog + SettingsDialog extracted to minias/dialogs.py
- 2026-03-17: Phase 3 Plan 02 executed — MiniasApp moved to minias/app.py, entry point updated, monolith dissolved; Phase 3 complete
- 2026-03-17: Phase 4 Plan 02 executed — 4 dead code items removed (get_samples, send_command, EXCEL_SETUP, template_path)

## Project Reference
See: .planning/PROJECT.md (updated 2025-03-17)
**Core value:** Navigable, maintainable codebase — identical behavior and appearance
**Current focus:** Phase 4 in progress (04-02 dead code removal done, 04-01 bug fixes pending)

## Phase Status
| Phase | Name | Status | Plans |
|-------|------|--------|-------|
| 1 | Package Scaffold & Leaf Models | Complete | 1/1 |
| 2 | Service Module Extraction | Complete | 3/3 |
| 3 | Dialogs, App Shell & Entry Point | Complete | 2/2 |
| 4 | Bug Fixes & Dead Code Removal | In Progress | 1/2 |
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
| 02-01 | Kept inline imports inside methods during extraction | Two-pass discipline: no refactoring during extraction |
| 02-02 | Removed `import sqlite3` from monolith | Only used within MiniasDatabase class, no other references in remaining code |
| 02-03 | Changed CertificateGenerator.script_dir to os.getcwd() | Module relocated to minias/ — __file__-relative paths would break resource resolution |
| 03-02 | Added hatchling build-system to pyproject.toml | uv sync skips entry point installation without [build-system] — required for `uv run minias` |
| 03-02 | Kept minias_app.py as compatibility shim | Preserves backward compat for `python minias_app.py` direct execution |
| 04-02 | Removed 4 confirmed-dead items in 2 atomic commits | Grouped by file for clean history |

## Performance Metrics

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 01-01 | 4min | 3 | 4 |
| 02-01 | 7min | 2 | 4 |
| 02-02 | 6min | 2 | 3 |
| 02-03 | 8min | 2 | 4 |
| 03-02 | 8min | 2 | 5 |
| 04-02 | 3min | 2 | 3 |

---
*Last updated: 2026-03-17 after Phase 4 Plan 02 execution — dead code removal complete*


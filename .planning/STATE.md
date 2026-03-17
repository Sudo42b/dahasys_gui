---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 06
current_plan: Not started
status: unknown
last_updated: "2026-03-17T06:44:00.615Z"
progress:
  total_phases: 6
  completed_phases: 6
  total_plans: 12
  completed_plans: 12
---

# Project State: MINIAS Refactor

## Status
**Current Phase:** 06
**Current Plan:** Not started
**Overall Progress:** [██████████] 100%

## Session Log
- 2025-03-17: Phase 1 context gathered → `.planning/phases/01-package-scaffold-leaf-models/01-CONTEXT.md`
- 2026-03-17: Phase 1 Plan 01 executed — minias/ package created, 5 dataclasses extracted
- 2026-03-17: Phase 2 Plan 01 executed — SerialCommunicator + TestCalculator extracted to minias/
- 2026-03-17: Phase 2 Plan 02 executed — MiniasDatabase extracted to minias/database.py
- 2026-03-17: Phase 2 Plan 03 executed — ExcelExporter + CertificateGenerator extracted; Phase 2 complete
- 2026-03-17: Phase 3 Plan 01 executed — LimitsDialog + SettingsDialog extracted to minias/dialogs.py
- 2026-03-17: Phase 3 Plan 02 executed — MiniasApp moved to minias/app.py, entry point updated, monolith dissolved; Phase 3 complete
- 2026-03-17: Phase 4 Plan 02 executed — 4 dead code items removed (get_samples, send_command, EXCEL_SETUP, template_path)
- 2026-03-17: Phase 5 Plan 01 executed — safe_get closures consolidated, port lists deduplicated, inline imports removed
- 2026-03-17: Phase 5 Plan 02 executed — stop-save dedup, unit conversion centralized, configparser INI; Phase 5 complete
- 2026-03-17: Phase 6 Plan 01 executed — _create_gui() + _init_tables() decomposed in app.py and database.py
- 2026-03-17: Phase 6 Plan 02 executed — CertificateGenerator.generate() decomposed into 5 sub-methods

## Project Reference
See: .planning/PROJECT.md (updated 2025-03-17)
**Core value:** Navigable, maintainable codebase — identical behavior and appearance
**Current focus:** Phase 6 Plan 02 complete. Certificate generate() decomposed.

## Phase Status
| Phase | Name | Status | Plans |
|-------|------|--------|-------|
| 1 | Package Scaffold & Leaf Models | Complete | 1/1 |
| 2 | Service Module Extraction | Complete | 3/3 |
| 3 | Dialogs, App Shell & Entry Point | Complete | 2/2 |
| 4 | Bug Fixes & Dead Code Removal | Complete | 2/2 |
| 5 | Deduplication & Code Quality | Complete | 2/2 |
| 6 | Method Decomposition | In Progress | 2/2 |

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
| 05-01 | _safe_get as module-level function, not class method | No dependency on self — pure function of row, column_names, and lookup params |
| 05-01 | FALLBACK_PORTS[:4] in _get_port_list() | Preserves original shorter 4-port fallback behavior |
| 05-02 | configparser with VB6 INI adapter | VB6 [Key]=Value format incompatible with standard configparser sections |
| 05-02 | format_2sigma_microns() distinct from format_microns() | 2sigma display (* 2000) is different from simple micron (* 1000) |
| 05-02 | INI path CWD-relative, not __file__-relative | Matches project convention; __file__ resolves to minias/ after Phase 3 move |
| 06-01 | _create_status_bar includes check_frame and Test Results label | Natural visual grouping between input panel and result grid |
| 06-01 | _create_measure_tables has only MEASURES table | MEASURES_REGISTERED not in current schema — only 8 tables total |
| 06-02 | Styles dict (not tuple) for sub-method style passing | Named access cleaner than positional — styles["title"] vs styles[0] |
| 06-02 | Extracted _build_z_table as separate method | Keeps _build_data_table under 100 lines |

## Performance Metrics

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 01-01 | 4min | 3 | 4 |
| 02-01 | 7min | 2 | 4 |
| 02-02 | 6min | 2 | 3 |
| 02-03 | 8min | 2 | 4 |
| 03-02 | 8min | 2 | 5 |
| 04-02 | 3min | 2 | 3 |
| 05-01 | 5min | 2 | 3 |
| 05-02 | 8min | 2 | 4 |
| 06-01 | 3min | 2 | 2 |
| 06-02 | 3min | 1 | 1 |

---
*Last updated: 2026-03-17 after Phase 6 Plan 02 execution*


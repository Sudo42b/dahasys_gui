# MINIAS Refactor

## What This Is

Refactoring the MINIAS Probe Testing System — a Python/Tkinter/SQLite desktop application that re-implements a VB6 legacy probe testing system. The current codebase is a ~3064-line monolithic single file (`minias_app.py`) that handles serial communication with measurement probes, stores test results in SQLite, and exports reports to Excel/PDF. The goal is to split this into well-organized modules by responsibility and clean up code quality, while preserving identical behavior and appearance.

## Core Value

The application must continue to work exactly as it does today — serial probe testing workflow, database operations, and report generation — while becoming navigable and maintainable through modular file organization.

## Requirements

### Validated

<!-- Existing capabilities confirmed working in the current monolith. -->

- ✓ Serial communication with measurement probes (CR-terminated protocol) — existing
- ✓ Test orchestration (multi-axis, multi-cycle probe testing workflow) — existing
- ✓ SQLite database for operators, codes, setup, limits, test results — existing
- ✓ Statistical calculations (sigma, range, mean, pass/fail evaluation) — existing
- ✓ Excel export of test results — existing
- ✓ PDF certificate generation with company logo — existing
- ✓ INI config file for serial port settings — existing
- ✓ Tkinter GUI matching VB6 original layout (figs/demo.png) — existing
- ✓ Limits editing dialog — existing
- ✓ COM port settings dialog with port detection — existing
- ✓ Operator and code management (add/delete) — existing
- ✓ Test result browsing by ID — existing

### Active

<!-- Refactoring scope. -->

- [ ] Split monolithic minias_app.py into logical modules by responsibility
- [ ] Extract data models into dedicated models.py
- [ ] Extract database layer into database.py
- [ ] Extract serial communication into serial_comm.py
- [ ] Extract test calculation logic into calculator.py
- [ ] Extract Excel export into excel_export.py
- [ ] Extract PDF certificate generation into certificate.py
- [ ] Extract dialog classes into dialogs.py (or individual files)
- [ ] Clean up duplicated code (safe_get x4, stop-and-save duplication, fallback patterns)
- [ ] Fix identified bugs (indentation bug in _on_print_certificate, undefined self.tree_results, duplicate imports, unused imports)
- [ ] Remove dead code (unused get_samples, send_command, EXCEL_SETUP table, unused configparser import)
- [ ] Centralize unit conversion (raw mm ↔ microns ↔ 2-sigma display)
- [ ] Move inline imports (time, re) to module top-level
- [ ] Break up long methods (_create_gui 207 lines, _init_tables 134 lines, generate() 305 lines)
- [ ] Create proper Python package structure with __init__.py
- [ ] Ensure app launches and runs identically after refactor (uv run minias)

### Out of Scope

- Adding a test suite — deferred to future work
- Changing the UI layout or appearance — must match figs/demo.png
- Database schema changes — existing minias.db must remain compatible
- Adding new features (notifications, new export formats, etc.) — pure refactor
- MVC/MVP architecture — too heavy; splitting by responsibility is sufficient
- Rewriting the test thread/GUI interaction pattern — functional change, not structural

## Context

- **Origin:** VB6 legacy program (MINIAS.EXE, MSCOMM32.OCX, Minias.mdb) converted to Python
- **Current state:** Working single-file app (~3064 lines), version 1.0.0
- **Pain point:** Hard to navigate — finding and changing things in a 3000-line file is painful
- **Code quality issues identified:**
  - `safe_get()` duplicated 4 times as nested closures
  - Stop-and-save logic duplicated between two methods
  - `MiniasApp` is a god class (1273 lines, 41.6% of codebase)
  - Indentation bug in `_on_print_certificate()` causes logic errors
  - `self.tree_results` referenced but never defined (would crash)
  - `configparser` imported but never used (INI parsed manually)
  - Duplicate reportlab imports inside method + module level
  - Scattered unit conversion logic (mm ↔ microns) with no central utility
  - `check_same_thread=False` on SQLite with no locking (race condition risk)

## Constraints

- **UI Appearance**: GUI must remain visually identical to figs/demo.png (VB6 original)
- **DB Compatibility**: Existing minias.db data must continue to work — no schema changes
- **Tech Stack**: Python >= 3.10, Tkinter, SQLite, pyserial, openpyxl, reportlab
- **Entry Point**: `uv run minias` must continue to work (pyproject.toml scripts entry)
- **Graceful Degradation**: Optional imports (serial, openpyxl, reportlab) must keep try/except + feature flag pattern

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Split by responsibility, not MVC layers | Simpler structure for a desktop app; matches the existing section banners | — Pending |
| No tests in this round | Focus on structural cleanup only; tests are a separate effort | — Pending |
| Minor improvements OK | Fix obvious bugs found during refactor (indentation, dead code) | — Pending |
| Keep single package (not nested packages) | Flat module structure is sufficient for ~3000 lines | — Pending |

---
*Last updated: 2025-03-17 after initialization*

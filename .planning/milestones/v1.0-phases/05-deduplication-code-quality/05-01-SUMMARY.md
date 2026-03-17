---
phase: 05-deduplication-code-quality
plan: 01
subsystem: database, serial, dialogs
tags: [deduplication, code-quality, refactoring, python]

# Dependency graph
requires:
  - phase: 02-service-module-extraction
    provides: "database.py, serial_comm.py, dialogs.py extracted modules"
provides:
  - "Single _safe_get helper in database.py replacing 4 duplicated closures"
  - "FALLBACK_PORTS constant in dialogs.py replacing 3 inline port lists"
  - "Clean module-level imports in serial_comm.py (no inline imports)"
affects: [06-method-decomposition]

# Tech tracking
tech-stack:
  added: []
  patterns: [module-level-helper-function, module-level-constant]

key-files:
  created: []
  modified:
    - minias/database.py
    - minias/dialogs.py
    - minias/serial_comm.py

key-decisions:
  - "_safe_get placed as module-level function (not class method) since it has no dependency on self"
  - "FALLBACK_PORTS[:4] used in _get_port_list() to preserve the original shorter 4-port fallback behavior"

patterns-established:
  - "Module-level helper for row-level DB column lookup with graceful fallback"
  - "Module-level constants for repeated literal lists"

requirements-completed: [DEDUP-01, DEDUP-03, QUAL-02]

# Metrics
duration: 5min
completed: 2026-03-17
---

# Phase 5 Plan 01: Simple Deduplication & Import Cleanup Summary

**Consolidated 4 safe_get closures into single _safe_get helper, 3 fallback port lists into FALLBACK_PORTS constant, and removed 3 redundant inline imports**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-17T05:39:56Z
- **Completed:** 2026-03-17T05:45:22Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Eliminated 4 duplicated safe_get closure definitions in database.py, replaced with single module-level _safe_get function
- Consolidated 3 inline COM port fallback lists in dialogs.py into one FALLBACK_PORTS constant
- Removed 3 redundant inline imports (time, re) from serial_comm.py methods — module-level imports already existed

## Task Commits

Each task was committed atomically:

1. **Task 1: Consolidate safe_get closures in database.py** - `ad68928` (refactor)
2. **Task 2a: Consolidate fallback port list in dialogs.py** - `6482f0c` (refactor)
3. **Task 2b: Remove inline imports in serial_comm.py** - `c415d64` (refactor)

## Files Created/Modified
- `minias/database.py` - Added module-level _safe_get(); removed 4 closure definitions in get_codes, get_code_info, get_limits, get_test_result
- `minias/dialogs.py` - Added FALLBACK_PORTS constant; replaced 3 inline port lists
- `minias/serial_comm.py` - Removed 3 inline imports (import time as _time, import re, import time); replaced _time.sleep with time.sleep

## Decisions Made
- _safe_get placed as module-level function (not class method) since it has no dependency on self — it only needs row, column_names, and lookup params
- FALLBACK_PORTS[:4] used in _get_port_list() to preserve the original shorter 4-port fallback behavior (may have been intentional for that specific context)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plan 01 complete, ready for Plan 02 (method extraction helpers, app.py inline import cleanup)
- All 3 modules (database.py, dialogs.py, serial_comm.py) verified working after changes

---
*Phase: 05-deduplication-code-quality*
*Completed: 2026-03-17*

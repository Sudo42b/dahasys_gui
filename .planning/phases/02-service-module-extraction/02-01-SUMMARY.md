---
phase: 02-service-module-extraction
plan: 01
subsystem: serial, calculator
tags: [pyserial, statistics, serial-communication, test-calculation, module-extraction]

# Dependency graph
requires:
  - phase: 01-package-scaffold-leaf-models
    provides: minias/ package with models.py (LimitInfo used by TestCalculator)
provides:
  - SerialCommunicator class in minias/serial_comm.py with SERIAL_AVAILABLE flag
  - TestCalculator class in minias/calculator.py
affects: [02-02, 02-03, 03-01]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Leaf service extraction — zero-internal-dependency classes first"
    - "Feature flag co-location — SERIAL_AVAILABLE lives with its try/except in serial_comm.py"

key-files:
  created:
    - minias/serial_comm.py
    - minias/calculator.py
  modified:
    - minias_app.py
    - minias/__init__.py

key-decisions:
  - "Kept inline imports (import re, import time) inside methods where original had them — no refactoring during extraction"

patterns-established:
  - "Service modules follow same convention as models: module docstring, imports, single class"
  - "Feature flags (SERIAL_AVAILABLE, etc.) co-locate with their try/except import block in the module that owns the dependency"

requirements-completed: [STRUCT-04, STRUCT-05]

# Metrics
duration: 7min
completed: 2026-03-17
---

# Phase 2 Plan 1: Service Module Extraction Summary

**SerialCommunicator + SERIAL_AVAILABLE extracted to minias/serial_comm.py, TestCalculator extracted to minias/calculator.py — ~293 lines removed from monolith**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-17T03:31:59Z
- **Completed:** 2026-03-17T03:39:19Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- SerialCommunicator class (232 lines) extracted to minias/serial_comm.py with SERIAL_AVAILABLE flag
- TestCalculator class (65 lines) extracted to minias/calculator.py with LimitInfo import from minias.models
- Monolith reduced from ~2985 to 2692 lines (~293 lines removed)
- minias/__init__.py updated with re-exports for both classes

## Task Commits

Each task was committed atomically:

1. **Task 1: Extract SerialCommunicator to minias/serial_comm.py** - `4b37519` (feat)
2. **Task 2: Extract TestCalculator to minias/calculator.py** - `3a71728` (feat)

## Files Created/Modified
- `minias/serial_comm.py` - SerialCommunicator class + SERIAL_AVAILABLE try/except flag (232 lines)
- `minias/calculator.py` - TestCalculator class with statistics and LimitInfo imports (65 lines)
- `minias_app.py` - Removed both class definitions and SERIAL_AVAILABLE block, added imports from new modules
- `minias/__init__.py` - Added re-exports for SerialCommunicator, SERIAL_AVAILABLE, TestCalculator

## Decisions Made
- Kept inline `import re`, `import time`, `import sys` inside methods where the original code had them — no refactoring during extraction (two-pass discipline)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both leaf service classes extracted, ready for Plan 02 (Database extraction) and Plan 03 (ExcelExporter + PdfExporter)
- minias_app.py is at 2692 lines, still the entry point with MiniasDatabase, ExcelExporter, PdfExporter, and MiniasApp remaining

---
*Phase: 02-service-module-extraction*
*Completed: 2026-03-17*

---
phase: 05-deduplication-code-quality
plan: 02
subsystem: code-quality
tags: [configparser, unit-conversion, deduplication, refactoring]

requires:
  - phase: 05-deduplication-code-quality
    provides: "Plan 01 completed simple deduplication and inline import cleanup"
provides:
  - "Deduplicated stop-and-save logic via _finalize_incomplete_axes() helper"
  - "Centralized unit conversion functions in models.py (mm_to_microns, microns_to_mm, format_microns, format_2sigma_microns)"
  - "configparser-based INI parsing with VB6 format preservation"
affects: [06-method-decomposition]

tech-stack:
  added: [configparser]
  patterns: [VB6 INI adapter pattern, centralized unit conversion]

key-files:
  created: []
  modified:
    - minias/models.py
    - minias/app.py
    - minias/dialogs.py
    - minias/excel_export.py

key-decisions:
  - "Used configparser with VB6 INI adapter (_parse_vb6_ini/_write_vb6_ini) since VB6 [Key]=Value format is non-standard"
  - "Added format_2sigma_microns() alongside format_microns() since 2sigma display pattern (*2000) is distinct from microns (*1000)"
  - "Left certificate.py _fmt_micron as-is since it handles string formatting differently (appends 'micron' text)"
  - "Fixed INI path from __file__-relative to CWD-relative to match project convention"

patterns-established:
  - "VB6 INI adapter: _parse_vb6_ini() strips [] brackets, maps to synthetic MINIAS section for configparser"
  - "Unit conversion: use mm_to_microns/microns_to_mm/format_microns from models.py instead of inline * 1000"

requirements-completed: [DEDUP-02, QUAL-01, QUAL-03]

duration: 8min
completed: 2026-03-17
---

# Phase 5 Plan 02: Complex Deduplication & Code Quality Summary

**Deduplicated stop-and-save logic via shared helper, centralized mm↔micron conversion in models.py, replaced manual INI parsing with configparser VB6 adapter**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-17T05:50:45Z
- **Completed:** 2026-03-17T05:59:11Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Extracted `_finalize_incomplete_axes()` helper eliminating 30+ lines of duplicated stop-save logic between `_on_stop()` and `_stop_and_save_current()`
- Created 4 unit conversion functions (`mm_to_microns`, `microns_to_mm`, `format_microns`, `format_2sigma_microns`) in models.py, replacing scattered `* 1000` / `/ 1000.0` across 3 modules
- Rewrote `_load_config()` and `_save_config()` using configparser with VB6 INI format adapter, preserving all extra keys and round-trip fidelity
- Moved `import time` and `import stat` from inline to module level in app.py
- Fixed INI path from `os.path.dirname(__file__)` (broken after module move) to CWD-relative `"MINIAS.INI"`

## Task Commits

Each task was committed atomically:

1. **Task 1: Deduplicate stop-and-save logic and centralize unit conversion** - `f272815` (refactor)
2. **Task 2: Replace manual INI parsing with configparser** - `cc3abee` (refactor)

## Files Created/Modified
- `minias/models.py` - Added mm_to_microns, microns_to_mm, format_microns, format_2sigma_microns utility functions
- `minias/app.py` - Extracted _finalize_incomplete_axes(), replaced unit conversions, configparser INI parsing, module-level imports
- `minias/dialogs.py` - Replaced * 1000 / / 1000.0 with format_microns/microns_to_mm calls
- `minias/excel_export.py` - Replaced * 2000 / * 1000 with format_2sigma_microns/format_microns calls

## Decisions Made
- Used configparser with custom VB6 adapter because VB6 INI format `[Key]=Value` is incompatible with standard configparser sections — adapter strips brackets and uses synthetic `[MINIAS]` section
- Added `format_2sigma_microns()` as distinct function since 2sigma display (`* 2000`) is a different operation from simple micron conversion (`* 1000`)
- Left certificate.py's `_fmt_micron` helper unchanged — it appends "micron" text which is domain-specific formatting, not pure conversion
- Fixed INI path from `__file__`-relative (broken since Phase 3 module relocation) to CWD-relative `"MINIAS.INI"` per project convention

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed INI path using __file__ in _save_config too**
- **Found during:** Task 2 (configparser rewrite)
- **Issue:** Both _load_config and _save_config used `os.path.dirname(__file__)` which resolves to `minias/` instead of project root after Phase 3 module relocation
- **Fix:** Changed both to use `"MINIAS.INI"` (CWD-relative)
- **Files modified:** minias/app.py
- **Verification:** Round-trip test passes — reads 7 keys from MINIAS.INI, values match expected
- **Committed in:** cc3abee (Task 2 commit)

**2. [Rule 2 - Missing Critical] Moved import stat to module level**
- **Found during:** Task 2 (configparser rewrite)
- **Issue:** `import stat` was inline inside _save_config() — inconsistent with QUAL-02 scope (inline imports should be module-level)
- **Fix:** Moved to module-level imports alongside other stdlib imports
- **Files modified:** minias/app.py
- **Verification:** No inline `import stat` in function body
- **Committed in:** cc3abee (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both fixes improve correctness and consistency. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 5 complete — all deduplication and code quality improvements done
- Ready for Phase 6: Method Decomposition

---
*Phase: 05-deduplication-code-quality*
*Completed: 2026-03-17*

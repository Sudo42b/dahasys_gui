---
phase: 03-dialogs-app-shell-entry-point
plan: 02
subsystem: app-shell
tags: [tkinter, entry-point, package-structure, hatchling]

# Dependency graph
requires:
  - phase: 03-01
    provides: "LimitsDialog and SettingsDialog extracted to minias/dialogs.py"
provides:
  - "minias/app.py with MiniasApp class and main() function"
  - "Proper package entry point via minias.app:main"
  - "python -m minias support via __main__.py"
  - "Backward-compatible shim at minias_app.py"
affects: [04-bug-fixes-dead-code]

# Tech tracking
tech-stack:
  added: [hatchling]
  patterns: [package-entry-point, compatibility-shim]

key-files:
  created:
    - minias/app.py
  modified:
    - minias/__init__.py
    - minias/__main__.py
    - minias_app.py
    - pyproject.toml

key-decisions:
  - "Added hatchling build-system to enable proper entry point installation via uv"
  - "Kept minias_app.py as compatibility shim instead of deleting it"

patterns-established:
  - "Package entry point: minias.app:main via pyproject.toml [project.scripts]"
  - "Compatibility shim pattern for backward-compatible module moves"

requirements-completed: [STRUCT-09, STRUCT-10, STRUCT-11]

# Metrics
duration: 8min
completed: 2026-03-17
---

# Phase 3 Plan 02: App Shell & Entry Point Summary

**MiniasApp class + main() moved to minias/app.py, pyproject.toml entry point changed to minias.app:main, monolith dissolved to 7-line shim**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-17T04:31:39Z
- **Completed:** 2026-03-17T04:39:52Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Moved MiniasApp class (~1274 lines) and main() to minias/app.py — pure structural move, zero logic changes
- Updated pyproject.toml from `minias_app:main` to `minias.app:main` with proper hatchling build-system
- Converted 1316-line monolith minias_app.py to a 7-line compatibility shim
- Verified all 10 package modules import correctly + shim works

## Task Commits

Each task was committed atomically:

1. **Task 1: Move MiniasApp and main() to minias/app.py and update entry points** - `c2741cc` (feat)
2. **Task 2: Comprehensive verification** - verification-only, no commit needed

## Files Created/Modified
- `minias/app.py` - Main GUI application class (MiniasApp) and entry point (main)
- `minias/__init__.py` - Added MiniasApp and main re-exports
- `minias/__main__.py` - Updated to import from minias.app (was minias_app)
- `minias_app.py` - Converted to 7-line compatibility shim
- `pyproject.toml` - Updated entry point + added hatchling build-system

## Decisions Made
- **Added hatchling build-system:** `uv sync` was skipping entry point installation without a `[build-system]` — added hatchling with `packages = ["minias"]` to enable proper `uv run minias` support
- **Kept minias_app.py as shim:** Preserves backward compatibility for anyone running `python minias_app.py` directly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added hatchling build-system to pyproject.toml**
- **Found during:** Task 1 (uv sync after entry point change)
- **Issue:** `uv sync` warned "Skipping installation of entry points because this project is not packaged" — `uv run minias` would not work without a build-system
- **Fix:** Added `[build-system]` with hatchling and `[tool.hatch.build.targets.wheel]` with `packages = ["minias"]`
- **Files modified:** pyproject.toml
- **Verification:** `uv sync` builds package successfully, `uv run minias` resolves
- **Committed in:** c2741cc (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for entry point to work. No scope creep — hatchling is the standard minimal build backend.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 complete — monolith fully dissolved into 10-module package
- All structural extraction (Phases 1-3) is done
- Ready for Phase 4: Bug Fixes & Dead Code Removal (cleanup pass begins)

---
*Phase: 03-dialogs-app-shell-entry-point*
*Completed: 2026-03-17*

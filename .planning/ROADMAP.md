# Roadmap: MINIAS Refactor

**Created:** 2025-03-17
**Phases:** 6
**Requirements:** 28
**Granularity:** Standard

---

## Phase 1: Package Scaffold & Leaf Models

**Goal:** Create the `minias/` package structure and extract the zero-dependency dataclass models as the first module.

**Requirements:** STRUCT-01, STRUCT-02
**Plans:** 1/1 plans complete

Plans:
- [x] 01-01-PLAN.md — Create package scaffold + extract 5 dataclasses to models.py

### Success Criteria
1. `minias/` directory exists with `__init__.py` (version string only) and `__main__.py` (stub that calls existing `main()`)
2. `minias/models.py` contains all 5 dataclasses (TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo) with identical field definitions
3. `minias_app.py` imports from `minias.models` instead of defining dataclasses locally
4. App launches and runs via `uv run python minias_app.py` — no behavioral change

### Notes
- models.py is the universal leaf of the dependency DAG — nothing depends on it failing
- Keep `minias_app.py` as the entry point for now; the pyproject.toml change comes in Phase 3
- Diffs should be mechanically simple: new file with classes, old file with classes replaced by imports
- Smoke test: launch app, open limits dialog, browse a test result

---

## Phase 2: Service Module Extraction

**Goal:** Extract all five service/backend classes (database, serial, calculator, excel, certificate) into dedicated modules following the bottom-up dependency order.

**Requirements:** STRUCT-03, STRUCT-04, STRUCT-05, STRUCT-06, STRUCT-07
**Plans:** 3/3 plans complete

Plans:
- [x] 02-01-PLAN.md — Extract serial_comm.py + calculator.py (leaf modules)
- [ ] 02-02-PLAN.md — Extract database.py (largest extraction)
- [ ] 02-03-PLAN.md — Extract excel_export.py + certificate.py (export modules)

### Success Criteria
1. Each of the 5 modules exists under `minias/` and contains exactly the class extracted from the monolith, with identical logic
2. Each module manages its own optional-import feature flag (e.g., `SERIAL_AVAILABLE` in `serial_comm.py`)
3. `minias_app.py` imports all 5 classes from `minias.*` modules instead of defining them locally
4. App launches and runs identically — serial communication, database operations, Excel export, and PDF certificate generation all function as before

### Notes
- **Extraction order within this phase matters:** serial_comm.py (no deps) → calculator.py (models) → database.py (models) → excel_export.py (models) → certificate.py (models)
- database.py is the largest extraction (~300 lines) and medium risk — keep `safe_get` as-is during extraction (dedup comes in Phase 5)
- Each extraction = one plan + smoke test. Do NOT batch multiple extractions into one commit
- Preserve `check_same_thread=False` pattern in database.py — do not add locking

---

## Phase 3: Dialogs, App Shell & Entry Point

**Goal:** Extract dialog classes, move the remaining MiniasApp into `minias/app.py`, and wire the new package entry point so `uv run minias` works through the package.

**Requirements:** STRUCT-08, STRUCT-09, STRUCT-10, STRUCT-11
**Plans:** 2 plans

Plans:
- [ ] 03-01-PLAN.md — Extract LimitsDialog + SettingsDialog to minias/dialogs.py
- [ ] 03-02-PLAN.md — Move MiniasApp to minias/app.py, update entry point, dissolve monolith

### Success Criteria
1. `minias/dialogs.py` contains LimitsDialog and SettingsDialog with correct imports from sibling modules
2. `minias/app.py` contains MiniasApp class and `main()` function — the monolith's original `minias_app.py` is now an empty shim or deleted
3. `pyproject.toml` scripts entry updated to `minias = "minias.app:main"`
4. `uv run minias` launches the app successfully through the new package structure
5. All GUI functionality works: probe testing workflow, limits editing, COM port settings, result browsing, Excel/PDF export

### Notes
- This is the highest-risk phase — entry point change + final monolith dissolution
- Run `uv sync` after pyproject.toml change before testing
- The old `minias_app.py` can be kept as a compatibility shim (`from minias.app import main; main()`) or deleted
- Dialogs depend on models, database, and serial_comm — all already extracted in prior phases
- After this phase, the monolith is fully dissolved. All subsequent phases are internal improvements

---

## Phase 4: Bug Fixes & Dead Code Removal

**Goal:** Fix the 4 known bugs and remove 4 pieces of dead code identified during research — all in the newly extracted modules.

**Requirements:** BUGF-01, BUGF-02, BUGF-03, BUGF-04, DEAD-01, DEAD-02, DEAD-03, DEAD-04
**Plans:** 1/2 plans executed

Plans:
- [ ] 04-01-PLAN.md — Fix 4 bugs (indentation, tree_results, duplicate imports, unused import)
- [ ] 04-02-PLAN.md — Remove 4 dead code items (get_samples, send_command, EXCEL_SETUP, template_path)

### Success Criteria
1. `_on_print_certificate()` indentation bug is fixed — cancelling the file dialog no longer executes certificate generation logic
2. `_on_delete_result()` references `self.tree` (not undefined `self.tree_results`) — delete result works without crash
3. No duplicate imports exist in any module (reportlab imports consolidated; unused `configparser` import removed)
4. Dead methods removed: `get_samples()` from database.py, `send_command()` from serial_comm.py
5. EXCEL_SETUP table creation removed from `_init_tables()` (or moved to a clearly-marked legacy section)
6. Unused `template_path` parameter removed from ExcelExporter constructor

### Notes
- These are all safe, isolated fixes with clear before/after behavior
- Bug fixes should be in separate commits from dead code removal for clean git history
- BUGF-01 (indentation bug) is a genuine logic error — test the certificate generation path carefully
- BUGF-02 (tree_results) may not have been hit in production if delete-result is rarely used

---

## Phase 5: Deduplication & Code Quality

**Goal:** Consolidate duplicated code patterns and improve code quality across the extracted modules.

**Requirements:** DEDUP-01, DEDUP-02, DEDUP-03, QUAL-01, QUAL-02, QUAL-03

### Success Criteria
1. A single `safe_get()` function exists (in `database.py` or a `utils.py`) — no duplicated closures remain anywhere
2. Stop-and-save logic exists in one canonical method, called by both `_on_stop()` and `_stop_and_save_current()`
3. Fallback port list and code info fallback patterns are consolidated (no copy-paste variants)
4. Unit conversion functions (`mm_to_microns`, `microns_to_display`, etc.) exist in a central location and are used consistently
5. All inline imports (`time`, `re`) moved to module-level (except graceful degradation try/except)
6. INI config parsing uses `configparser` properly instead of manual string parsing

### Notes
- DEDUP-01 (safe_get) is straightforward — define once, import everywhere
- DEDUP-02 (stop-and-save) requires careful analysis of what differs between the two methods
- QUAL-03 (configparser) replaces the manual INI parsing — verify the parsed values match exactly
- QUAL-01 (unit conversion) may require tracing all mm/micron math to ensure no conversion is missed

---

## Phase 6: Method Decomposition

**Goal:** Break up the three oversized methods into focused, well-named sub-methods for readability and navigability.

**Requirements:** METH-01, METH-02, METH-03

### Success Criteria
1. `_create_gui()` is decomposed into 4+ named builder methods (`_create_toolbar`, `_create_input_panel`, `_create_status_bar`, `_create_grid`, etc.) — no single method exceeds ~80 lines
2. `CertificateGenerator.generate()` is decomposed into logical sub-methods (header, body, table, footer, etc.) — no single method exceeds ~80 lines
3. `_init_tables()` is decomposed into per-table or per-group methods — no single method exceeds ~80 lines
4. All decomposed methods are private (underscore-prefixed) and called only from their parent method
5. App launches and runs identically — GUI layout unchanged, certificates render identically, database initializes correctly

### Notes
- This is the lowest-risk phase — purely internal restructuring within existing modules
- `_create_gui()` decomposition should follow the existing comment sections as natural split points
- `generate()` decomposition in certificate.py should produce the same PDF output byte-for-byte (or visually identical)
- `_init_tables()` can be split into one method per table or grouped logically (core tables, result tables, config tables)

---

## Phase Dependency Graph

```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
(scaffold)  (services) (app shell) (bugfix)  (dedup)   (decomp)
```

Phases 4, 5, and 6 could theoretically be parallelized since they touch different concerns, but sequential execution is safer given the absence of a test suite.

---
*Last updated: 2025-03-17*

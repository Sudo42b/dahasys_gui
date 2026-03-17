# Requirements: MINIAS Refactor

**Defined:** 2025-03-17
**Core Value:** Make the codebase navigable and maintainable by splitting the monolith into logical modules

## v1 Requirements

Requirements for this refactoring round. Each maps to roadmap phases.

### Structural Extraction

- [x] **STRUCT-01**: Create `minias/` package directory with `__init__.py` and `__main__.py`
- [x] **STRUCT-02**: Extract 5 dataclasses (TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo) into `minias/models.py`
- [x] **STRUCT-03**: Extract MiniasDatabase class into `minias/database.py`
- [x] **STRUCT-04**: Extract SerialCommunicator class into `minias/serial_comm.py`
- [x] **STRUCT-05**: Extract TestCalculator class into `minias/calculator.py`
- [x] **STRUCT-06**: Extract ExcelExporter class into `minias/excel_export.py`
- [x] **STRUCT-07**: Extract CertificateGenerator class into `minias/certificate.py`
- [ ] **STRUCT-08**: Extract LimitsDialog and SettingsDialog into `minias/dialogs.py`
- [x] **STRUCT-09**: Move remaining MiniasApp class and main() into `minias/app.py`
- [x] **STRUCT-10**: Update pyproject.toml scripts entry to `minias.app:main`
- [x] **STRUCT-11**: App launches and runs identically via `uv run minias` after restructure

### Code Deduplication

- [x] **DEDUP-01**: Consolidate 4 duplicated `safe_get()` closures into a single utility function
- [x] **DEDUP-02**: Deduplicate stop-and-save logic between `_on_stop()` and `_stop_and_save_current()`
- [x] **DEDUP-03**: Consolidate duplicated fallback port list and code info fallback patterns

### Bug Fixes

- [ ] **BUGF-01**: Fix indentation bug in `_on_print_certificate()` that causes logic errors when file dialog is cancelled
- [ ] **BUGF-02**: Fix undefined `self.tree_results` reference in `_on_delete_result()` (should be `self.tree`)
- [ ] **BUGF-03**: Remove duplicate reportlab imports inside `CertificateGenerator.generate()` (already imported at module level)
- [ ] **BUGF-04**: Remove unused `configparser` import and other unused imports

### Dead Code Removal

- [x] **DEAD-01**: Remove unused `get_samples()` method from database class
- [x] **DEAD-02**: Remove unused `send_command()` method from SerialCommunicator
- [x] **DEAD-03**: Remove EXCEL_SETUP table creation code (table is created but never read/written)
- [x] **DEAD-04**: Remove unused `template_path` parameter from ExcelExporter constructor

### Method Decomposition

- [ ] **METH-01**: Break `_create_gui()` (207 lines) into focused builder methods (_create_toolbar, _create_input_panel, _create_status_bar, _create_grid, etc.)
- [ ] **METH-02**: Break `CertificateGenerator.generate()` (305 lines) into logical sub-methods
- [ ] **METH-03**: Break `_init_tables()` (134 lines) into smaller, focused methods

### Code Quality

- [x] **QUAL-01**: Centralize unit conversion logic (raw mm to microns to 2-sigma display) into utility functions
- [x] **QUAL-02**: Move inline imports (`time`, `re`) to module top-level where they belong
- [x] **QUAL-03**: Replace manual INI parsing with proper `configparser` usage

## v2 Requirements

Deferred to future work. Tracked but not in current roadmap.

### Testing

- **TEST-01**: Add pytest test suite for database module
- **TEST-02**: Add pytest tests for calculator module
- **TEST-03**: Add pytest tests for export modules
- **TEST-04**: Add integration test for full test workflow

### Architecture

- **ARCH-01**: Introduce proper thread safety for SQLite (connection locking)
- **ARCH-02**: Decouple test orchestration from GUI (extract test workflow state machine)
- **ARCH-03**: Add type annotations to all public methods missing them

## Out of Scope

| Feature | Reason |
|---------|--------|
| MVC/MVP architecture | Over-engineering for a desktop app; splitting by responsibility is sufficient |
| UI layout changes | Must remain visually identical to figs/demo.png |
| Database schema changes | Existing minias.db must remain compatible |
| New features (export formats, etc.) | Pure refactor — no functional additions |
| Thread safety fixes | Unsafe but working; changing threading model risks regressions |
| Tkinter mixin classes | Adds complexity without navigational benefit |
| Sub-package nesting | Flat package sufficient for ~3000 lines |
| Class renaming | Breaks muscle memory and grep patterns for no benefit |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| STRUCT-01 | Phase 1 | Complete |
| STRUCT-02 | Phase 1 | Complete |
| STRUCT-03 | Phase 2 | Complete |
| STRUCT-04 | Phase 2 | Complete |
| STRUCT-05 | Phase 2 | Complete |
| STRUCT-06 | Phase 2 | Complete |
| STRUCT-07 | Phase 2 | Complete |
| STRUCT-08 | Phase 3 | Pending |
| STRUCT-09 | Phase 3 | Complete |
| STRUCT-10 | Phase 3 | Complete |
| STRUCT-11 | Phase 3 | Complete |
| DEDUP-01 | Phase 5 | Complete |
| DEDUP-02 | Phase 5 | Complete |
| DEDUP-03 | Phase 5 | Complete |
| BUGF-01 | Phase 4 | Pending |
| BUGF-02 | Phase 4 | Pending |
| BUGF-03 | Phase 4 | Pending |
| BUGF-04 | Phase 4 | Pending |
| DEAD-01 | Phase 4 | Complete |
| DEAD-02 | Phase 4 | Complete |
| DEAD-03 | Phase 4 | Complete |
| DEAD-04 | Phase 4 | Complete |
| METH-01 | Phase 6 | Pending |
| METH-02 | Phase 6 | Pending |
| METH-03 | Phase 6 | Pending |
| QUAL-01 | Phase 5 | Complete |
| QUAL-02 | Phase 5 | Complete |
| QUAL-03 | Phase 5 | Complete |

**Coverage:**
- v1 requirements: 28 total
- Mapped to phases: 28
- Unmapped: 0

---
*Requirements defined: 2025-03-17*
*Last updated: 2025-03-17 — phase mapping complete*

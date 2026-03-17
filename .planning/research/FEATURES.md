# Code Quality Features for MINIAS Refactor

Research on what structural qualities and code organization features to target
when splitting a ~3000-line Python/Tkinter monolith into modules.

---

## Table Stakes (must-have for maintainability)

These are non-negotiable. Without them, the refactor doesn't achieve its goal of
making the codebase navigable and maintainable.

### 1. Single Responsibility per module

Each `.py` file should own one concern. A developer looking for "how does serial
communication work" should open exactly one file, not scroll through 3064 lines.

**Current problem:** Everything lives in `minias_app.py`. The file already has
section banners (`# === 데이터 모델 ===`, `# === 데이터베이스 모듈 ===`) that mark
where modules should be — the banners are the extraction guide.

**Target:** 7-9 modules, each 100-500 lines. No module exceeds ~600 lines. The
existing class boundaries (`MiniasDatabase`, `SerialCommunicator`, `TestCalculator`,
`ExcelExporter`, `CertificateGenerator`, `MiniasApp`, `LimitsDialog`,
`SettingsDialog`) already define the splits.

### 2. No duplicated logic

Identical or near-identical code blocks must be extracted into a single shared
function.

**Current problem:** `safe_get()` is defined as a nested closure 4 separate times
(lines 346, 386, 500, 590) with minor signature variations. The stop-and-save
calculation loop is duplicated between `_on_stop()` (line 2308-2337) and
`_stop_and_save_current()` (line 2356-2385) — 30 lines of nearly identical axis
result computation.

**Target:**
- One `safe_get()` as a module-level or class-level method in the database module
- One `_finalize_pending_axes()` method that both stop paths call
- Zero copy-pasted blocks longer than 3 lines

### 3. No dead code

Unused functions, imports, and unreachable code must be removed.

**Current problem:**
- `configparser` imported (line 16) but INI is parsed manually — never used
- `get_samples()` method exists but is never called
- `send_command()` method exists but is never called
- `EXCEL_SETUP` table created but never read or written
- Duplicate `reportlab` imports (module-level + inside method)

**Target:** Every import is used. Every function is called. Every table is either
used or explicitly documented as reserved for future use.

### 4. No known bugs

Bugs discovered during analysis must be fixed during refactor, not carried forward.

**Current problem:**
- **Indentation bug in `_on_print_certificate()`** (line 2420-2443): The `if not
  result:` check at line 2424 runs outside the `if file_path:` block due to wrong
  indentation. If the user cancels the file dialog, `result` is undefined and the
  method crashes. The `try:` block starting at line 2443 is also indented under
  `if code_info is None` instead of being at the method level.
- **`self.tree_results`** referenced at lines 2483-2484 but never defined as an
  instance attribute — will crash at runtime if that code path is reached.

**Target:** Zero known bugs. Both issues fixed as part of extracting the relevant
code into its new module.

### 5. No god classes

No single class should hold >40% of the codebase or have >30 public methods.

**Current problem:** `MiniasApp` is 1273 lines (41.6% of the file). It handles
GUI construction, event handling, test orchestration, serial data processing,
result saving, navigation, and button state management. It has ~40+ methods.

**Target:** `MiniasApp` delegates to collaborator objects (which it already
partially does via `self.db`, `self.serial`, `self.calculator`, etc.). After
extracting dialogs and moving the remaining long methods into the appropriate
modules, the main app class should be under 800 lines and focused on GUI wiring
and event dispatch.

### 6. No methods exceeding ~80 lines

Long methods are hard to understand, test, and modify.

**Current problem:**
- `_create_gui()`: 207 lines of widget construction
- `_init_tables()`: 134 lines of CREATE TABLE statements
- `generate()` (CertificateGenerator): 305 lines of PDF construction

**Target:** Break each into named sub-methods:
- `_create_gui()` → `_create_menu_bar()`, `_create_control_panel()`,
  `_create_results_table()`, `_create_status_bar()`, etc.
- `_init_tables()` → individual `_create_X_table()` methods or a list of SQL
  strings executed in a loop
- `generate()` → `_build_header()`, `_build_results_table()`,
  `_build_footer()`, etc.

### 7. Imports at module top-level

All imports should be at the top of the file, not buried inside methods.

**Current problem:** `import time` and `import re` appear inside method bodies
as inline imports. `reportlab` components are imported both at module level and
again inside `generate()`.

**Target:** All imports at the top of their respective module file. The only
exception is the existing graceful degradation pattern (`try: import serial`)
which is correct and should be preserved.

### 8. Thread-safe database access

Cross-thread database access must be explicitly safe.

**Current problem:** `check_same_thread=False` is set on the SQLite connection
(line 151) but there is no locking mechanism. The test thread writes results
while the GUI thread reads — this is a data race.

**Target:** Add a `threading.Lock` to `MiniasDatabase` that wraps all
`cursor.execute()` calls involving writes, or document the access pattern if
analysis shows reads and writes are actually serialized through the queue.

---

## Differentiators (nice-to-have quality improvements)

These would make the codebase notably clean but aren't strictly required for the
refactor to succeed. Implement opportunistically during the split.

### 1. Centralized unit conversion

A single utility module or set of functions for mm ↔ microns ↔ 2-sigma display
conversions. Currently this math is scattered across the test processing,
display updates, and export logic with magic multipliers (`* 1000`, `* 2`).

A `units.py` with `mm_to_microns()`, `microns_to_mm()`, and
`to_two_sigma_display()` would eliminate an entire class of subtle bugs.

### 2. Consistent error handling pattern

Standardize on: GUI-facing methods use `messagebox`, internal methods raise
exceptions or return `Optional`/sentinel values. Currently it's a mix — some
methods print errors, some show messageboxes, some do both.

### 3. Type completeness on all public interfaces

The codebase already uses type hints on most method signatures. Completing
coverage on the remaining untyped methods and adding return types everywhere
would enable future mypy adoption.

### 4. Dataclass validation

Add `__post_init__` validation to dataclasses where invalid data could cause
downstream failures (e.g., `naxis` must be 1-5, `test_type` must be one of
the known values). Currently dataclasses accept any values silently.

### 5. Constants module

Extract magic numbers and repeated string literals into named constants:
axis names, test types (`"ST"`, `"ND"`), baud rates, default limits,
column name mappings. Currently these are scattered as string literals
throughout the code.

### 6. Docstrings on all public methods

The codebase has Korean docstrings on most methods but some are missing.
Full coverage would help future developers (and AI tools) understand intent.

### 7. Package `__init__.py` with clean public API

The `__init__.py` should re-export the main entry point and key classes so
that the package structure is clear:
```python
from .app import MiniasApp
from .database import MiniasDatabase
```

---

## Anti-Features (things to deliberately NOT do)

These are temptations that would derail the refactor or make the code worse.
Each is a real risk given this project's context.

### 1. Do NOT introduce MVC/MVP/MVVM architecture

The PROJECT.md explicitly marks this out of scope. A desktop Tkinter app with
one main window and two dialogs does not benefit from a formal architecture
pattern. Splitting by responsibility (which the code already naturally does)
is sufficient. Adding view-models, controllers, or observer patterns would
add abstraction layers that no one will navigate.

### 2. Do NOT create deep package hierarchies

`minias/gui/widgets/panels/control_panel.py` is worse than
`minias/gui.py`. For ~3000 lines split into 7-9 files, a flat package
(`minias/`) is correct. Nested packages are justified at ~10,000+ lines.

### 3. Do NOT add abstract base classes or interfaces

There is one database implementation (SQLite), one serial implementation,
one calculator. Creating `AbstractDatabase`, `ISerialCommunicator`, or
`BaseExporter` adds code that serves no purpose — there are no alternative
implementations and none are planned.

### 4. Do NOT refactor the test thread/GUI interaction pattern

The current pattern (background thread + `queue.Queue` + `root.after()` polling)
works and is the standard Tkinter threading approach. Rewriting it to use
asyncio, concurrent.futures, or a different event system is a functional
change, not a structural one, and risks introducing new bugs in the most
critical code path.

### 5. Do NOT change the database schema

Existing `minias.db` files must continue to work. Do not rename columns,
normalize tables, add foreign key constraints, or remove the `EXCEL_SETUP`
table (even though it's unused — it may exist in production databases).
Schema cleanup is a separate project that requires data migration tooling.

### 6. Do NOT add a test suite in this round

Tests are valuable but are a separate effort. Writing tests while
simultaneously moving code between files means tests would be written against
interfaces that are still in flux. Refactor first, stabilize the module
boundaries, then add tests.

### 7. Do NOT optimize performance

No profiling, no caching layers, no connection pooling, no lazy loading.
The app processes one measurement at a time over serial at human-interactive
speeds. Performance is not a problem and "optimizing" it adds complexity
for zero user benefit.

### 8. Do NOT change the UI appearance

The GUI must remain visually identical to `figs/demo.png`. Do not modernize
widget styles, rearrange layouts, add new buttons, or switch to ttk-themed
widgets unless the original VB6 UI already uses that style. The refactor is
internal only.

### 9. Do NOT add configuration management beyond what exists

The app reads `MINIAS.INI` for serial port settings. Do not add YAML/TOML
config files, environment variable support, or a settings framework. The
`configparser` import should be removed (it's unused), not expanded.

### 10. Do NOT scope-creep into new features

If you notice "it would be nice if the app could also..." — stop. Write it
down in a separate document if you want, but do not implement it. The refactor
PR should contain zero new features. Every behavioral change is a risk to
the "identical functionality" requirement.

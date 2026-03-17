# Architecture Research: Module Decomposition Plan

## 1. Recommended Module Layout

```
minias/
    __init__.py          # Package init, re-exports main() for entry point
    models.py            # Dataclasses: TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo
    database.py          # MiniasDatabase class
    serial_comm.py       # SerialCommunicator class + SERIAL_AVAILABLE flag
    calculator.py        # TestCalculator class
    excel_export.py      # ExcelExporter class + EXCEL_AVAILABLE flag
    certificate.py       # CertificateGenerator class + PDF_AVAILABLE flag
    dialogs.py           # LimitsDialog, SettingsDialog classes
    app.py               # MiniasApp class (main GUI), main() entry point
```

### What goes where

| Module | Contents | Lines (est.) |
|--------|----------|-------------|
| `models.py` | `TestResult`, `AxisResult`, `CodeInfo`, `SetupInfo`, `LimitInfo` dataclasses | ~80 |
| `database.py` | `MiniasDatabase` class (connect, _init_tables, all CRUD methods) | ~640 |
| `serial_comm.py` | `SerialCommunicator` class, `SERIAL_AVAILABLE` flag | ~220 |
| `calculator.py` | `TestCalculator` class (sigma, range, mean, evaluate) | ~60 |
| `excel_export.py` | `ExcelExporter` class, `EXCEL_AVAILABLE` flag | ~70 |
| `certificate.py` | `CertificateGenerator` class, `PDF_AVAILABLE` flag | ~320 |
| `dialogs.py` | `LimitsDialog`, `SettingsDialog` classes | ~310 |
| `app.py` | `MiniasApp` class, `main()` function | ~1280 |
| `__init__.py` | `from minias.app import main` (one line) | ~5 |

### Why a package, not flat modules

The current `pyproject.toml` entry point is `minias_app:main`. After refactoring,
it becomes `minias:main` (via `__init__.py` re-export). This requires renaming the
file `minias_app.py` to a `minias/` package directory. The `pyproject.toml` change:

```toml
[project.scripts]
minias = "minias:main"
```

### Alternative considered: flat modules without package

Placing `models.py`, `database.py`, etc. at the repo root avoids the package overhead
but pollutes the top-level directory and makes imports awkward (`import models` instead
of `from minias.models import TestResult`). Rejected.

---

## 2. Dependency Graph

### Directed Acyclic Graph (DAG)

```
app.py
  |
  +------> dialogs.py
  |          |
  |          +------> database.py -----> models.py
  |          +------> serial_comm.py
  |          +------> models.py
  |
  +------> database.py -----> models.py
  +------> serial_comm.py
  +------> calculator.py -----> models.py
  +------> excel_export.py ---> models.py
  +------> certificate.py ----> models.py
  +------> models.py
```

### As import statements

```python
# models.py — LEAF (no internal imports)
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

# database.py — depends on: models
from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo

# serial_comm.py — LEAF (no internal imports)
import queue, threading
# (uses pyserial with try/except)

# calculator.py — depends on: models
from minias.models import LimitInfo

# excel_export.py — depends on: models
from minias.models import TestResult, AxisResult

# certificate.py — depends on: models
from minias.models import TestResult, AxisResult, CodeInfo

# dialogs.py — depends on: models, database, serial_comm
from minias.models import LimitInfo
from minias.database import MiniasDatabase
from minias.serial_comm import SerialCommunicator

# app.py — depends on: ALL other modules (root of the DAG)
from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo
from minias.database import MiniasDatabase
from minias.serial_comm import SerialCommunicator, SERIAL_AVAILABLE
from minias.calculator import TestCalculator
from minias.excel_export import ExcelExporter
from minias.certificate import CertificateGenerator
from minias.dialogs import LimitsDialog, SettingsDialog
```

### Module classification

| Role | Modules | Rule |
|------|---------|------|
| **Leaf** (zero internal deps) | `models.py`, `serial_comm.py` | Nothing inside the package imports these modules' peers |
| **Near-leaf** (depend only on models) | `database.py`, `calculator.py`, `excel_export.py`, `certificate.py` | Import only `models.py` |
| **Mid-tier** (depend on models + services) | `dialogs.py` | Imports `models.py`, `database.py`, `serial_comm.py` |
| **Root** (imports everything) | `app.py` | The only module that sees the whole package |

### Why serial_comm.py is a leaf

`SerialCommunicator` uses only stdlib (`queue`, `threading`, `time`, `re`) and
`pyserial`. It does not reference any dataclass or database type. It returns raw
`float` values. This makes it fully independent.

### Why dialogs.py is mid-tier

`LimitsDialog` takes a `MiniasDatabase` instance and a `LimitInfo` dataclass.
`SettingsDialog` takes a config `Dict` and uses `SerialCommunicator.get_available_ports()`.
These dependencies are unavoidable without introducing unnecessary abstractions.

---

## 3. Refactoring Order

Extract modules bottom-up from the DAG. Each step leaves the app fully working.

### Step 1: Extract `models.py` (leaf)

**Why first:** Zero dependencies. Every other module needs these types. Extracting
them first creates the shared vocabulary for all subsequent extractions.

**What moves:**
- Lines 62-135: `TestResult`, `AxisResult`, `CodeInfo`, `SetupInfo`, `LimitInfo`
- The `datetime`, `dataclasses`, `typing` imports they use

**Verification:** `from minias.models import TestResult` works. App starts.

### Step 2: Extract `serial_comm.py` (leaf)

**Why second:** Also zero internal dependencies. The `SerialCommunicator` class
references no dataclass — it returns `Optional[float]`. Self-contained.

**What moves:**
- Lines 777-995: `SerialCommunicator` class
- Lines 19-25: `SERIAL_AVAILABLE` flag and `serial` import
- The `queue`, `threading` imports it uses

**Verification:** `from minias.serial_comm import SerialCommunicator, SERIAL_AVAILABLE` works.

### Step 3: Extract `calculator.py` (near-leaf)

**Why third:** Depends only on `LimitInfo` from `models.py` (already extracted).
Tiny module, easy win.

**What moves:**
- Lines 1002-1058: `TestCalculator` class
- The `statistics` import

**Verification:** Calculator tests pass (manual). App starts.

### Step 4: Extract `database.py` (near-leaf)

**Why fourth:** Depends only on `models.py`. Largest single extraction (~634 lines).
After this, `app.py` shrinks significantly.

**What moves:**
- Lines 142-775: `MiniasDatabase` class
- The `sqlite3` import

**Special concern:** The `safe_get()` closure is duplicated 4 times inside this class.
During extraction, deduplicate it into a module-level `_safe_get(row, col_names, name, alt_name=None, default=None)` helper function at the top of `database.py`.

**Verification:** Database CRUD operations work. App starts and loads data.

### Step 5: Extract `excel_export.py` (near-leaf)

**Why fifth:** Depends only on `models.py`. Small, self-contained.

**What moves:**
- Lines 1066-1131: `ExcelExporter` class
- Lines 29-35: `EXCEL_AVAILABLE` flag and `openpyxl` import

**Verification:** Excel export works from the app.

### Step 6: Extract `certificate.py` (near-leaf)

**Why sixth:** Depends only on `models.py`. Contains inline `reportlab` imports
(duplicate of module-level imports) — clean these up during extraction.

**What moves:**
- Lines 1139-1451: `CertificateGenerator` class
- Lines 38-54: `PDF_AVAILABLE` flag and `reportlab` imports

**Note:** Remove the duplicate `from reportlab...` imports inside `generate()` method
(lines 1160-1172). Keep only the module-level try/except block.

**Verification:** PDF generation works.

### Step 7: Extract `dialogs.py` (mid-tier)

**Why seventh:** Depends on `models.py`, `database.py`, `serial_comm.py` — all
already extracted.

**What moves:**
- Lines 2739-3049: `LimitsDialog`, `SettingsDialog` classes

**Verification:** Limits and Settings dialogs open and function correctly.

### Step 8: Create package structure

**What happens:**
1. Create `minias/` directory
2. Move all extracted modules into it
3. Create `minias/__init__.py` with `from minias.app import main`
4. Rename the remaining `minias_app.py` content to `minias/app.py`
5. Update `pyproject.toml` entry point
6. Delete old `minias_app.py`

**Verification:** `uv run minias` launches the app.

### Summary table

| Step | Module | Depends on | Lines moved | Risk |
|------|--------|-----------|-------------|------|
| 1 | `models.py` | (nothing) | ~80 | Minimal |
| 2 | `serial_comm.py` | (nothing) | ~220 | Minimal |
| 3 | `calculator.py` | models | ~60 | Minimal |
| 4 | `database.py` | models | ~640 | Medium (largest extraction, safe_get cleanup) |
| 5 | `excel_export.py` | models | ~70 | Minimal |
| 6 | `certificate.py` | models | ~320 | Low (duplicate import cleanup) |
| 7 | `dialogs.py` | models, database, serial_comm | ~310 | Low |
| 8 | Package creation | all | structural | Medium (entry point change) |

---

## 4. Circular Import Prevention

### Strategy 1: Models as the universal leaf

`models.py` defines all shared data types (`TestResult`, `AxisResult`, `CodeInfo`,
`SetupInfo`, `LimitInfo`). Every other module imports FROM models, but models imports
NOTHING from the package.

```python
# models.py — ONLY stdlib imports, never:
# from minias.database import ...   ← FORBIDDEN
# from minias.app import ...        ← FORBIDDEN
```

This is the single most important rule. If a type needs to be shared, it goes in
`models.py`.

### Strategy 2: GUI imports everything, nothing imports GUI

`app.py` is the convergence point — it imports all service modules. But no service
module ever imports from `app.py` or `dialogs.py`.

```
app.py → database.py    ✅
app.py → serial_comm.py ✅
database.py → app.py    ❌ NEVER
calculator.py → app.py  ❌ NEVER
```

### Strategy 3: Dialogs depend downward only

`dialogs.py` needs `MiniasDatabase` and `SerialCommunicator` because:
- `LimitsDialog.__init__` takes `db: MiniasDatabase` and `limits: LimitInfo`
- `SettingsDialog` calls `SerialCommunicator.get_available_ports()`

This is acceptable because dialogs are UI components that sit between `app.py` and
service modules. The key constraint: **dialogs never import from app.py**.

```
app.py → dialogs.py → database.py → models.py   ✅ (chain, no cycle)
dialogs.py → app.py                               ❌ NEVER
```

### Strategy 4: Feature flags stay with their module

Each optional-import flag lives in the module that uses it:

```python
# serial_comm.py
SERIAL_AVAILABLE = False  # set True if import serial succeeds

# excel_export.py
EXCEL_AVAILABLE = False   # set True if import openpyxl succeeds

# certificate.py
PDF_AVAILABLE = False     # set True if import reportlab succeeds
```

`app.py` imports these flags:
```python
from minias.serial_comm import SERIAL_AVAILABLE
from minias.excel_export import EXCEL_AVAILABLE
from minias.certificate import PDF_AVAILABLE
```

This avoids a central "flags" module that everything would import and that
could create tight coupling.

### Strategy 5: No TYPE_CHECKING imports needed

For this codebase, all cross-module type references are concrete runtime
dependencies (database methods return `TestResult`, calculator takes `LimitInfo`).
There are no cases where a type is needed only for annotations but not at
runtime. Therefore, `from __future__ import annotations` and `TYPE_CHECKING`
blocks are unnecessary complexity — skip them.

### Danger zones to watch

| Scenario | Risk | Mitigation |
|----------|------|------------|
| `database.py` importing `SerialCommunicator` for some reason | Cycle via `dialogs.py` | database.py has no serial dependency. Keep it that way. |
| `certificate.py` importing `MiniasDatabase` to fetch data | Would add an unnecessary dependency | Pass data as arguments (already the case: `generate(result, axis_results, ...)`) |
| Adding a "utils" module imported by both `models.py` and `database.py` | Potential coupling | Only add utils if truly needed. Currently `safe_get` is database-internal. |

---

## 5. God Class Decomposition: MiniasApp

The `MiniasApp` class is 1273 lines with 41 methods. It handles GUI construction,
event handling, test orchestration, data loading, config management, and printing.

### Current method inventory (grouped by responsibility)

```
INIT & CONFIG (4 methods, ~135 lines)
  __init__             31 lines  — Component wiring, state vars, tk vars
  _load_config         32 lines  — INI file parsing
  _save_config         47 lines  — INI file writing
  _load_initial_data   25 lines  — Load codes, operators, setup, limits from DB

GUI CONSTRUCTION (2 methods, ~210 lines)
  _create_gui         207 lines  — Build all widgets
  _init_grid_rows      12 lines  — Reset treeview rows

DATA MANAGEMENT (7 methods, ~150 lines)
  _on_code_selected     7 lines
  _on_add_code         14 lines
  _on_del_code         13 lines
  _on_add_operator      8 lines
  _on_del_operator     13 lines
  _refresh_id_list      5 lines
  _on_id_selected       7 lines

RESULT LOADING & DISPLAY (2 methods, ~90 lines)
  _on_load_id          48 lines  — Serial/ID search with multi-result dialog
  _load_test_result    48 lines  — Load and display a saved test result

TEST ORCHESTRATION (8 methods, ~400 lines)
  _on_start            63 lines  — Validate inputs, connect serial, start thread
  _run_test           130 lines  — Background test loop (axis/cycle)
  _on_pause            10 lines
  _on_stop             55 lines  — Stop + partial save
  _stop_and_save       40 lines  — Duplicate of stop logic
  _complete_test       90 lines  — Calculate overall results, save to DB
  _update_grid_row_live 16 lines
  _update_grid_row     15 lines

PRINTING & EXPORT (3 methods, ~100 lines)
  _on_print_certificate 60 lines — Save PDF dialog
  _on_print_direct      50 lines — Print via OS viewer
  _on_delete_result     35 lines — Delete test record

SETTINGS & EXIT (4 methods, ~35 lines)
  _on_settings           2 lines
  _apply_settings        6 lines
  _on_limits             4 lines
  _on_exit              10 lines
  _reset_buttons         2 lines
  run                    3 lines
```

### Recommended decomposition: Composition, not inheritance

Do NOT split `MiniasApp` via multiple inheritance or mixin classes. Tkinter's
single-root widget hierarchy makes mixins fragile. Instead, use **internal
coordinator objects** that receive references to shared state.

#### Phase 1: Extract `_create_gui` into builder functions (during refactor)

The 207-line `_create_gui` method builds 5 distinct UI sections. Break it into
private methods within `MiniasApp`:

```python
class MiniasApp:
    def _create_gui(self):
        self._build_toolbar()       # btn_frame: Start, Stop, Save PDF, Print, Settings, Exit
        self._build_input_panel()   # input_frame: Probe Type, Code, Serial, Operator, ID lookup
        self._build_status_bar()    # status_frame: cyan status display
        self._build_options_bar()   # check_frame: Limits, Check options, NAxis/NCycles
        self._build_results_grid()  # grid_frame: Treeview + scrollbar
        self._build_footer()        # statusbar at bottom

    def _build_toolbar(self):
        """상단 버튼 프레임 생성"""
        btn_frame = ttk.Frame(self.root, padding="5")
        btn_frame.pack(fill=tk.X)
        self.btn_start = ttk.Button(btn_frame, text="Start", ...)
        # ... ~30 lines

    def _build_input_panel(self):
        """입력 프레임 생성"""
        # ... ~60 lines

    # etc.
```

This alone reduces `_create_gui` from 207 lines to ~10 lines, and each builder
method is ~30-60 lines.

#### Phase 2: Deduplicate stop-and-save logic

`_on_stop()` (lines 2290-2347) and `_stop_and_save_current()` (lines 2349-2389)
contain nearly identical code for calculating partial axis results. Extract the
shared logic:

```python
def _finalize_partial_axes(self):
    """현재까지 측정 데이터가 있는 축의 결과를 계산하여 axis_results에 추가"""
    for axis, values in self.measurements.items():
        if not values:
            continue
        if any(ar.axis == axis for ar in self.axis_results):
            continue

        sigma = self.calculator.calculate_sigma(values)
        range_val = self.calculator.calculate_range(values)

        axis_result_str = "OK"
        if self.limits:
            axis_result_str = self.calculator.evaluate_axis_result(
                sigma, range_val, self.limits,
                self.var_check_sigma.get(), self.var_check_range.get(),
            )

        self.axis_results.append(AxisResult(
            axis=axis, sigma=sigma, range_val=range_val,
            result=axis_result_str, ncycles=len(values), direction=str(axis),
        ))

def _on_stop(self):
    # ... confirm dialog ...
    self.is_testing = False
    self.is_paused = False
    self._finalize_partial_axes()
    if self.axis_results:
        self._complete_test()
    # ...

def _stop_and_save_current(self):
    self.is_testing = False
    self.is_paused = False
    self._finalize_partial_axes()
    if self.axis_results:
        self._complete_test()
    # ...
```

#### Phase 3: Move INI config to a function (not a class)

`_load_config` and `_save_config` are pure I/O with no GUI dependency. Extract as
module-level functions in `app.py`:

```python
def load_ini_config(ini_path: str) -> Dict:
    """INI 설정 파일 로드"""
    config = {"port": "COM1", "baudrate": 9600, "working_dir": os.getcwd()}
    # ... parsing logic ...
    return config

def save_ini_config(ini_path: str, config: Dict):
    """INI 설정 파일 저장"""
    # ... writing logic ...
```

These stay in `app.py` (not worth a separate module for ~80 lines), but being
top-level functions removes ~80 lines of instance methods from the class.

#### What NOT to do

- **Don't extract a TestController class.** The test thread (`_run_test`) is deeply
  coupled to the GUI via `self.root.after()`, `self.var_status`, `self.tree`, etc.
  Separating it would require an event/callback system that adds complexity without
  payoff for this application size.

- **Don't use Tkinter mixins.** `class ToolbarMixin`, `class GridMixin`, etc. cause
  method resolution order (MRO) confusion and make the code harder to trace, not easier.

- **Don't create a separate `config.py` module.** The INI config is 2 functions
  (~80 lines). A dedicated module is overkill.

### Post-decomposition MiniasApp structure

After applying all phases, `MiniasApp` looks like:

```python
class MiniasApp:
    """MINIAS 메인 애플리케이션 (Tkinter GUI)"""

    # --- Init ---
    def __init__(self):                  # ~30 lines (unchanged)

    # --- GUI Construction (broken into builders) ---
    def _create_gui(self):               # ~10 lines (dispatcher)
    def _build_toolbar(self):            # ~30 lines
    def _build_input_panel(self):        # ~60 lines
    def _build_status_bar(self):         # ~10 lines
    def _build_options_bar(self):        # ~25 lines
    def _build_results_grid(self):       # ~35 lines
    def _build_footer(self):             # ~5 lines
    def _init_grid_rows(self):           # ~12 lines

    # --- Data Loading ---
    def _load_initial_data(self):        # ~25 lines
    def _on_code_selected(self):         # ~7 lines
    def _on_add_code(self):              # ~14 lines
    def _on_del_code(self):              # ~13 lines
    def _on_add_operator(self):          # ~8 lines
    def _on_del_operator(self):          # ~13 lines
    def _refresh_id_list(self):          # ~5 lines
    def _on_id_selected(self):           # ~7 lines
    def _on_load_id(self):               # ~48 lines
    def _load_test_result(self):         # ~48 lines

    # --- Test Orchestration ---
    def _on_start(self):                 # ~63 lines
    def _run_test(self):                 # ~130 lines
    def _on_pause(self):                 # ~10 lines
    def _on_stop(self):                  # ~20 lines (after dedup)
    def _stop_and_save_current(self):    # ~10 lines (after dedup)
    def _finalize_partial_axes(self):    # ~25 lines (NEW, shared logic)
    def _complete_test(self):            # ~90 lines
    def _update_grid_row_live(self):     # ~16 lines
    def _update_grid_row(self):          # ~15 lines
    def _reset_buttons(self):            # ~2 lines

    # --- Print & Export ---
    def _on_print_certificate(self):     # ~60 lines
    def _on_print_direct(self):          # ~50 lines
    def _on_delete_result(self):         # ~35 lines

    # --- Settings & Lifecycle ---
    def _on_settings(self):              # ~2 lines
    def _apply_settings(self):           # ~6 lines
    def _on_limits(self):                # ~4 lines
    def _on_exit(self):                  # ~10 lines
    def run(self):                       # ~3 lines
```

The class is still ~1100 lines (we removed ~80 lines of config + ~90 lines of
duplication), but crucially `_create_gui` is now navigable (6 focused builders
instead of one 207-line wall), and the stop logic is DRY.

Further reduction would require architectural changes (MVC, event bus) that are
explicitly out of scope per PROJECT.md.

---

## Summary: Complete Refactoring Execution Order

```
1. Extract models.py          (leaf, ~80 lines, zero risk)
2. Extract serial_comm.py     (leaf, ~220 lines, zero risk)
3. Extract calculator.py      (near-leaf, ~60 lines, zero risk)
4. Extract database.py        (near-leaf, ~640 lines, medium risk — safe_get dedup)
5. Extract excel_export.py    (near-leaf, ~70 lines, zero risk)
6. Extract certificate.py     (near-leaf, ~320 lines, low risk — import cleanup)
7. Extract dialogs.py         (mid-tier, ~310 lines, low risk)
8. Create minias/ package     (structural, medium risk — entry point change)
9. Break up _create_gui       (internal refactor, low risk)
10. Deduplicate stop-and-save (internal refactor, low risk)
11. Extract config functions  (internal refactor, zero risk)
```

After step 8, the monolith is gone. Steps 9-11 clean up the god class internals.
Each step should be a separate commit with a manual smoke test (`uv run minias`).

# STACK.md — Restructuring a Python/Tkinter Desktop App

Research for splitting `minias_app.py` (3064 lines, 13 classes) into a clean
multi-module package. All recommendations are specific to this project — a
Tkinter desktop app with SQLite, serial comms, calculations, and report export.

---

## 1. Recommended Package Structure

**Confidence: High**

The monolith already has clear section banners that map directly to modules.
The refactor is mechanical — cut along existing seams, not invent new ones.

```
dahasys_gui/                      # repo root (unchanged)
├── pyproject.toml                # updated [project.scripts] entry
├── minias_app.py                 # DELETED after migration (keep as backup initially)
├── minias.db                     # runtime database (unchanged)
├── MINIAS.INI                    # legacy config (unchanged)
├── resources/                    # existing assets (unchanged)
│   ├── form.xlsx
│   └── logo.png
├── figs/                         # reference screenshots (unchanged)
│
└── minias/                       # NEW — the Python package
    ├── __init__.py               # package marker + version; re-exports nothing
    ├── __main__.py               # `python -m minias` support
    ├── app.py                    # MiniasApp class (GUI shell + event handlers)
    ├── models.py                 # dataclasses: TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo
    ├── database.py               # MiniasDatabase class
    ├── serial_comm.py            # SerialCommunicator class (+ SERIAL_AVAILABLE flag)
    ├── calculator.py             # TestCalculator class
    ├── excel_export.py           # ExcelExporter class (+ EXCEL_AVAILABLE flag)
    ├── certificate.py            # CertificateGenerator class (+ PDF_AVAILABLE flag)
    ├── dialogs.py                # LimitsDialog + SettingsDialog classes
    └── utils.py                  # safe_get(), unit conversion helpers, shared constants
```

### Why This Shape

| Decision | Rationale |
|----------|-----------|
| Flat package (no sub-packages) | ~3000 lines across 10 files ≈ 300 lines/file avg. Sub-packages add complexity for no benefit. |
| One file per existing section banner | The monolith already has `# === 데이터베이스 모듈 ===` etc. Each becomes a file. Zero design invention needed. |
| `dialogs.py` as one file (not per-dialog) | LimitsDialog is 78 lines, SettingsDialog is 230 lines. Together ~308 lines. Not worth separate files. |
| `utils.py` for shared helpers | `safe_get()` is duplicated 4x as nested closures. One canonical version. Unit conversion (mm ↔ microns ↔ 2σ) belongs here too. |
| `__main__.py` for `-m` support | Standard Python practice. Allows `python -m minias` in addition to the entry point script. |
| `app.py` not `gui.py` | The class is called `MiniasApp`. The file name should match the primary class concept. |

### Approximate File Sizes After Split

| File | Lines (est.) | Source |
|------|-------------|--------|
| `models.py` | ~80 | 5 dataclasses (lines 57–136) |
| `database.py` | ~635 | MiniasDatabase (lines 142–776) |
| `serial_comm.py` | ~215 | SerialCommunicator (lines 782–996) |
| `calculator.py` | ~60 | TestCalculator (lines 1002–1060) |
| `excel_export.py` | ~70 | ExcelExporter (lines 1066–1133) |
| `certificate.py` | ~315 | CertificateGenerator (lines 1139–1453) |
| `app.py` | ~1275 | MiniasApp (lines 1459–2733) — still the largest, but acceptable |
| `dialogs.py` | ~310 | LimitsDialog + SettingsDialog (lines 2739–3051) |
| `utils.py` | ~40–60 | safe_get, unit conversion, constants |
| `__init__.py` | ~5 | Version string only |
| `__main__.py` | ~5 | Calls main() |

### Should `app.py` (1275 lines) Be Split Further?

**Confidence: Medium** — possible but not required in this round.

The 1275-line `MiniasApp` class is a Tkinter root window. In Tkinter apps, the
root window class typically IS large because it owns all the widgets and event
handlers. Splitting it further means either:

- **Option A: Split by GUI region** — e.g., `gui_test_panel.py`,
  `gui_results_panel.py`. Requires passing the parent frame and shared state
  between files. Adds coupling complexity.
- **Option B: Extract `_create_gui()` into a builder** — The 207-line
  `_create_gui()` method could become a standalone function that takes `self`
  and builds the GUI. This is simpler but only helps one method.

**Recommendation:** Leave `app.py` at 1275 lines for now. It's navigable at
that size. If future work adds features, split by GUI region then. The PROJECT.md
already marks this as out of scope ("No MVC/MVP architecture").

---

## 2. Module Organization Patterns

### 2.1 Import Dependency Graph (No Cycles)

**Confidence: High**

The dependency flow must be strictly one-directional:

```
models.py          ← no imports from minias package
    ↑
utils.py           ← imports models (for type hints only, if needed)
    ↑
database.py        ← imports models
    ↑
calculator.py      ← imports models
    ↑
serial_comm.py     ← imports nothing from minias (self-contained)
    ↑
excel_export.py    ← imports models, database
    ↑
certificate.py     ← imports models, database
    ↑
dialogs.py         ← imports database (for LimitsDialog data access)
    ↑
app.py             ← imports everything above
    ↑
__main__.py        ← imports app
```

**Rules to prevent circular imports:**

1. **`models.py` imports NOTHING from the package.** It only uses stdlib
   (`dataclasses`, `datetime`, `typing`). This is the foundation layer.
2. **No module imports `app.py`.** Only `__main__.py` and the entry point do.
3. **`database.py` does not import GUI modules.** If the database needs to
   signal the GUI (e.g., errors), it raises exceptions. The GUI catches them.
4. **Dialogs receive dependencies via constructor arguments**, not by importing
   `app.py`. Example: `LimitsDialog(parent, db)` where `db` is passed in.

### 2.2 Import Style Within the Package

**Confidence: High**

Use explicit relative or absolute imports. Be consistent — pick one. For a flat
package this small, **absolute imports are simpler and clearer**:

```python
# In minias/app.py
from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo
from minias.database import MiniasDatabase
from minias.serial_comm import SerialCommunicator
from minias.calculator import TestCalculator
from minias.excel_export import ExcelExporter
from minias.certificate import CertificateGenerator
from minias.dialogs import LimitsDialog, SettingsDialog
from minias.utils import safe_get, microns_to_mm
```

**Why not relative imports?** Relative imports (`from .models import ...`) work
but are confusing when the package is small and flat. Absolute imports are
immediately readable and greppable. They also work identically whether the module
is run as part of the package or referenced externally.

### 2.3 How `__init__.py` Should Look

**Confidence: High**

Keep it minimal. Do NOT re-export the entire API surface. This is a desktop app,
not a library that other packages import.

```python
# minias/__init__.py
"""MINIAS Probe Testing System"""

__version__ = "1.0.0"
```

That's it. No `from .models import *`. No `from .app import MiniasApp`. The only
consumer of these modules is `app.py` and `__main__.py` — they know exactly what
to import.

**When to re-export in `__init__.py`:** Only if this package were published as a
library for external consumers to `import minias`. It's not. It's a desktop app.

### 2.4 How `__main__.py` Should Look

**Confidence: High**

```python
# minias/__main__.py
"""python -m minias 지원"""

from minias.app import main

if __name__ == "__main__":
    main()
```

### 2.5 Feature Flag Pattern (Optional Imports)

**Confidence: High**

Each module that wraps an optional dependency owns its own feature flag:

```python
# minias/serial_comm.py
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Serial communication disabled.")
```

The flag lives in the module that uses the dependency. `app.py` checks it via:

```python
from minias.serial_comm import SERIAL_AVAILABLE
```

Do NOT centralize all feature flags in `__init__.py` or `utils.py`. Each module
is responsible for its own optional dependency.

### 2.6 Splitting the God Class (`MiniasApp`)

**Confidence: High** for the extraction approach below.

The MiniasApp class (1273 lines) should NOT be decomposed into inheritance
hierarchies or mixin classes. That creates harder-to-follow control flow.
Instead, reduce its size through these mechanical extractions:

1. **Extract `safe_get()` to `utils.py`** — Currently duplicated 4 times as
   nested closures inside different methods. Make it a module-level function.
   Saves ~40 lines of duplication.

2. **Extract dialog classes** — `LimitsDialog` and `SettingsDialog` are already
   separate classes. They move to `dialogs.py` with zero refactoring needed.

3. **Extract calculation, export, and serial classes** — Already separate
   classes. They move to their own files. Zero refactoring needed.

4. **Extract the `_on_print_certificate` / `generate()` flow** — The 305-line
   `generate()` method on `CertificateGenerator` already lives in its own class.
   It moves with the class.

5. **Do NOT extract individual `_on_*` event handlers into separate files.**
   They reference `self.var_*` Tkinter variables extensively. Moving them would
   require either passing 20+ widget references or creating a shared state
   object — both are worse than a 1275-line class.

**Net result:** MiniasApp drops to ~1275 lines (it's already ~1275 after
removing the other classes). This is acceptable for a Tkinter root window class.
The class is large but every method is an event handler or GUI builder — it has
high cohesion.

---

## 3. Python Packaging

### 3.1 `pyproject.toml` Entry Point

**Confidence: High**

Current:
```toml
[project.scripts]
minias = "minias_app:main"
```

After refactor:
```toml
[project.scripts]
minias = "minias.app:main"
```

This means: in the `minias` package, in the `app` module, call the `main()`
function. `uv run minias` continues to work identically.

### 3.2 How `uv` Discovers the Package

**Confidence: High**

`uv` (and pip) discover packages by looking for directories with `__init__.py`.
Once `minias/` exists with `__init__.py`, the package is installable.

No changes needed to `pyproject.toml` beyond the scripts entry. No
`[tool.setuptools.packages]` or `packages = [...]` configuration needed — the
default package discovery finds `minias/` automatically.

### 3.3 What Happens to the Old `minias_app.py`

**Confidence: High**

Delete it. After the refactor, the `minias/` package replaces it entirely.

**Migration sequence:**
1. Create `minias/` directory with all module files.
2. Update `pyproject.toml` scripts entry.
3. Run `uv sync` to re-install the package.
4. Verify `uv run minias` launches the app.
5. Delete `minias_app.py`.

Do NOT keep `minias_app.py` as a shim that imports from the package. That adds
a confusing layer of indirection.

### 3.4 Working Directory and File Paths

**Confidence: High**

The app references files relative to the working directory:
- `minias.db` (SQLite database)
- `MINIAS.INI` (config file)
- `resources/form.xlsx` (Excel template)
- `resources/logo.png` (PDF logo)

These paths must NOT change. The app assumes it runs from the repo root. Since
the entry point script (`uv run minias`) sets the working directory to wherever
the user runs it (typically the repo root), all relative paths continue to work.

**Do NOT use `__file__`-relative paths** for data files. The current code uses
plain relative paths (`"minias.db"`, `"MINIAS.INI"`) and this should stay the
same. The working directory is the repo root, not `minias/`.

---

## 4. What NOT to Do

### 4.1 Do NOT Create Sub-Packages

**Confidence: High**

```
# BAD — over-engineered for 3000 lines
minias/
├── gui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── panels/
│   │   ├── test_panel.py
│   │   └── results_panel.py
│   └── dialogs/
│       ├── limits.py
│       └── settings.py
├── core/
│   ├── __init__.py
│   ├── calculator.py
│   └── models.py
├── io/
│   ├── __init__.py
│   ├── serial.py
│   ├── excel.py
│   └── pdf.py
└── data/
    ├── __init__.py
    └── database.py
```

This is a 3000-line app, not a framework. Nested packages add `__init__.py`
files, longer import paths, and cognitive overhead. A flat package with 10 files
is perfectly navigable.

### 4.2 Do NOT Use Mixins or Multiple Inheritance to Split MiniasApp

**Confidence: High**

```python
# BAD — "mixin decomposition" anti-pattern
class TestingMixin:
    def _on_start(self): ...
    def _on_pause(self): ...

class ResultsMixin:
    def _on_browse_results(self): ...

class MiniasApp(TestingMixin, ResultsMixin, tk.Tk):
    ...
```

This scatters the class across files while keeping tight coupling (every mixin
references `self.var_*`, `self.db`, etc.). It makes control flow impossible to
follow and creates implicit dependencies between mixins. The "god class" problem
becomes a "god class hidden across 5 files" problem.

### 4.3 Do NOT Create Abstract Base Classes or Interfaces

**Confidence: High**

```python
# BAD — premature abstraction
class DatabaseInterface(ABC):
    @abstractmethod
    def connect(self): ...
    @abstractmethod
    def get_operators(self) -> List[str]: ...
```

There is exactly one database implementation (SQLite), one serial implementation,
one calculator. ABCs add a layer of indirection with zero benefit. If a second
implementation is ever needed (unlikely for a desktop probe tester), add the
abstraction then.

### 4.4 Do NOT Create a Central "State" or "Context" Object

**Confidence: High**

```python
# BAD — state bag anti-pattern
class AppState:
    db: MiniasDatabase
    serial: SerialCommunicator
    current_test: Optional[TestResult]
    var_probe_type: tk.StringVar
    ...
```

Tkinter variables (`StringVar`, `IntVar`, etc.) are inherently tied to the GUI.
Extracting them into a separate state object doesn't decouple anything — every
module still needs the state object, and now you have an additional class to
maintain. Let `MiniasApp` own its state directly, as it does now.

### 4.5 Do NOT Change Import Guard Patterns

**Confidence: High**

The existing try/except import pattern with feature flags is correct and should
be preserved exactly as-is in each module. Do not:

- Move feature flags to a central config
- Replace try/except with `importlib.util.find_spec()`
- Make feature checks lazy

The current pattern is explicit, obvious, and matches the AGENTS.md guidelines.

### 4.6 Do NOT Rename Classes During the Split

**Confidence: High**

Keep every class name identical: `MiniasDatabase`, `SerialCommunicator`,
`TestCalculator`, `ExcelExporter`, `CertificateGenerator`, `MiniasApp`,
`LimitsDialog`, `SettingsDialog`. Renaming during a structural refactor
creates unnecessary diff noise and makes it harder to verify the refactor
preserved behavior.

### 4.7 Do NOT Add `__all__` to Modules

**Confidence: Medium**

`__all__` is for controlling `from module import *` behavior. Nobody should be
using `import *` in this project. Each module's public API is obvious from its
class name. Adding `__all__` is busywork that provides no safety in a non-library
codebase.

### 4.8 Do NOT Move Data Files into the Package

**Confidence: High**

```
# BAD — moving resources into the package
minias/
├── data/
│   ├── form.xlsx
│   └── logo.png
```

The app expects `resources/form.xlsx` and `resources/logo.png` relative to the
working directory. Moving them into the package would require `importlib.resources`
or `__file__`-relative path resolution. This adds complexity and changes behavior
for zero benefit in a desktop app that always runs from its own directory.

---

## Summary of Confidence Levels

| Recommendation | Confidence |
|---------------|------------|
| Flat package, one module per existing section | **High** |
| Absolute imports between modules | **High** |
| Minimal `__init__.py` (no re-exports) | **High** |
| Feature flags stay in their respective modules | **High** |
| `pyproject.toml` entry: `minias.app:main` | **High** |
| Delete `minias_app.py` after migration | **High** |
| Keep relative file paths for data files | **High** |
| Do not split `app.py` further this round | **Medium** |
| Do not add `__all__` | **Medium** |
| No sub-packages, mixins, ABCs, or state objects | **High** |
| No class renames during split | **High** |

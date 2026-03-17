# Refactoring Pitfalls: Monolithic Python/Tkinter to Modules

Specific to the MINIAS codebase (`minias_app.py`, ~3064 lines, Python/Tkinter/SQLite).

---

## 1. Breaking the App During Extraction

**Description:** Extracting a class (e.g., `MiniasDatabase`) into `database.py` introduces a subtle breakage — a missing import, a changed relative path, a lost closure reference — and the app crashes on startup or mid-operation. Because there are no tests, the breakage goes unnoticed until the user hits a specific workflow path (e.g., Excel export only used after completing a full test).

**Warning Signs:**
- The app launches fine but crashes when you trigger a less-common code path (PDF export, limits dialog, serial settings)
- You extracted a class but forgot it depends on a dataclass defined 800 lines above it in the original file
- `ExcelExporter.generate()` (305 lines) calls `safe_get` as a nested closure — moving the class without the closure breaks silently until export is attempted

**Prevention:**
- Extract one class/module at a time, then immediately launch with `uv run minias` and manually exercise the affected functionality
- Before extracting, search the entire file for every reference to the class being moved and every reference FROM that class to other symbols in the file
- Keep a checklist of functional smoke tests: launch → select code → start test (simulation) → complete test → export Excel → export PDF → edit limits → change COM settings → browse past results
- Use `from minias_app import X` temporarily during extraction, switching to the new module import only after verifying it works

**Phase Relevance:** Every single extraction step. This is the #1 risk throughout the entire refactor.

---

## 2. Circular Imports

**Description:** Python's import system executes module-level code at import time. When `MiniasApp` (in `app.py`) imports `MiniasDatabase` from `database.py`, and `database.py` imports `TestResult` from `models.py`, that's fine — it's a DAG. But if `database.py` also needs something from `app.py` (e.g., a utility function left behind), you get `ImportError: cannot import name 'X' from partially initialized module`. In Tkinter apps this is especially dangerous because the god class (`MiniasApp`, 1273 lines) touches everything: database, serial, calculator, exporter, certificate generator, dialogs.

**Warning Signs:**
- `ImportError` or `AttributeError` on module-level symbols at startup
- You feel the urge to add `from app import MiniasApp` inside a module like `dialogs.py` — this is the circular import forming
- `LimitsDialog` and `SettingsDialog` currently live in the same file as `MiniasApp` and directly reference `MiniasDatabase`, `SerialCommunicator`, and `LimitInfo` — splitting dialogs into their own file while they depend on classes that depend on models creates a dependency web

**Prevention:**
- Establish a strict one-way import hierarchy before writing any code:
  ```
  models.py          (no imports from project)
     ↑
  database.py        (imports models)
     ↑
  calculator.py      (imports models)
  serial_comm.py     (no project imports)
  excel_export.py    (imports models)
  certificate.py     (imports models)
     ↑
  dialogs.py         (imports models, database, serial_comm)
     ↑
  app.py             (imports everything)
  ```
- Never let a lower-level module import from `app.py`
- If a dialog needs to call back into the app, pass a callback function or the specific object it needs (dependency injection), not the whole `MiniasApp` instance
- The current code already does this correctly: `SettingsDialog.__init__` takes `parent`, `config`, and `callback` — preserve this pattern

**Phase Relevance:** Critical during the first 2-3 extractions when the dependency graph is being established. Once the hierarchy is set, later extractions follow the pattern.

---

## 3. Over-Splitting Small Modules

**Description:** `TestCalculator` is 57 lines — five static methods doing basic `statistics.stdev()`, `statistics.mean()`, `max()-min()`, and two comparison methods. Giving it its own file creates a `calculator.py` that's mostly boilerplate (docstring, imports, class definition) with trivially small methods. Similarly, `CertificateGenerator` is ~310 lines but is a single `generate()` method with PDF layout logic — splitting it further (into what? `pdf_header.py`?) would be absurd.

**Warning Signs:**
- A module has fewer than ~80 lines of actual logic (excluding imports/docstrings)
- You're creating a file for a single function or a class with only static methods
- The module has no internal state and could just as easily be functions in a `utils.py`
- You find yourself creating `__init__.py` files that re-export everything because the split adds no navigational value

**Prevention:**
- Apply the "would I open this file to find this code?" test. If looking for test calculations, `calculator.py` makes sense as a name even at 57 lines — it's a clear responsibility boundary
- Consider combining tiny related modules: `calculator.py` (57 lines) could live inside `models.py` if the models are also small, but keeping it separate is defensible since it's a distinct responsibility
- Do NOT split `ExcelExporter.generate()` (305 lines) into sub-methods as part of this refactor — that's a code quality improvement, not a structural extraction
- Set a rough threshold: anything under ~40 lines of logic probably doesn't justify its own file unless it has a clearly distinct responsibility

**Phase Relevance:** During initial module planning (before extraction begins). The decision of what becomes a file should be made once and not revised mid-refactor.

---

## 4. Losing Track of GUI State When Splitting the God Class

**Description:** `MiniasApp` has 20+ instance variables tracking GUI state: `self.is_testing`, `self.is_paused`, `self.current_axis`, `self.current_cycle`, `self.measurements`, `self.axis_results`, plus 11 `tk.StringVar`/`tk.BooleanVar` variables. When extracting methods that read or modify this state (e.g., `_run_test` reads `self.is_testing`, `self.is_paused`, `self.var_naxis`, `self.measurements`, `self.limits`, `self.serial`, `self.calculator`, `self.db`, and writes to `self.current_axis`, `self.current_cycle`, `self.axis_results`), the extracted code must still have access to all of it. Moving `_run_test` into a separate `test_runner.py` means either passing 15 parameters or passing the entire `MiniasApp` instance — which defeats the purpose of extraction.

**Warning Signs:**
- An extracted function/class needs more than 5-6 parameters from `MiniasApp`
- You start passing `self` (the MiniasApp instance) to extracted modules — you've just moved the god class problem, not solved it
- After extraction, you can't tell which module owns the `is_testing` flag — is it the test runner's state or the GUI's state?
- Tkinter `StringVar` objects are bound to the root window — they can't be created before `tk.Tk()` exists, so they can't be initialized in a module's constructor independently

**Prevention:**
- Accept that `MiniasApp` will remain the largest file. The goal is to extract self-contained responsibilities (database, serial, calculator, export, PDF, dialogs), NOT to break apart the GUI orchestration
- The test orchestration (`_run_test`, `_on_start`, `_on_pause`, `_on_stop`, `_complete_test`) should stay in `app.py` because it's inherently GUI state management
- Extract things that DON'T need GUI state: `MiniasDatabase` needs zero Tkinter references, `TestCalculator` is pure math, `ExcelExporter` and `CertificateGenerator` take data parameters
- If you do extract test orchestration later, use an intermediate state object (a dataclass holding `is_testing`, `current_axis`, etc.) rather than scattering state across modules

**Phase Relevance:** Mid-refactor, when the easy extractions (models, database, calculator) are done and you're tempted to further decompose `MiniasApp` itself.

---

## 5. SQLite Threading Issues

**Description:** The current code creates a single `sqlite3.Connection` with `check_same_thread=False` (line 151) and shares it between the main Tkinter thread and the background test thread (`_run_test` calls `self.db.save_measure()` from `threading.Thread`). SQLite in WAL mode handles concurrent reads, but concurrent writes from two threads on the same connection with no locking can corrupt data or raise `sqlite3.OperationalError: database is locked`. Today this works by accident because the test thread writes infrequently and the GUI thread mostly reads — but refactoring could change timing.

**Warning Signs:**
- `sqlite3.OperationalError: database is locked` during testing
- Intermittent data corruption in `MEASURES` table (the test thread writes here every cycle)
- Test results missing random cycles (write silently failed)
- Moving `MiniasDatabase` to its own module tempts you to "fix" the threading model — but that's a behavioral change, not a structural one

**Prevention:**
- During the refactor, preserve the exact same threading behavior: single connection, `check_same_thread=False`, no locks. Document it as a known issue but don't fix it — fixing it is a functional change that could introduce new bugs
- When extracting `database.py`, verify that the same `MiniasDatabase` instance is shared (not accidentally creating a second connection)
- If you absolutely must add safety, a single `threading.Lock` around `conn.execute()` is the minimal change — but even this is out of scope per PROJECT.md
- Do NOT change the connection to per-thread connections — this would change the MEASURES table behavior where the test thread writes and the GUI thread reads back immediately

**Phase Relevance:** When extracting `database.py` and when reviewing the test thread interaction. The temptation to "fix" this is strong — resist it.

---

## 6. Entry Point Breakage

**Description:** `pyproject.toml` declares `minias = "minias_app:main"` — this means `uv run minias` calls the `main()` function in the `minias_app` module (resolved to `minias_app.py` at project root). If you rename `minias_app.py`, move `main()` to a different module, or restructure into a package (`minias/`), the entry point string must be updated to match. A mismatch gives an unhelpful `ModuleNotFoundError` or `AttributeError` at launch.

**Warning Signs:**
- `uv run minias` fails with `ModuleNotFoundError: No module named 'minias_app'`
- You restructured into `minias/__init__.py` but forgot that `"minias_app:main"` now resolves differently
- The app works with `python minias_app.py` (because `__name__ == "__main__"` still triggers) but fails via the `uv run minias` entry point

**Prevention:**
- If keeping a flat structure: leave `minias_app.py` as the entry point file with `main()` in it, even if `MiniasApp` moves to `app.py`. Have `minias_app.py` do: `from app import MiniasApp` then define `main()` locally
- If creating a package: update `pyproject.toml` to `minias = "minias.app:main"` or `minias = "minias.__main__:main"`
- After ANY structural change, immediately test with `uv run minias` (not `python minias_app.py`)
- Consider also adding `if __name__ == "__main__": main()` to whatever file contains `main()` as a fallback

**Phase Relevance:** At the very first extraction (when you decide the file structure) and at the very end (final verification). Easy to get right if you decide the package structure up front.

---

## 7. Import Path Changes Breaking the App

**Description:** The current monolith has zero internal imports — everything is in one file. The moment you extract `models.py`, every other module and the main app needs `from models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo`. If you later rename `models.py` to `data_models.py`, or move it into a `minias/` package, every import breaks. With 6-8 modules all importing from each other, a rename ripples across the entire codebase.

**Warning Signs:**
- `ImportError: No module named 'models'` — you're running from a different working directory, or the module isn't on `sys.path`
- Relative imports (`from .models import ...`) work when run as a package (`python -m minias`) but fail when run as a script (`python minias_app.py`)
- IDE shows no errors (it resolves imports differently than the runtime `sys.path`)

**Prevention:**
- Decide up front: flat structure with absolute imports, or package structure with relative imports. Don't mix them
- For a flat structure (all `.py` files in project root): use `from models import TestResult`. This works because the project root is on `sys.path` when running via `uv run minias`
- For a package structure (`minias/` directory): use `from minias.models import TestResult` or `from .models import TestResult`. Ensure `pyproject.toml` entry point matches
- After establishing the first inter-module import, verify it works with `uv run minias` before proceeding
- Never use `sys.path.append()` hacks — if you need them, your structure is wrong

**Phase Relevance:** At the very beginning when the module structure is decided, then again with each new module extraction.

---

## 8. Scope Creep — "Fixing" Things Beyond Structural Cleanup

**Description:** The codebase has known bugs (indentation error in `_on_print_certificate`, undefined `self.tree_results`, duplicate imports) and code smells (`safe_get` duplicated 4 times, `ExcelExporter.generate()` at 305 lines, scattered unit conversion). While refactoring, you'll be reading every line of code, and the temptation to fix everything you see is overwhelming. Each "small fix" risks changing behavior, and without tests, you can't verify that a fix didn't break something else.

**Warning Signs:**
- You're refactoring `ExcelExporter.generate()` into sub-methods while supposedly just moving it to `excel_export.py`
- You're adding a `threading.Lock` to `MiniasDatabase` while extracting it
- You're changing the `safe_get` pattern to a utility function while moving `database.py` — this changes 4 call sites and could affect column name resolution
- You've been working on the "extraction" for 2 hours but spent most of it on code improvements
- The diff shows logic changes mixed with structural moves

**Prevention:**
- Strict two-pass approach: Phase 1 is pure structural extraction (copy-paste classes into new files, add imports, verify). Phase 2 is improvements (deduplication, bug fixes, cleanup)
- For each extraction, the diff should show only: (a) new file with the class, (b) old file with the class replaced by an import, (c) no logic changes
- Keep a running list of improvements noticed during extraction — add them to PROJECT.md "Active" tasks, don't do them inline
- The PROJECT.md already distinguishes structural tasks from cleanup tasks — respect that boundary

**Phase Relevance:** Throughout the entire refactor, but most dangerous during the first few extractions when you're deeply reading the code and noticing issues.

---

## 9. Tkinter-Specific Issues (mainloop, after(), threading)

**Description:** Tkinter is single-threaded — all widget manipulation must happen on the main thread (the one running `root.mainloop()`). The current code correctly uses `self.root.after(0, callback)` to schedule GUI updates from the background test thread (lines 2027, 2057, 2097, 2117, 2129). When code moves between files, three things can go wrong: (a) the `self.root` reference is lost, (b) `root.after()` calls are replaced with direct widget manipulation from the wrong thread, (c) the `threading.Event` synchronization pattern between the test thread and the GUI (lines 2106-2118) breaks.

**Warning Signs:**
- `RuntimeError: main thread is not in main loop` — you called a Tkinter method from the test thread
- `TclError: invalid command name` — a callback references a widget that was destroyed (e.g., dialog closed before `after()` fires)
- The app freezes — you accidentally called `event.wait()` on the main thread, or `mainloop()` was called before all widgets were created
- `self.root.after(0, ...)` lambdas capture stale variable references because Python closures capture by reference, not by value — the existing code correctly uses default arguments (`lambda a=axis, c=cycle: ...`) to avoid this, but careless editing during refactoring could break this pattern

**Prevention:**
- Keep all `root.after()` calls in `app.py` (the file that owns `self.root`). Don't let extracted modules schedule their own GUI callbacks
- The test thread (`_run_test`) should stay in `app.py` because it's tightly coupled to GUI state and uses `root.after()` extensively
- If you extract a dialog class, pass `parent` (the Tk window) to its constructor — the current `LimitsDialog` and `SettingsDialog` already do this correctly. Preserve the pattern
- Never move `root.mainloop()` or `root.protocol("WM_DELETE_WINDOW", ...)` out of the `MiniasApp.run()` method
- When moving code that uses `self.root.after()`, verify every lambda's variable capture is preserved exactly

**Phase Relevance:** When extracting dialogs and if there's any temptation to extract the test orchestration. Less relevant for pure data modules (database, models, calculator).

---

## 10. Test Regression — Verifying Behavior Without a Test Suite

**Description:** There are no automated tests. The only way to verify the refactor didn't break anything is manual testing. But manual testing is slow, error-prone, and can't cover all paths — especially paths that require physical hardware (serial probe connected). The refactor explicitly excludes adding tests (PROJECT.md: "Adding a test suite — deferred to future work"), so you must rely on other strategies.

**Warning Signs:**
- You made an extraction and only verified "it launches" — but the Excel export, PDF generation, serial communication, limits dialog, and result browsing are all untested
- You can't test serial communication without hardware, so you assume it's fine
- After 5 extractions, you've accumulated changes you've never tested together
- Import-time side effects (like `SERIAL_AVAILABLE = False` printing a warning) behave differently when import order changes

**Prevention:**
- **Smoke test checklist** — run after EVERY extraction:
  1. `uv run minias` → app launches without errors in console
  2. Select an operator and code from dropdowns (verifies DB read works)
  3. Open Limits dialog, change a value, save (verifies DB write + dialog interaction)
  4. Open COM Settings dialog (verifies serial module loaded)
  5. Click Start without serial → should enter simulation mode gracefully
  6. Browse a past test result by ID (verifies result loading)
  7. Export to Excel (verifies openpyxl integration)
  8. Generate PDF certificate (verifies reportlab integration)
- **Console output check** — watch for Python warnings, import errors, or tracebacks in the terminal where you ran `uv run minias`. The app may appear to work while printing errors to console
- **Import verification** — after each extraction, add a temporary `python -c "from module_name import ClassName; print('OK')"` check for every new module
- **Diff review** — for each extraction, the diff should be mechanically simple: class removed from old file, identical class in new file, import added. Any logic changes in the diff are a red flag
- **Feature flags** — the existing `SERIAL_AVAILABLE`, `EXCEL_AVAILABLE`, `PDF_AVAILABLE` flags must remain functional. Verify that `try/except ImportError` blocks in the new module files produce the same flags accessible from `app.py`

**Phase Relevance:** After every single extraction step. The discipline of testing after each step (not batching) is what prevents compound failures.

---

## Summary: Risk Heat Map

| Pitfall | Likelihood | Impact | Peak Phase |
|---------|-----------|--------|------------|
| 1. Breaking app during extraction | High | Critical | Every step |
| 2. Circular imports | Medium | Critical | First 2-3 extractions |
| 3. Over-splitting small modules | Low | Low | Planning |
| 4. Losing GUI state | Medium | High | Mid-refactor |
| 5. SQLite threading | Low | High | DB extraction |
| 6. Entry point breakage | Medium | Critical | First & last step |
| 7. Import path changes | Medium | High | Every step |
| 8. Scope creep | High | Medium | Throughout |
| 9. Tkinter threading issues | Medium | High | Dialog/orchestration extraction |
| 10. Test regression | High | Critical | Every step |

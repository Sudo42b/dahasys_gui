# Research Summary: MINIAS Monolith Refactor

Synthesis of [STACK.md](STACK.md), [FEATURES.md](FEATURES.md),
[ARCHITECTURE.md](ARCHITECTURE.md), and [PITFALLS.md](PITFALLS.md).

---

## 1. Key Findings

- **The monolith already has clean seams.** Section banners (`# === 데이터베이스 모듈 ===`)
  and class boundaries map 1:1 to target modules. The extraction is mechanical, not
  architectural — cut along existing lines.
- **The dependency graph is a clean DAG.** `models.py` is the universal leaf,
  `app.py` is the sole root. No circular dependencies exist if the one-way import
  rule is enforced: nothing imports `app.py` except `__main__.py`.
- **MiniasApp (1273 lines, 41 methods) must stay large.** Test orchestration,
  event handlers, and Tkinter state are tightly coupled. Splitting via mixins or
  controllers adds complexity without benefit. Internal cleanup (break up
  `_create_gui`, deduplicate stop logic) is the right approach.
- **No tests exist — manual smoke testing after every extraction is mandatory.**
  The 8-point smoke test checklist is the only safety net. Batch extractions
  without testing compound failure risk.
- **Scope creep is the highest-probability risk.** Every line will be read during
  extraction. The temptation to fix bugs, add locks, refactor long methods, or
  improve patterns while moving code must be resisted. Structural move first,
  improvements second.
- **The SQLite threading model is unsafe but must not be changed.** Single
  connection with `check_same_thread=False`, no locks. Document it; don't fix it
  during extraction.
- **Four concrete bugs exist** (indentation in `_on_print_certificate`, undefined
  `self.tree_results`, 4x duplicated `safe_get`, duplicate reportlab imports). Fix
  them in a dedicated cleanup pass after structural extraction, not during.

---

## 2. Recommended Approach

**Two-pass strategy:**

1. **Pass 1 — Pure structural extraction.** Move classes into modules one at a time,
   bottom-up from the dependency graph. Each extraction = one commit + smoke test.
   Diffs should show only: new file with class, old file with class replaced by
   import, zero logic changes.

2. **Pass 2 — Internal cleanup.** Deduplicate `safe_get`, break `_create_gui` into
   builder methods, deduplicate stop-and-save logic, extract INI config to
   functions, fix known bugs, remove dead code.

**Bottom-up order matters.** Extract leaf modules first (models, serial_comm) so
that each subsequent module can import from already-extracted modules. This
prevents temporary shims and keeps the app working at every step.

---

## 3. Stack Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Package structure | Flat `minias/` package, 10 files | ~300 lines/file avg. Sub-packages add overhead for zero navigational benefit at 3000 lines. |
| Import style | Absolute (`from minias.models import TestResult`) | Greppable, works identically in all contexts, avoids relative import confusion. |
| `__init__.py` | Minimal — version string only | This is a desktop app, not a library. No re-exports needed. |
| `__main__.py` | `from minias.app import main; main()` | Standard `-m` support. |
| Entry point | `minias = "minias.app:main"` in pyproject.toml | Direct module path, no shim. |
| Feature flags | Per-module (`SERIAL_AVAILABLE` in `serial_comm.py`, etc.) | Flags live where the dependency is used. No central flags module. |
| `safe_get` | Module-level function in `database.py` | Currently 4x duplicated closures. Single canonical version. |
| Class names | Unchanged | No renames during structural refactor. |
| File paths | Relative to working directory (unchanged) | `minias.db`, `resources/form.xlsx` stay as-is. No `__file__`-relative paths. |

---

## 4. Table Stakes

Non-negotiable requirements — the refactor fails without these:

1. **Single responsibility per module** — one file per concern, guided by existing
   section banners.
2. **No duplicated logic** — `safe_get()` consolidated, stop-and-save deduplicated.
3. **No dead code** — unused imports (`configparser`), uncalled methods
   (`get_samples`, `send_command`), duplicate imports removed.
4. **No known bugs carried forward** — indentation bug in `_on_print_certificate`
   and undefined `self.tree_results` fixed.
5. **No methods exceeding ~80 lines** — `_create_gui` (207 lines) broken into
   named builders; `_init_tables` (134 lines) broken into smaller methods.
6. **Imports at module top-level** — no buried `import time` or `import re` inside
   methods (except the graceful degradation try/except pattern).
7. **Thread-safe awareness** — document the `check_same_thread=False` pattern;
   don't accidentally create a second connection during extraction.

See [FEATURES.md](FEATURES.md) for full details.

---

## 5. Critical Pitfalls

| # | Risk | Mitigation |
|---|------|------------|
| 1 | **Breaking the app during extraction** — missing import, lost closure, changed path. No tests to catch it. | Extract one module at a time. Smoke test immediately. Diff must be mechanically simple. |
| 2 | **Circular imports** — `database.py` accidentally importing from `app.py`, or dialogs creating a cycle. | Enforce strict DAG: models → services → dialogs → app. Nothing imports `app.py`. Pass dependencies via constructor. |
| 3 | **Scope creep** — fixing bugs, adding locks, refactoring methods while doing structural extraction. | Two-pass discipline. Pass 1 = copy-paste + import. Pass 2 = improvements. Keep a "noticed issues" list. |
| 4 | **Entry point breakage** — `pyproject.toml` entry doesn't match new package structure. | Update to `minias.app:main`, run `uv sync`, verify `uv run minias` immediately. |
| 5 | **Tkinter threading traps** — `root.after()` lambdas with stale captures, widget manipulation from wrong thread. | Keep all `root.after()` calls and test orchestration in `app.py`. Preserve lambda default-argument capture pattern. |

See [PITFALLS.md](PITFALLS.md) for the full 10-item risk analysis.

---

## 6. Refactoring Order

Bottom-up from the dependency DAG. Each step = one commit + smoke test.

| Step | Module | Depends on | Risk |
|------|--------|-----------|------|
| 1 | `models.py` | (nothing) | Minimal |
| 2 | `serial_comm.py` | (nothing) | Minimal |
| 3 | `calculator.py` | models | Minimal |
| 4 | `database.py` | models | Medium — largest extraction, `safe_get` dedup |
| 5 | `excel_export.py` | models | Minimal |
| 6 | `certificate.py` | models | Low — duplicate import cleanup |
| 7 | `dialogs.py` | models, database, serial_comm | Low |
| 8 | Package creation | all | Medium — entry point change, `uv sync` |
| 9 | Break up `_create_gui` | (internal) | Low |
| 10 | Deduplicate stop-and-save | (internal) | Low |
| 11 | Extract config functions | (internal) | Minimal |

Steps 1-8 eliminate the monolith. Steps 9-11 clean up the god class internals.
See [ARCHITECTURE.md](ARCHITECTURE.md) §3 for detailed extraction instructions.

---

## 7. Anti-Patterns

Things to deliberately **NOT** do:

1. **No sub-packages** — `minias/gui/widgets/panels/` is over-engineering for 3000
   lines. Flat package only.
2. **No mixins or multiple inheritance** — splitting `MiniasApp` via `TestingMixin`,
   `ResultsMixin` scatters a coupled class across files. Worse than a god class.
3. **No ABCs or interfaces** — one implementation of each concern. `AbstractDatabase`
   serves no purpose.
4. **No central state/context object** — Tkinter vars are tied to the GUI. Extracting
   them into `AppState` doesn't decouple anything.
5. **No MVC/MVP/MVVM** — explicitly out of scope. A single-window desktop app doesn't
   benefit from formal architecture patterns.
6. **No test suite in this round** — tests written against modules in flux are
   throwaway work. Refactor first, test second.
7. **No behavioral changes** — no schema changes, no UI changes, no performance
   optimization, no new features. Every behavioral change risks the "identical
   functionality" requirement.

# AGENTS.md - Coding Agent Instructions

## Project Overview

MINIAS Probe Testing System: a Python/Tkinter desktop GUI application re-implementing
a legacy Visual Basic 6.0 probe testing system. The app manages serial communication
with measurement probes, stores test results in SQLite, and exports reports to
Excel/PDF.

**Architecture:** Monolithic single-file application (`minias_app.py`, ~1850 lines)
with a separate migration utility (`migrate_mdb.py`). No web framework, no REST API.

**Key reference:** The original VB6 UI is captured in `figs/demo.png`. The Python GUI
must remain visually similar to that reference.

---

## Build & Run Commands

| Task | Command |
|------|---------|
| Install dependencies | `uv sync` |
| Run the application | `uv run minias` or `uv run python minias_app.py` |
| Run migration utility | `uv run python migrate_mdb.py` |
| Add a dependency | `uv add <package>` |

### Python Version

The project targets **Python >= 3.10** (`requires-python` in pyproject.toml).
The `.python-version` file pins Python 3.14 for local development via `uv`.

### Testing

**No test suite exists.** No pytest, unittest, or any test framework is configured.
If you add tests, use `pytest` and place them in a `tests/` directory. Run with:
```
uv run pytest tests/
uv run pytest tests/test_database.py              # single file
uv run pytest tests/test_database.py::test_func   # single test
```

### Linting & Formatting

**No linters or formatters are configured.** No ruff, black, flake8, mypy, or isort
config exists. If you add tooling, prefer `ruff` for linting/formatting and add config
to `pyproject.toml` under `[tool.ruff]`.

### CI/CD

None. No GitHub Actions, Jenkins, or other CI pipelines exist.

---

## Dependencies

Runtime (declared in `pyproject.toml`):
- `pyserial>=3.5` -- Serial communication with measurement probes
- `openpyxl>=3.1.0` -- Excel file export
- `reportlab>=4.0.0` -- PDF certificate generation
- `pyodbc>=5.3.0` -- Access MDB migration (used only by migrate_mdb.py)

All third-party imports use **graceful degradation** via try/except with feature flags:
```python
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
```

Standard library: `tkinter`, `sqlite3`, `datetime`, `dataclasses`, `typing`,
`statistics`, `threading`, `queue`, `os`, `configparser`.

---

## Code Style Guidelines

### Import Ordering

1. Standard library imports
2. Third-party imports (wrapped in try/except with feature flags)
3. Local imports (none currently, but follow this order if modules are added)

Separate each group with a blank line.

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Classes | PascalCase | `MiniasDatabase`, `TestCalculator` |
| Methods/functions | snake_case | `get_operators()`, `save_test_result()` |
| Private methods | `_` prefix | `_init_tables()`, `_create_gui()` |
| Event handlers | `_on_` prefix | `_on_start()`, `_on_pause()` |
| Constants | UPPER_SNAKE_CASE | `SERIAL_AVAILABLE`, `BAUDRATES` |
| Variables | snake_case | `self.db_path`, `self.is_testing` |
| Tkinter variables | `var_` prefix | `self.var_probe_type`, `self.var_code` |
| Dataclass fields | snake_case | `serial_number`, `mean_sigma` |
| SQL column names | UPPER_SNAKE_CASE | `ID_COL`, `SERIAL_NUMBER` |

### Type Hints

Use type hints on all method signatures (parameters and return types). Use `typing`
module types (`List`, `Optional`, `Dict`, `Tuple`) for consistency with existing code.
Annotate instance variables where the type is not obvious:
```python
def __init__(self, db_path: str = "minias.db"):
    self.db_path = db_path
    self.conn: Optional[sqlite3.Connection] = None

def get_operators(self) -> List[str]:
```

### Docstrings

Use short Korean docstrings in triple-double-quotes. No parameter/return docs needed
for simple methods:
```python
class MiniasDatabase:
    """SQLite 데이터베이스 관리"""

    def connect(self):
        """데이터베이스 연결"""
```

Module-level docstrings are allowed in English or Korean.

### Comments

- **Section headers:** Use `# ====...====` banners with Korean titles:
  ```python
  # =============================================================================
  # 데이터베이스 모듈
  # =============================================================================
  ```
- **Sub-sections:** Use `# --- TOPIC ---` pattern
- **Inline comments:** Korean or English, whichever is clearer

### String Formatting

Use **f-strings** exclusively. No `.format()` or `%` formatting.

### SQL

Write inline SQL with triple-quoted strings. Use `CREATE TABLE IF NOT EXISTS` for
schema initialization. Table/column names are UPPER_SNAKE_CASE. Use parameterized
queries (`?` placeholders) for all user-supplied values -- never use string
interpolation in SQL.

### Error Handling

1. **GUI operations:** Use `messagebox.showwarning()` / `messagebox.showerror()`
2. **Backend operations:** Use `try/except` with `print(f"Error description: {e}")`
3. **Complex operations:** Add `traceback.print_exc()` after the print
4. **Optional imports:** Use try/except with boolean feature flags
5. **Never silently swallow exceptions** -- always log or display them

### Blank Lines & Formatting

- 2 blank lines between top-level classes and functions
- 1 blank line between methods within a class
- No enforced line length limit, but keep lines reasonable (~100-120 chars)

### Data Models

Use `@dataclass` with `field(default_factory=...)` for mutable defaults. All fields
should have default values to allow incremental construction.

---

## Database

- **Engine:** SQLite via `sqlite3` standard library
- **Schema:** Defined in `CREATE_TABLES.sql` and initialized at runtime in
  `MiniasDatabase._init_tables()`
- **Tables:** OPERATORS, CODES, SETUP, LIMITS, TEST_RESULTS, TEST_AXIS_RESULTS,
  TEST_SAMPLES, MEASURES, MEASURES_REGISTERED, EXCEL_SETUP
- **ER diagram:** `ER_DIAGRAM.md` (Mermaid format)
- **Migration from Access MDB:** Use `migrate_mdb.py` with pyodbc

---

## Project Context (from CLAUDE.md)

This project converts a VB6 legacy program (MINIAS.EXE, MSCOMM32.OCX, Minias.mdb)
to Python. Key requirements:
- The converted program must provide **identical functionality** to the VB6 original
- Use **Python + Tkinter + SQLite** as the technology stack
- UI must closely match the VB6 original (see `figs/demo.png`)
- Document any issues or discrepancies discovered during conversion

---

## Key Files

| File | Purpose |
|------|---------|
| `minias_app.py` | Main application (GUI, DB, serial, export -- all in one) |
| `migrate_mdb.py` | Access MDB to SQLite migration utility |
| `minias.db` | SQLite database (runtime data) |
| `MINIAS.INI` | Legacy config (serial port settings, paths) |
| `CREATE_TABLES.sql` | Reference SQL schema |
| `DB_SCHEMA_FULL.txt` | Full database schema from XSD export |
| `ER_DIAGRAM.md` | Entity-relationship diagram (Mermaid) |
| `resources/form.xlsx` | Excel certificate template |
| `resources/logo.png` | Company logo for PDF output |
| `figs/demo.png` | VB6 original UI screenshot (reference) |
| `pyproject.toml` | Project metadata & dependencies |
| `CLAUDE.MD` | AI agent instructions / project goals |

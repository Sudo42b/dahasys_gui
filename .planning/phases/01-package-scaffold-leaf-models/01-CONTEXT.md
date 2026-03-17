# Phase 1: Package Scaffold & Leaf Models - Context

**Gathered:** 2025-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the `minias/` package directory structure and extract the 5 zero-dependency dataclasses (TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo) from `minias_app.py` into `minias/models.py`. The monolith (`minias_app.py`) remains the entry point and imports from the new package. No logic changes, no bug fixes — pure structural extraction.

</domain>

<decisions>
## Implementation Decisions

### __init__.py content
- Include `__version__ = "1.0.0"` version string
- Re-export ALL public classes from all modules (not just models — build up as modules are added in later phases)
- For Phase 1: re-export the 5 dataclasses from `minias.models`
- Also re-export feature flags (SERIAL_AVAILABLE, EXCEL_AVAILABLE, PDF_AVAILABLE) when those modules are added in Phase 2
- Goal: `from minias import TestResult` should work, not just `from minias.models import TestResult`

### __main__.py behavior
- Simple `main()` call only — no CLI argument parsing, no argparse
- Phase 1-2: calls `from minias_app import main; main()` (existing monolith is still the entry point)
- Phase 3: will switch to `from minias.app import main; main()` when MiniasApp moves
- `python -m minias` should launch the app identically to `uv run minias`

### Import style
- Absolute imports throughout: `from minias.models import TestResult`
- No relative imports (`.models`, `..database`)
- This was decided at project level and carries through all phases

### Extraction mechanics
- Copy dataclass definitions verbatim to `minias/models.py` — no modifications
- Replace the original definitions in `minias_app.py` with `from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo`
- Keep all stdlib imports needed by models (datetime, dataclasses, typing) in models.py
- The `# === 데이터 모델 ===` banner comment in minias_app.py gets replaced by the import statement

### Claude's Discretion
- Exact ordering of imports in models.py
- Whether to add `__all__` to models.py
- Comment style in __init__.py

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project structure
- `.planning/PROJECT.md` — Project goals, constraints (DB compat, UI compat, entry point must work)
- `.planning/REQUIREMENTS.md` — STRUCT-01 and STRUCT-02 are this phase's requirements
- `.planning/ROADMAP.md` — Phase 1 success criteria and notes

### Research findings
- `.planning/research/ARCHITECTURE.md` — Module dependency DAG, recommended extraction order
- `.planning/research/STACK.md` — Package structure recommendations, import patterns
- `.planning/research/PITFALLS.md` — Pitfall #1 (breaking app during extraction), #6 (entry point), #7 (import paths)

### Source code
- `minias_app.py` lines 57-135 — The 5 dataclasses to extract
- `pyproject.toml` — Current entry point (`minias_app:main`) — NOT changed in this phase

No external specs — requirements are fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- The 5 dataclasses (lines 62-135) are fully self-contained — they only depend on stdlib (`datetime`, `dataclasses`, `typing`)
- No cross-references between the dataclasses themselves
- All fields have default values (allows incremental construction)

### Established Patterns
- `@dataclass` with `field(default_factory=...)` for mutable defaults (datetime)
- Korean docstrings in triple-double-quotes
- Type hints on all fields
- `from typing import List, Optional, Dict, Tuple` style (not `list[str]` builtins)

### Integration Points
- Every other class in minias_app.py references these dataclasses
- MiniasDatabase returns TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo
- TestCalculator uses AxisResult
- ExcelExporter and CertificateGenerator consume TestResult and AxisResult
- MiniasApp creates and passes all model types
- After extraction: all these consumers will import from `minias.models`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — standard Python package scaffolding with the decisions captured above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-package-scaffold-leaf-models*
*Context gathered: 2025-03-17*

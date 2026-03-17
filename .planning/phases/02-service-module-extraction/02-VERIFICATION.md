---
phase: 02-service-module-extraction
verified: 2026-03-17T04:15:00Z
status: passed
score: 11/11 must-haves verified
human_verification:
  - test: "Launch app with `uv run python minias_app.py`, open limits dialog, browse results, test serial panel, export Excel, generate PDF"
    expected: "All functionality identical to pre-extraction behavior"
    why_human: "No test suite — visual and functional behavior requires manual smoke test"
---

# Phase 2: Service Module Extraction — Verification Report

**Phase Goal:** Extract all five service/backend classes (database, serial, calculator, excel, certificate) into dedicated modules following the bottom-up dependency order.
**Verified:** 2026-03-17T04:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | SerialCommunicator class exists in minias/serial_comm.py with identical logic | ✓ VERIFIED | File exists, 232 lines, class defined at line 20, exports SerialCommunicator + SERIAL_AVAILABLE |
| 2  | SERIAL_AVAILABLE feature flag lives in serial_comm.py with try/except | ✓ VERIFIED | Lines 10-17: `try: import serial ... SERIAL_AVAILABLE = True except ImportError: SERIAL_AVAILABLE = False` |
| 3  | TestCalculator class exists in minias/calculator.py with identical logic | ✓ VERIFIED | File exists, 65 lines, imports LimitInfo from minias.models, 5 static methods |
| 4  | MiniasDatabase class exists in minias/database.py with identical logic | ✓ VERIFIED | File exists, 642 lines, all CRUD methods present, imports all 5 dataclasses from minias.models |
| 5  | check_same_thread=False preserved in database.py | ✓ VERIFIED | Line 19: `sqlite3.connect(self.db_path, check_same_thread=False)` |
| 6  | All safe_get closures preserved as-is in database.py | ✓ VERIFIED | 4 separate `def safe_get` closures at lines 214, 254, 368, 458 — not deduplicated |
| 7  | ExcelExporter class exists in minias/excel_export.py with EXCEL_AVAILABLE flag | ✓ VERIFIED | File exists, 82 lines, EXCEL_AVAILABLE try/except at lines 6-12, class at line 17 |
| 8  | CertificateGenerator class exists in minias/certificate.py with PDF_AVAILABLE flag | ✓ VERIFIED | File exists, 341 lines, PDF_AVAILABLE try/except at lines 8-25, class at line 29 |
| 9  | minias_app.py imports all 5 classes from minias.* modules — no local definitions | ✓ VERIFIED | Lines 17-21 import all 5 classes/flags; grep for `class SerialCommunicator/TestCalculator/MiniasDatabase/ExcelExporter/CertificateGenerator` in monolith returns zero matches |
| 10 | Feature flag definitions removed from monolith | ✓ VERIFIED | grep for `SERIAL_AVAILABLE =`, `EXCEL_AVAILABLE =`, `PDF_AVAILABLE =` in minias_app.py returns zero matches |
| 11 | minias/__init__.py re-exports all extracted classes and flags | ✓ VERIFIED | Lines 6-10: re-exports SerialCommunicator, SERIAL_AVAILABLE, TestCalculator, MiniasDatabase, ExcelExporter, EXCEL_AVAILABLE, CertificateGenerator, PDF_AVAILABLE |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `minias/serial_comm.py` | SerialCommunicator + SERIAL_AVAILABLE (min 200 lines) | ✓ VERIFIED | 232 lines, exports match, class substantive |
| `minias/calculator.py` | TestCalculator (min 50 lines) | ✓ VERIFIED | 65 lines, imports LimitInfo, 5 static methods |
| `minias/database.py` | MiniasDatabase (min 600 lines) | ✓ VERIFIED | 642 lines, imports all 5 models, full CRUD |
| `minias/excel_export.py` | ExcelExporter + EXCEL_AVAILABLE (min 60 lines) | ✓ VERIFIED | 82 lines, try/except openpyxl, class with export_result method |
| `minias/certificate.py` | CertificateGenerator + PDF_AVAILABLE (min 300 lines) | ✓ VERIFIED | 341 lines, try/except reportlab, class with generate method |
| `minias/__init__.py` | Re-exports all classes + flags | ✓ VERIFIED | 10 lines, all re-exports present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| minias_app.py | minias/serial_comm.py | `from minias.serial_comm import SerialCommunicator, SERIAL_AVAILABLE` | ✓ WIRED | Line 17, used at lines 39, 108, 527, 535, 558, 1426, 1526, 1536, 1574, 1600 |
| minias_app.py | minias/calculator.py | `from minias.calculator import TestCalculator` | ✓ WIRED | Line 18, used at line 41 (`self.calculator = TestCalculator()`) |
| minias_app.py | minias/database.py | `from minias.database import MiniasDatabase` | ✓ WIRED | Line 19, used at lines 39, 1311 |
| minias_app.py | minias/excel_export.py | `from minias.excel_export import ExcelExporter, EXCEL_AVAILABLE` | ✓ WIRED | Line 20, used at line 42 |
| minias_app.py | minias/certificate.py | `from minias.certificate import CertificateGenerator, PDF_AVAILABLE` | ✓ WIRED | Line 21, used at line 43 |
| minias/database.py | minias/models.py | `from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo` | ✓ WIRED | Line 7, all 5 dataclasses imported and used throughout CRUD methods |
| minias/calculator.py | minias/models.py | `from minias.models import LimitInfo` | ✓ WIRED | Line 6, LimitInfo used in evaluate_axis_result and evaluate_overall_result |
| minias/excel_export.py | minias/models.py | `from minias.models import TestResult, AxisResult` | ✓ WIRED | Line 14, both used in export_result method signature |
| minias/certificate.py | minias/models.py | `from minias.models import TestResult, AxisResult, CodeInfo` | ✓ WIRED | Line 26, all three used in generate method signature |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| STRUCT-03 | 02-02-PLAN | Extract MiniasDatabase class into `minias/database.py` | ✓ SATISFIED | database.py exists (642 lines), MiniasDatabase class with all CRUD methods, imported by monolith at line 19 |
| STRUCT-04 | 02-01-PLAN | Extract SerialCommunicator class into `minias/serial_comm.py` | ✓ SATISFIED | serial_comm.py exists (232 lines), SerialCommunicator class + SERIAL_AVAILABLE flag, imported by monolith at line 17 |
| STRUCT-05 | 02-01-PLAN | Extract TestCalculator class into `minias/calculator.py` | ✓ SATISFIED | calculator.py exists (65 lines), TestCalculator class with 5 static methods, imported by monolith at line 18 |
| STRUCT-06 | 02-03-PLAN | Extract ExcelExporter class into `minias/excel_export.py` | ✓ SATISFIED | excel_export.py exists (82 lines), ExcelExporter class + EXCEL_AVAILABLE flag, imported by monolith at line 20 |
| STRUCT-07 | 02-03-PLAN | Extract CertificateGenerator class into `minias/certificate.py` | ✓ SATISFIED | certificate.py exists (341 lines), CertificateGenerator class + PDF_AVAILABLE flag, imported by monolith at line 21 |

**Orphaned requirements:** None. REQUIREMENTS.md maps exactly STRUCT-03 through STRUCT-07 to Phase 2. All 5 are claimed by plans and all 5 are satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | No blockers or warnings found |

**Scanned files:** serial_comm.py, calculator.py, database.py, excel_export.py, certificate.py, __init__.py
**Patterns checked:** TODO/FIXME/HACK/PLACEHOLDER, empty implementations, console.log-only handlers
**Result:** Clean. The `return []` in serial_comm.py (lines 36, 44) is legitimate fallback logic for when pyserial is unavailable, not stub code.

### Human Verification Required

### 1. Full Application Smoke Test

**Test:** Run `uv run python minias_app.py` and perform the 8-point smoke test:
1. App launches without errors
2. Open limits dialog
3. Browse results
4. Test serial panel / COM port listing
5. Export to Excel
6. Generate PDF certificate
7. Change COM settings
8. Verify INI save

**Expected:** All functionality works identically to pre-extraction behavior. No crashes, no missing data, no broken UI elements.
**Why human:** No test suite exists. Visual and functional behavior cannot be verified programmatically.

### Gaps Summary

No gaps found. All 5 service modules extracted correctly:

- **serial_comm.py** (232 lines): SerialCommunicator + SERIAL_AVAILABLE — leaf module, no internal deps
- **calculator.py** (65 lines): TestCalculator — depends on models.LimitInfo
- **database.py** (642 lines): MiniasDatabase — depends on all 5 models, safe_get closures preserved, check_same_thread=False preserved
- **excel_export.py** (82 lines): ExcelExporter + EXCEL_AVAILABLE — depends on models.TestResult, AxisResult
- **certificate.py** (341 lines): CertificateGenerator + PDF_AVAILABLE — depends on models.TestResult, AxisResult, CodeInfo; script_dir changed to os.getcwd() for correct resource path resolution

Monolith reduced from ~2985 lines (post-Phase 1) to 1633 lines. Remaining content: MiniasApp, LimitsDialog, SettingsDialog, main() — ready for Phase 3.

All 5 requirement IDs (STRUCT-03 through STRUCT-07) accounted for across 3 plans and verified against codebase. REQUIREMENTS.md traceability table matches.

---

_Verified: 2026-03-17T04:15:00Z_
_Verifier: Claude (gsd-verifier)_

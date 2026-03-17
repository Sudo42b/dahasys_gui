"""데이터 모델 및 유틸리티"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


# =============================================================================
# 단위 변환 유틸리티
# =============================================================================


def mm_to_microns(mm_value: float) -> float:
    """mm를 micron으로 변환"""
    return mm_value * 1000.0


def microns_to_mm(micron_value: float) -> float:
    """micron을 mm로 변환"""
    return micron_value / 1000.0


def format_microns(mm_value: float, decimals: int = 1) -> str:
    """mm 값을 micron 표시 문자열로 변환"""
    return f"{mm_value * 1000.0:.{decimals}f}"


def format_2sigma_microns(mm_sigma: float, decimals: int = 1) -> str:
    """mm sigma 값을 2sigma micron 표시 문자열로 변환"""
    return f"{mm_sigma * 2000.0:.{decimals}f}"


@dataclass
class TestResult:
    """테스트 결과 데이터"""

    id_col: int = 0
    date: datetime = field(default_factory=datetime.now)
    code: str = ""
    serial_number: str = ""
    operator: str = ""
    test_type: str = "ST"
    result: str = ""
    mean_sigma: float = 0.0
    mean_range: float = 0.0
    worst_sigma: float = 0.0
    worst_range: float = 0.0
    mean_sigma_limit: float = 0.0
    mean_range_limit: float = 0.0
    worst_range_limit: float = 0.0
    second_test: str = "N"


@dataclass
class AxisResult:
    """축별 테스트 결과"""

    id_col: int = 0
    axis: int = 0
    direction: str = ""
    sigma: float = 0.0
    range_val: float = 0.0
    result: str = ""
    ncycles: int = 0
    second_test: str = "N"


@dataclass
class CodeInfo:
    """프로브 코드 정보"""

    code: str = ""
    naxis: int = 4
    probe_type: str = ""
    x_plus_dir: int = 1
    x_minus_dir: int = 1
    y_plus_dir: int = 1
    y_minus_dir: int = 1
    z_minus_dir: int = 1


@dataclass
class SetupInfo:
    """테스트 설정 정보"""

    test_type: str = "ST"
    ncycles: int = 100
    naxis: int = 4
    nworstdatums: int = 1
    sigma_test: bool = True
    range_test: bool = True


@dataclass
class LimitInfo:
    """한계값 정보"""

    test_type: str = "ST"
    mean_sigma: float = 0.0
    mean_range: float = 0.0
    worst_range: float = 0.0
    mean_range_performance: float = 0.0
    worst_range_performance: float = 0.0
    mean_range_second: float = 0.0
    worst_range_second: float = 0.0

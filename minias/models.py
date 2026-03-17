"""데이터 모델"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


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

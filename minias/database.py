"""데이터베이스 모듈"""

import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Tuple

from minias.models import TestResult, AxisResult, CodeInfo, SetupInfo, LimitInfo


def _safe_get(row, column_names, name, alt_name=None, default=None):
    """행 데이터에서 컬럼값 안전 조회"""
    if name in column_names:
        val = row[name]
        return val if val is not None else default
    if alt_name and alt_name in column_names:
        val = row[alt_name]
        return val if val is not None else default
    return default


class MiniasDatabase:
    """SQLite 데이터베이스 관리"""

    def __init__(self, db_path: str = "minias.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        """데이터베이스 연결"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def close(self):
        """연결 종료"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _init_tables(self):
        """테이블 초기화"""
        cursor = self.conn.cursor()
        self._create_core_tables(cursor)
        self._create_config_tables(cursor)
        self._create_result_tables(cursor)
        self._create_measure_tables(cursor)
        self.conn.commit()

        # 기본 데이터 삽입
        self._insert_default_data()

    def _create_core_tables(self, cursor):
        """기본 테이블 생성 (OPERATORS, CODES)"""
        # OPERATORS 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OPERATORS (
                OPERATOR VARCHAR(20) PRIMARY KEY
            )
        """)

        # CODES 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CODES (
                CODE VARCHAR(11) PRIMARY KEY,
                NAXIS INT DEFAULT 4,
                PROBE_TYPE VARCHAR(30),
                XPLUS_DIR SMALLINT DEFAULT 1,
                XMINUS_DIR SMALLINT DEFAULT 1,
                YPLUS_DIR SMALLINT DEFAULT 1,
                YMINUS_DIR SMALLINT DEFAULT 1,
                ZMINUS_DIR SMALLINT DEFAULT 1
            )
        """)

    def _create_config_tables(self, cursor):
        """설정 테이블 생성 (SETUP, LIMITS)"""
        # SETUP 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SETUP (
                TEST_TYPE VARCHAR(2) PRIMARY KEY,
                NCYCLES INT DEFAULT 100,
                NAXIS SMALLINT DEFAULT 4,
                NWORSTDATUMS SMALLINT DEFAULT 1,
                SIGMA_TEST BOOLEAN DEFAULT 1,
                RANGE_TEST BOOLEAN DEFAULT 1
            )
        """)

        # LIMITS 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LIMITS (
                TEST_TYPE VARCHAR(2) PRIMARY KEY,
                MEAN_SIGMA REAL,
                MEAN_RANGE REAL,
                WORST_RANGE REAL,
                MEAN_RANGE_PERFORMANCE REAL,
                WORST_RANGE_PERFORMANCE REAL,
                MEAN_RANGE_SECOND REAL,
                WORST_RANGE_SECOND REAL
            )
        """)

    def _create_result_tables(self, cursor):
        """결과 테이블 생성 (TEST_RESULTS, TEST_AXIS_RESULTS, TEST_SAMPLES)"""
        # TEST_RESULTS 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TEST_RESULTS (
                ID_COL INTEGER PRIMARY KEY AUTOINCREMENT,
                DATE DATETIME,
                CODE VARCHAR(20),
                SERIAL_NUMBER VARCHAR(10),
                OPERATOR VARCHAR(20),
                TEST VARCHAR(2),
                RESULT VARCHAR(2),
                MEAN_SIGMA REAL,
                MEAN_RANGE REAL,
                WORST_SIGMA REAL,
                WORST_RANGE REAL,
                MEAN_SIGMA_LIMIT REAL,
                MEAN_RANGE_LIMIT REAL,
                WORST_RANGE_LIMIT REAL,
                SECOND_TEST VARCHAR(1) DEFAULT 'N'
            )
        """)

        # TEST_AXIS_RESULTS 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TEST_AXIS_RESULTS (
                ID_COL INT,
                AXIS SMALLINT,
                DIR VARCHAR(2),
                SIGMA REAL,
                RANGE REAL,
                RESULT VARCHAR(2),
                NCYCLES INT,
                SECOND_TEST VARCHAR(1) DEFAULT 'N',
                PRIMARY KEY (ID_COL, AXIS)
            )
        """)

        # TEST_SAMPLES 테이블
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS TEST_SAMPLES (
                ID_COL INT,
                AXIS SMALLINT,
                CYCLE SMALLINT,
                VALUE REAL,
                SECOND_TEST VARCHAR(1) DEFAULT 'N',
                WORST_DATUM VARCHAR(1) DEFAULT 'N',
                PRIMARY KEY (ID_COL, AXIS, CYCLE)
            )
        """)

    def _create_measure_tables(self, cursor):
        """측정값 테이블 생성 (MEASURES)"""
        # MEASURES 테이블 (현재 측정값)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS MEASURES (
                AXIS SMALLINT,
                CYCLE INT,
                VALUE REAL,
                SECOND_TEST VARCHAR(1) DEFAULT 'N',
                WORST_DATUM VARCHAR(1) DEFAULT 'N',
                PRIMARY KEY (AXIS, CYCLE)
            )
        """)

    def _insert_default_data(self):
        """기본 데이터 삽입"""
        cursor = self.conn.cursor()

        # 기본 Setup 추가
        cursor.execute("""
            INSERT OR IGNORE INTO SETUP (TEST_TYPE, NCYCLES, NAXIS, NWORSTDATUMS, SIGMA_TEST, RANGE_TEST)
            VALUES ('ST', 100, 4, 1, 1, 1)
        """)

        # 기본 Limits 추가
        cursor.execute("""
            INSERT OR IGNORE INTO LIMITS (TEST_TYPE, MEAN_SIGMA, MEAN_RANGE, WORST_RANGE)
            VALUES ('ST', 0.005, 0.010, 0.015)
        """)

        self.conn.commit()

    # --- OPERATORS ---
    def get_operators(self) -> List[str]:
        """작업자 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT OPERATOR FROM OPERATORS ORDER BY OPERATOR")
        return [row["OPERATOR"] for row in cursor.fetchall()]

    def add_operator(self, operator: str):
        """작업자 추가"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO OPERATORS (OPERATOR) VALUES (?)", (operator,)
        )
        self.conn.commit()

    # --- CODES ---
    def get_codes(self) -> List[CodeInfo]:
        """코드 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM CODES ORDER BY CODE")
        results = []

        # 컬럼명 가져오기
        col_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        for row in cursor.fetchall():
            results.append(
                CodeInfo(
                    code=_safe_get(row, col_names, "CODE", default=""),
                    naxis=int(_safe_get(row, col_names, "NAXIS", default=4) or 4),
                    probe_type=_safe_get(row, col_names, "PROBE_TYPE", default=""),
                    x_plus_dir=int(
                        _safe_get(row, col_names, "X_PLUS_DIR", "XPLUS_DIR", 1) or 1
                    ),
                    x_minus_dir=int(
                        _safe_get(row, col_names, "X_MINUS_DIR", "XMINUS_DIR", 1) or 1
                    ),
                    y_plus_dir=int(
                        _safe_get(row, col_names, "Y_PLUS_DIR", "YPLUS_DIR", 1) or 1
                    ),
                    y_minus_dir=int(
                        _safe_get(row, col_names, "Y_MINUS_DIR", "YMINUS_DIR", 1) or 1
                    ),
                    z_minus_dir=int(
                        _safe_get(row, col_names, "Z_MINUS_DIR", "ZMINUS_DIR", 1) or 1
                    ),
                )
            )
        return results

    def get_code_list(self) -> List[str]:
        """코드 문자열 목록 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT CODE FROM CODES ORDER BY CODE")
        return [row["CODE"] for row in cursor.fetchall()]

    def get_code_info(self, code: str) -> Optional[CodeInfo]:
        """특정 코드 정보 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM CODES WHERE CODE = ?", (code,))
        row = cursor.fetchone()
        if row:
            col_names = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )

            return CodeInfo(
                code=_safe_get(row, col_names, "CODE", default=""),
                naxis=int(_safe_get(row, col_names, "NAXIS", default=4) or 4),
                probe_type=_safe_get(row, col_names, "PROBE_TYPE", default=""),
            )
        return None

    def add_code(self, code_info: CodeInfo):
        """코드 추가"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO CODES
            (CODE, NAXIS, PROBE_TYPE, XPLUS_DIR, XMINUS_DIR, YPLUS_DIR, YMINUS_DIR, ZMINUS_DIR)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                code_info.code,
                code_info.naxis,
                code_info.probe_type,
                code_info.x_plus_dir,
                code_info.x_minus_dir,
                code_info.y_plus_dir,
                code_info.y_minus_dir,
                code_info.z_minus_dir,
            ),
        )
        self.conn.commit()

    def delete_code(self, code: str):
        """코드 삭제"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM CODES WHERE CODE = ?", (code,))
        self.conn.commit()

    def delete_test_result(self, id_col: int):
        """테스트 결과 및 관련 데이터 삭제"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM TEST_SAMPLES WHERE ID_COL = ?", (id_col,))
        cursor.execute("DELETE FROM TEST_AXIS_RESULTS WHERE ID_COL = ?", (id_col,))
        cursor.execute("DELETE FROM TEST_RESULTS WHERE ID_COL = ?", (id_col,))
        self.conn.commit()

    def search_by_serial_number(self, serial_number: str) -> List[Tuple[int, str, str]]:
        """시리얼 번호로 테스트 결과 검색"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT ID_COL, CODE, SERIAL_NUMBER FROM TEST_RESULTS
            WHERE SERIAL_NUMBER LIKE ? ORDER BY ID_COL DESC
        """,
            (f"%{serial_number}%",),
        )
        return [
            (row["ID_COL"], row["CODE"] or "", row["SERIAL_NUMBER"] or "")
            for row in cursor.fetchall()
        ]

    # --- SETUP ---
    def get_setup(self, test_type: str = "ST") -> Optional[SetupInfo]:
        """설정 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM SETUP WHERE TEST_TYPE = ?", (test_type,))
        row = cursor.fetchone()
        if row:
            return SetupInfo(
                test_type=row["TEST_TYPE"],
                ncycles=row["NCYCLES"],
                naxis=row["NAXIS"],
                nworstdatums=row["NWORSTDATUMS"],
                sigma_test=bool(row["SIGMA_TEST"]),
                range_test=bool(row["RANGE_TEST"]),
            )
        return None

    def save_setup(self, setup: SetupInfo):
        """설정 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO SETUP
            (TEST_TYPE, NCYCLES, NAXIS, NWORSTDATUMS, SIGMA_TEST, RANGE_TEST)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                setup.test_type,
                setup.ncycles,
                setup.naxis,
                setup.nworstdatums,
                setup.sigma_test,
                setup.range_test,
            ),
        )
        self.conn.commit()

    # --- LIMITS ---
    def get_limits(self, test_type: str = "ST") -> Optional[LimitInfo]:
        """한계값 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM LIMITS WHERE TEST_TYPE = ?", (test_type,))
        row = cursor.fetchone()
        if row:
            # 컬럼 이름 목록 가져오기 (동적으로 처리)
            col_names = [desc[0] for desc in cursor.description]

            return LimitInfo(
                test_type=_safe_get(row, col_names, "TEST_TYPE", default="ST"),
                mean_sigma=_safe_get(row, col_names, "MEAN_SIGMA", default=0.0),
                mean_range=_safe_get(row, col_names, "MEAN_RANGE", default=0.0),
                worst_range=_safe_get(row, col_names, "WORST_RANGE", default=0.0),
                mean_range_performance=_safe_get(
                    row, col_names, "MEAN_RANGE_PERFORMANCE", default=0.0
                ),
                worst_range_performance=_safe_get(
                    row, col_names, "WORST_RANGE_PERFORMANCE", default=0.0
                ),
                mean_range_second=_safe_get(
                    row, col_names, "MEAN_RANGE_SECOND", default=0.0
                ),
                worst_range_second=_safe_get(
                    row, col_names, "WORST_RANGE_SECOND", default=0.0
                ),
            )
        return None

    def save_limits(self, limits: LimitInfo):
        """한계값 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO LIMITS
            (TEST_TYPE, MEAN_SIGMA, MEAN_RANGE, WORST_RANGE,
             MEAN_RANGE_PERFORMANCE, WORST_RANGE_PERFORMANCE,
             MEAN_RANGE_SECOND, WORST_RANGE_SECOND)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                limits.test_type,
                limits.mean_sigma,
                limits.mean_range,
                limits.worst_range,
                limits.mean_range_performance,
                limits.worst_range_performance,
                limits.mean_range_second,
                limits.worst_range_second,
            ),
        )
        self.conn.commit()
        self.conn.commit()

    # --- TEST_RESULTS ---
    def save_test_result(self, result: TestResult) -> int:
        """테스트 결과 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO TEST_RESULTS
            (DATE, CODE, SERIAL_NUMBER, OPERATOR, TEST, RESULT,
             MEAN_SIGMA, MEAN_RANGE, WORST_SIGMA, WORST_RANGE,
             MEAN_SIGMA_LIMIT, MEAN_RANGE_LIMIT, WORST_RANGE_LIMIT, SECOND_TEST)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.date.isoformat(),
                result.code,
                result.serial_number,
                result.operator,
                result.test_type,
                result.result,
                result.mean_sigma,
                result.mean_range,
                result.worst_sigma,
                result.worst_range,
                result.mean_sigma_limit,
                result.mean_range_limit,
                result.worst_range_limit,
                result.second_test,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_test_result(self, id_col: int) -> Optional[TestResult]:
        """특정 테스트 결과 조회"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM TEST_RESULTS WHERE ID_COL = ?
        """,
            (id_col,),
        )
        row = cursor.fetchone()
        if row:
            col_names = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )

            date_str = _safe_get(row, col_names, "DATE")
            try:
                date_val = (
                    datetime.fromisoformat(date_str) if date_str else datetime.now()
                )
            except (ValueError, TypeError):
                date_val = datetime.now()

            return TestResult(
                id_col=_safe_get(row, col_names, "ID_COL", default=0),
                date=date_val,
                code=_safe_get(row, col_names, "CODE", default=""),
                serial_number=_safe_get(row, col_names, "SERIAL_NUMBER", default=""),
                operator=_safe_get(row, col_names, "OPERATOR", default=""),
                test_type=_safe_get(row, col_names, "TEST", default="ST"),
                result=_safe_get(row, col_names, "RESULT", default=""),
                mean_sigma=float(
                    _safe_get(row, col_names, "MEAN_SIGMA", default=0.0) or 0.0
                ),
                mean_range=float(
                    _safe_get(row, col_names, "MEAN_RANGE", default=0.0) or 0.0
                ),
                worst_sigma=float(
                    _safe_get(row, col_names, "WORST_SIGMA", default=0.0) or 0.0
                ),
                worst_range=float(
                    _safe_get(row, col_names, "WORST_RANGE", default=0.0) or 0.0
                ),
                mean_sigma_limit=float(
                    _safe_get(row, col_names, "MEAN_SIGMA_LIMIT", default=0.0) or 0.0
                ),
                mean_range_limit=float(
                    _safe_get(row, col_names, "MEAN_RANGE_LIMIT", default=0.0) or 0.0
                ),
                worst_range_limit=float(
                    _safe_get(row, col_names, "WORST_RANGE_LIMIT", default=0.0) or 0.0
                ),
                second_test=_safe_get(row, col_names, "SECOND_TEST", default="N"),
            )
        return None

    def get_last_id(self) -> int:
        """마지막 ID 조회"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(ID_COL) as max_id FROM TEST_RESULTS")
        row = cursor.fetchone()
        return row["max_id"] if row and row["max_id"] else 0

    def get_recent_ids(self, limit: int = 50) -> List[Tuple[int, str, str]]:
        """최근 테스트 ID 목록 조회 (ID, Code, Serial)"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT ID_COL, CODE, SERIAL_NUMBER FROM TEST_RESULTS
            ORDER BY ID_COL DESC LIMIT ?
        """,
            (limit,),
        )
        return [
            (row["ID_COL"], row["CODE"] or "", row["SERIAL_NUMBER"] or "")
            for row in cursor.fetchall()
        ]

    # --- TEST_AXIS_RESULTS ---
    def save_axis_result(self, result: AxisResult):
        """축별 결과 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO TEST_AXIS_RESULTS
            (ID_COL, AXIS, DIR, SIGMA, RANGE, RESULT, NCYCLES, SECOND_TEST)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                result.id_col,
                result.axis,
                result.direction,
                result.sigma,
                result.range_val,
                result.result,
                result.ncycles,
                result.second_test,
            ),
        )
        self.conn.commit()

    def get_axis_results(self, id_col: int) -> List[AxisResult]:
        """축별 결과 조회"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM TEST_AXIS_RESULTS WHERE ID_COL = ? ORDER BY AXIS", (id_col,)
        )
        results = []
        for row in cursor.fetchall():
            # axis 값을 int로 변환 (문자열일 수 있음)
            axis_val = row["AXIS"]
            try:
                axis_val = int(axis_val) if axis_val is not None else 0
            except (ValueError, TypeError):
                axis_val = 0

            results.append(
                AxisResult(
                    id_col=row["ID_COL"],
                    axis=axis_val,
                    direction=row["DIR"] or "",
                    sigma=float(row["SIGMA"] or 0.0),
                    range_val=float(row["RANGE"] or 0.0),
                    result=row["RESULT"] or "",
                    ncycles=int(row["NCYCLES"] or 0),
                    second_test=row["SECOND_TEST"] or "N",
                )
            )
        return results

    # --- TEST_SAMPLES ---
    def save_sample(
        self,
        id_col: int,
        axis: int,
        cycle: int,
        value: float,
        second_test: str = "N",
        worst_datum: str = "N",
    ):
        """샘플 데이터 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO TEST_SAMPLES
            (ID_COL, AXIS, CYCLE, VALUE, SECOND_TEST, WORST_DATUM)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (id_col, axis, cycle, value, second_test, worst_datum),
        )
        self.conn.commit()

    # --- MEASURES (현재 측정값) ---
    def clear_measures(self):
        """현재 측정값 초기화"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM MEASURES")
        self.conn.commit()

    def save_measure(
        self,
        axis: int,
        cycle: int,
        value: float,
        second_test: str = "N",
        worst_datum: str = "N",
    ):
        """현재 측정값 저장"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO MEASURES (AXIS, CYCLE, VALUE, SECOND_TEST, WORST_DATUM)
            VALUES (?, ?, ?, ?, ?)
        """,
            (axis, cycle, value, second_test, worst_datum),
        )
        self.conn.commit()

    def get_measures(self, axis: int = None) -> List[Tuple]:
        """현재 측정값 조회"""
        cursor = self.conn.cursor()
        if axis:
            cursor.execute(
                "SELECT * FROM MEASURES WHERE AXIS = ? ORDER BY CYCLE", (axis,)
            )
        else:
            cursor.execute("SELECT * FROM MEASURES ORDER BY AXIS, CYCLE")
        return cursor.fetchall()

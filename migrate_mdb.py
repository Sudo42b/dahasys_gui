"""
MDB to SQLite Migration Script
기존 Access DB (Minias.mdb)에서 SQLite로 데이터 마이그레이션
"""

import sqlite3
import os
import sys
from typing import Optional, Dict, List
from datetime import datetime

# pyodbc 설치 필요: pip install pyodbc
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    print("Warning: pyodbc not installed. Run: pip install pyodbc")


# Access 타입 -> SQLite 타입 매핑
TYPE_MAP = {
    'COUNTER': 'INTEGER PRIMARY KEY AUTOINCREMENT',
    'LONG': 'INTEGER',
    'INTEGER': 'INTEGER',
    'SHORT': 'INTEGER',
    'BYTE': 'INTEGER',
    'DOUBLE': 'REAL',
    'SINGLE': 'REAL',
    'CURRENCY': 'REAL',
    'DECIMAL': 'REAL',
    'VARCHAR': 'TEXT',
    'CHAR': 'TEXT',
    'TEXT': 'TEXT',
    'LONGCHAR': 'TEXT',
    'MEMO': 'TEXT',
    'DATETIME': 'TEXT',
    'BIT': 'INTEGER',
    'YESNO': 'INTEGER',
    'BINARY': 'BLOB',
    'LONGBINARY': 'BLOB',
    'GUID': 'TEXT',
}


def connect_mdb(mdb_path: str) -> Optional[pyodbc.Connection]:
    """Access MDB 파일 연결"""
    if not PYODBC_AVAILABLE:
        print("Error: pyodbc is required for MDB connection")
        return None

    if not os.path.exists(mdb_path):
        print(f"Error: MDB file not found: {mdb_path}")
        return None

    # Microsoft Access ODBC Driver
    drivers = [
        'Microsoft Access Driver (*.mdb, *.accdb)',
        'Microsoft Access Driver (*.mdb)',
    ]

    conn = None
    for driver in drivers:
        try:
            conn_str = f'DRIVER={{{driver}}};DBQ={mdb_path};'
            conn = pyodbc.connect(conn_str)
            print(f"Connected using driver: {driver}")
            break
        except pyodbc.Error:
            continue

    if not conn:
        print("Error: Could not connect to MDB. Install Microsoft Access Database Engine:")
        print("https://www.microsoft.com/en-us/download/details.aspx?id=54920")
        return None

    return conn


def get_mdb_tables(mdb_conn: pyodbc.Connection) -> List[str]:
    """MDB 테이블 목록 조회"""
    cursor = mdb_conn.cursor()
    tables = []
    for row in cursor.tables(tableType='TABLE'):
        if not row.table_name.startswith('MSys'):  # 시스템 테이블 제외
            tables.append(row.table_name)
    return tables


def get_table_schema(mdb_conn: pyodbc.Connection, table_name: str) -> List[Dict]:
    """테이블 스키마 조회"""
    cursor = mdb_conn.cursor()
    columns = []
    for col in cursor.columns(table=table_name):
        columns.append({
            'name': col.column_name,
            'type': col.type_name.upper(),
            'size': col.column_size,
            'nullable': col.nullable
        })
    return columns


def sanitize_name(name: str) -> str:
    """테이블/컬럼 이름 정규화 (공백, 특수문자 처리)"""
    # 특수문자 변환
    result = name.replace('+', 'PLUS').replace('-', 'MINUS')
    # 공백을 언더스코어로
    result = result.replace(' ', '_')
    # 특수문자 제거 (한글은 유지)
    # 알파벳, 숫자, 언더스코어, 한글만 허용
    sanitized = ''.join(c for c in result if c.isalnum() or c == '_' or '\uac00' <= c <= '\ud7a3')
    return sanitized


def map_type(access_type: str) -> str:
    """Access 타입을 SQLite 타입으로 매핑"""
    access_type = access_type.upper()
    for key, value in TYPE_MAP.items():
        if key in access_type:
            return value
    return 'TEXT'


def create_sqlite_table(sqlite_conn: sqlite3.Connection, table_name: str,
                        columns: List[Dict]) -> bool:
    """SQLite 테이블 생성"""
    cursor = sqlite_conn.cursor()

    sqlite_table = sanitize_name(table_name)

    # 컬럼 정의 생성
    col_defs = []
    for col in columns:
        col_name = sanitize_name(col['name'])
        col_type = map_type(col['type'])

        # AUTOINCREMENT는 한 번만
        if 'AUTOINCREMENT' in col_type:
            col_defs.append(f'"{col_name}" {col_type}')
        else:
            col_defs.append(f'"{col_name}" {col_type}')

    create_sql = f'CREATE TABLE IF NOT EXISTS "{sqlite_table}" ({", ".join(col_defs)})'

    try:
        cursor.execute(create_sql)
        sqlite_conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"  Error creating table {sqlite_table}: {e}")
        return False


def migrate_table(mdb_conn: pyodbc.Connection, sqlite_conn: sqlite3.Connection,
                 table_name: str) -> int:
    """테이블 데이터 마이그레이션"""
    mdb_cursor = mdb_conn.cursor()
    sqlite_cursor = sqlite_conn.cursor()

    # 테이블 이름 정규화
    sqlite_table = sanitize_name(table_name)

    try:
        # 스키마 조회 및 테이블 생성
        columns = get_table_schema(mdb_conn, table_name)
        if not columns:
            print(f"  - {table_name}: No columns found")
            return 0

        if not create_sqlite_table(sqlite_conn, table_name, columns):
            return 0

        # 원본 데이터 조회
        mdb_cursor.execute(f'SELECT * FROM [{table_name}]')
        rows = mdb_cursor.fetchall()

        if not rows:
            print(f"  - {table_name} -> {sqlite_table}: No data")
            return 0

        # 컬럼 이름 정규화
        sqlite_columns = [sanitize_name(col['name']) for col in columns]

        # INSERT 쿼리 생성
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join([f'"{c}"' for c in sqlite_columns])
        insert_sql = f'INSERT OR REPLACE INTO "{sqlite_table}" ({col_names}) VALUES ({placeholders})'

        # 데이터 삽입
        inserted = 0
        for row in rows:
            try:
                # datetime 객체를 문자열로 변환
                converted_row = []
                for val in row:
                    if isinstance(val, datetime):
                        converted_row.append(val.isoformat())
                    else:
                        converted_row.append(val)

                sqlite_cursor.execute(insert_sql, tuple(converted_row))
                inserted += 1
            except sqlite3.Error as e:
                if inserted == 0:  # 첫 번째 에러만 출력
                    print(f"  Warning: Insert error in {table_name}: {e}")

        sqlite_conn.commit()
        print(f"  - {table_name} -> {sqlite_table}: {inserted} rows migrated")
        return inserted

    except Exception as e:
        print(f"  Error migrating {table_name}: {e}")
        return 0


def migrate_mdb_to_sqlite(mdb_path: str, sqlite_path: str) -> bool:
    """전체 마이그레이션 수행"""
    print(f"Migration: {mdb_path} -> {sqlite_path}")
    print("-" * 60)

    # MDB 연결
    mdb_conn = connect_mdb(mdb_path)
    if not mdb_conn:
        return False

    # 기존 SQLite 파일 백업/삭제
    if os.path.exists(sqlite_path):
        backup_path = sqlite_path + '.backup'
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(sqlite_path, backup_path)
            print(f"Existing database backed up to: {backup_path}")
        except Exception as e:
            print(f"Warning: Could not backup existing database: {e}")

    # SQLite 연결
    sqlite_conn = sqlite3.connect(sqlite_path)

    # 테이블 목록 확인
    tables = get_mdb_tables(mdb_conn)
    print(f"\nFound {len(tables)} tables in MDB:")
    for t in tables:
        print(f"  - {t}")
    print()

    # 주요 테이블 우선 마이그레이션 (종속성 순서)
    priority_tables = [
        'OPERATORS', 'CODES', 'SETUP', 'LIMITS', 'EXCEL SETUP',
        'TEST RESULTS', 'TEST AXIS RESULTS', 'TEST SAMPLES', 'MEASURES'
    ]

    # 마이그레이션 순서 정렬
    ordered_tables = []
    for pt in priority_tables:
        if pt in tables:
            ordered_tables.append(pt)
            tables.remove(pt)
    ordered_tables.extend(tables)  # 나머지 테이블

    # 각 테이블 마이그레이션
    print("Migrating tables...")
    total_rows = 0
    for table in ordered_tables:
        rows = migrate_table(mdb_conn, sqlite_conn, table)
        total_rows += rows

    # 정리
    mdb_conn.close()
    sqlite_conn.close()

    print()
    print(f"Migration completed! Total rows: {total_rows}")
    print(f"SQLite database: {sqlite_path}")
    return True


def main():
    """메인 함수"""
    # 기본 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mdb_path = os.path.join(script_dir, 'MINIAS', 'Minias.mdb')
    sqlite_path = os.path.join(script_dir, 'minias.db')

    # 명령줄 인수 처리
    if len(sys.argv) >= 2:
        mdb_path = sys.argv[1]
    if len(sys.argv) >= 3:
        sqlite_path = sys.argv[2]

    print("=" * 60)
    print("MINIAS MDB to SQLite Migration Tool")
    print("=" * 60)
    print()

    if not PYODBC_AVAILABLE:
        print("Error: pyodbc module is required")
        print("Install with: pip install pyodbc")
        print()
        print("Also requires Microsoft Access Database Engine:")
        print("https://www.microsoft.com/en-us/download/details.aspx?id=54920")
        return 1

    if not os.path.exists(mdb_path):
        print(f"Error: MDB file not found: {mdb_path}")
        print()
        print("Usage: python migrate_mdb.py [mdb_path] [sqlite_path]")
        return 1

    success = migrate_mdb_to_sqlite(mdb_path, sqlite_path)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())

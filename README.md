# MINIAS - Probe Testing System (Python 재구현)

Visual Basic 6.0 기반 MINIAS 프로그램을 Python으로 재구현한 프로젝트입니다.

## 기능

- **프로브 테스트**: 측정 장비와 시리얼 통신을 통한 자동 측정
- **데이터 관리**: SQLite 데이터베이스를 통한 테스트 결과 저장/조회
- **통계 분석**: Sigma/Range 계산 및 합격/불합격 자동 판정
- **Excel 출력**: 테스트 결과를 Excel 파일로 내보내기
- **인증서 출력**: PDF 형식의 테스트 인증서 생성

## 설치

### 요구사항
- Python 3.10 이상
- Windows (시리얼 통신용)

### 패키지 설치

```bash
# uv 사용 시
uv pip install pyserial openpyxl reportlab

# pip 사용 시
pip install pyserial openpyxl reportlab
```

### (선택) Access MDB 마이그레이션용
```bash
pip install pyodbc
```
또한 Microsoft Access Database Engine이 필요합니다:
https://www.microsoft.com/en-us/download/details.aspx?id=54920

## 실행

```bash
python minias_app.py
```

또는 설치 후:
```bash
minias
```

## 사용법

### 1. 기본 설정

1. **Code 등록**: 프로브 코드와 타입 정보 등록
2. **Operator 등록**: 작업자 등록 (최초 사용 시 자동 등록)
3. **Limits 설정**: Limits 버튼으로 한계값 설정

### 2. 테스트 실행

1. Code 선택
2. Serial Number 입력
3. Operator 선택
4. **Start** 버튼 클릭
5. 측정 완료 후 자동으로 결과 저장

### 3. 결과 출력

- **Print Certificate**: PDF 인증서 출력
- Excel 출력: 프로그램에서 테스트 결과를 Excel로 내보내기

## 시리얼 통신 설정

`MINIAS.INI` 파일에서 설정:
```ini
[Communication Port]=1
[Settings Communication Port]=9600,N,8,1
```

## 데이터베이스 마이그레이션

기존 Access MDB 데이터를 SQLite로 마이그레이션:

```bash
python migrate_mdb.py MINIAS/Minias.mdb minias.db
```

## 파일 구조

```
MINIAS_COMPLETE_PACKAGE/
├── minias_app.py          # 메인 애플리케이션
├── migrate_mdb.py         # MDB -> SQLite 마이그레이션
├── minias.db             # SQLite 데이터베이스
├── MINIAS.INI            # 설정 파일
├── MINIAS/               # 원본 VB6 프로그램
│   ├── MINIAS.EXE
│   ├── Minias.mdb
│   └── ...
├── figs/                 # 참고 이미지
│   └── demo.png
└── xsd_schemas/          # 데이터베이스 스키마
```

## 데이터베이스 테이블

| 테이블 | 설명 |
|--------|------|
| TEST_RESULTS | 테스트 결과 (메인) |
| TEST_AXIS_RESULTS | 축별 상세 결과 |
| TEST_SAMPLES | 측정 샘플 데이터 |
| CODES | 프로브 코드 마스터 |
| OPERATORS | 작업자 마스터 |
| LIMITS | 한계값 설정 |
| SETUP | 테스트 설정 |

## 기술 스택

- **GUI**: Tkinter
- **데이터베이스**: SQLite
- **시리얼 통신**: PySerial
- **Excel**: openpyxl
- **PDF**: reportlab

## 원본 VB6 프로그램 정보

- MINIAS.EXE: Visual Basic 6.0 실행 파일
- MSCOMM32.OCX: 시리얼 통신 컨트롤
- grid32.ocx: MSGrid 컨트롤
- miniasdll.dll: 비즈니스 로직 (Delphi)
- Minias.mdb: Access 데이터베이스

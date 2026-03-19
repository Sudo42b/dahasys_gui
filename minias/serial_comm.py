"""시리얼 통신 모듈"""

import queue
import threading
import time
import re
from typing import Optional, List, Dict, Tuple

# 시리얼 통신
try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    print("Warning: pyserial not installed. Serial communication disabled.")


class SerialCommunicator:
    """시리얼 통신 관리"""

    def __init__(self, port: str = "COM1", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.is_connected = False
        self.data_queue = queue.Queue()
        self.read_thread: Optional[threading.Thread] = None
        self.running = False

    @staticmethod
    def get_available_ports() -> List[str]:
        """사용 가능한 시리얼 포트 목록"""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def get_available_ports_detail() -> List[Dict]:
        """사용 가능한 시리얼 포트 상세 목록"""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        result = []
        for p in ports:
            result.append(
                {
                    "device": p.device,
                    "description": p.description or p.device,
                    "hwid": p.hwid or "",
                    "manufacturer": getattr(p, "manufacturer", "") or "",
                }
            )
        return sorted(result, key=lambda x: x["device"])

    @staticmethod
    def test_port(port: str, baudrate: int = 9600) -> Tuple[bool, str]:
        """포트 연결 테스트 (열기/닫기만 시도)"""
        if not SERIAL_AVAILABLE:
            return False, "pyserial 모듈이 설치되지 않았습니다"
        try:
            s = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
            s.close()
            return True, f"{port} 연결 성공"
        except serial.SerialException as e:
            return False, f"{port} 연결 실패: {e}"
        except Exception as e:
            return False, f"{port} 오류: {e}"

    def connect(self) -> bool:
        """시리얼 포트 연결"""
        if not SERIAL_AVAILABLE:
            print("Serial module not available")
            return False

        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
            self.is_connected = True
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()
            print(f"Serial connected: {self.port} @ {self.baudrate}")
            return True
        except serial.SerialException as e:
            print(f"Serial connection error ({self.port}): {e}")
            return False
        except Exception as e:
            print(f"Serial connection error ({self.port}): {e}")
            return False

    def disconnect(self):
        """연결 해제"""
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.is_connected = False

    def _serial_log(self, msg: str):
        """시리얼 디버그 로그를 파일과 콘솔에 동시 출력 (flush 보장)"""
        import sys

        print(msg, flush=True)
        try:
            with open("serial_debug.log", "a", encoding="utf-8") as f:
                f.write(f"{msg}\n")
        except Exception:
            pass

    def _read_loop(self):
        """백그라운드 읽기 루프 — CR(\r) 종단 프로토콜 대응

        터치센서 데이터 형식 (실측 확인됨):
          1터치 = [0x00] + [숫자값\r]
          예: b'\x00' 이후 b'911\r'

        전략:
        - readline()으로 한 줄 단위 읽기
        - NULL/공백 등은 strip()으로 제거
        - 유효한 라인만 큐에 넣음
        """
        self._serial_log("[Serial] _read_loop started (CR-terminated protocol)")

        while self.running and self.serial and self.serial.is_open:
            try:
                if self.serial.in_waiting > 0:
                    line = (
                        self.serial.readline().decode("ascii", errors="ignore").strip()
                    )
                    if line:
                        self._serial_log(f"[Serial] Received: {line!r}")
                        self.data_queue.put(line)
                else:
                    # 데이터 없으면 짧은 대기 (CPU 과부하 방지)
                    time.sleep(0.01)
            except Exception as e:
                self._serial_log(f"[Serial ERROR] {e}")
                time.sleep(0.05)

    def read_value(self, timeout: float = 1.0) -> Optional[float]:
        """측정값 읽기

        장비 데이터 형식 (실측 확인):
          '01A-000.0018'  →  축 prefix '01A' + 측정값 '-000.0018' (mm 단위)
          - 앞 2~3자: 축 번호(숫자) + 채널(영문자)
           - 나머지: 부호 + 숫자값 (mm 단위, 화면 표시 시 ×1000으로 μm 변환)
        """
        try:
            data = self.data_queue.get(timeout=timeout)

            # 축/채널 prefix 제거 후 숫자값만 추출
            # 예: '01A-000.0018' → prefix='01A', value_str='-000.0018'
            #     '0A1-000.0019' → prefix='0A1', value_str='-000.0019'
            #     '01A+000.0018' → prefix='01A', value_str='+000.0018'
            # prefix 없는 순수 숫자 ('911', '-0.0018') 도 허용

            # 1) 부호(+/-)를 구분자로 prefix와 숫자값 분리
            match = re.match(r"^([^-+.]*?)([-+]\d+\.?\d*)$", data)
            if match and match.group(1):
                prefix = match.group(1)
                value_str = match.group(2)
                self._serial_log(f"[Serial] Prefix='{prefix}', Value='{value_str}'")
            else:
                # 2) 부호 없는 경우: 영문자 뒤의 숫자를 값으로 추출
                match2 = re.match(r"^([0-9A-Za-z]*[A-Za-z])(\d+\.?\d*)$", data)
                if match2:
                    prefix = match2.group(1)
                    value_str = match2.group(2)
                    self._serial_log(f"[Serial] Prefix='{prefix}', Value='{value_str}'")
                else:
                    # 3) prefix 없는 순수 숫자 데이터
                    value_str = data.replace(",", ".")

            raw_value = float(value_str)

            # 유효성 검증: 비정상적으로 큰 값 필터
            if abs(raw_value) > 99999:
                self._serial_log(f"[Serial] Out of range skipped: {raw_value}")
                return None

            self._serial_log(f"[Serial] Parsed value={raw_value:.6f}")
            return raw_value
        except queue.Empty:
            return None
        except ValueError:
            self._serial_log(f"[Serial] Parse error skipped: {data!r}")
            return None

    def clear_buffer(self):
        """버퍼 초기화 - 큐와 시리얼 입력 버퍼 모두 비움"""
        # 큐 비우기
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break
        # 시리얼 입력 버퍼 비우기
        if self.serial and self.serial.is_open:
            self.serial.reset_input_buffer()
        # 잠시 대기 후 다시 큐 비우기 (읽기 스레드가 방금 넣은 데이터 제거)
        time.sleep(0.1)
        while not self.data_queue.empty():
            try:
                self.data_queue.get_nowait()
            except queue.Empty:
                break

"""대화상자 모듈"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional, Dict

from minias.models import LimitInfo
from minias.database import MiniasDatabase
from minias.serial_comm import SerialCommunicator


# =============================================================================
# 한계값 설정 대화상자
# =============================================================================


class LimitsDialog:
    """한계값 설정 대화상자"""

    def __init__(self, parent, db: MiniasDatabase, limits: Optional[LimitInfo]):
        self.db = db
        self.limits = limits or LimitInfo()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Limits Settings")
        self.dialog.geometry("400x280")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 변수
        self.var_mean_sigma = tk.StringVar(value=f"{self.limits.mean_sigma * 2000:.1f}")
        self.var_mean_range = tk.StringVar(value=f"{self.limits.mean_range * 1000:.1f}")
        self.var_worst_range = tk.StringVar(
            value=f"{self.limits.worst_range * 1000:.1f}"
        )

        # GUI
        frame = ttk.Frame(self.dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Test Type: ST", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, pady=10
        )

        ttk.Label(frame, text="Mean 2SIGMA Limit:").grid(
            row=1, column=0, sticky=tk.E, pady=5
        )
        ttk.Entry(frame, textvariable=self.var_mean_sigma, width=15).grid(
            row=1, column=1, pady=5
        )

        ttk.Label(frame, text="Mean Range Limit:").grid(
            row=2, column=0, sticky=tk.E, pady=5
        )
        ttk.Entry(frame, textvariable=self.var_mean_range, width=15).grid(
            row=2, column=1, pady=5
        )

        ttk.Label(frame, text="Worst Range Limit:").grid(
            row=3, column=0, sticky=tk.E, pady=5
        )
        ttk.Entry(frame, textvariable=self.var_worst_range, width=15).grid(
            row=3, column=1, pady=5
        )

        # 버튼
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="Save", command=self._save, width=10).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(
            btn_frame, text="Cancel", command=self.dialog.destroy, width=10
        ).pack(side=tk.LEFT, padx=10)

        self.dialog.wait_window()

    def _save(self):
        """저장"""
        try:
            self.limits.test_type = "ST"
            self.limits.mean_sigma = float(self.var_mean_sigma.get()) / 2000.0
            self.limits.mean_range = float(self.var_mean_range.get()) / 1000.0
            self.limits.worst_range = float(self.var_worst_range.get()) / 1000.0

            self.db.save_limits(self.limits)
            messagebox.showinfo("Success", "Limits saved successfully")
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid number format")


# =============================================================================
# 통신 설정 대화상자
# =============================================================================


class SettingsDialog:
    """통신 설정 대화상자"""

    BAUDRATES = ["9600", "19200", "38400", "57600", "115200"]

    def __init__(self, parent, config: Dict, callback):
        self.config = config.copy()
        self.callback = callback
        self.port_details: List[Dict] = []

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Communication Settings")
        self.dialog.geometry("520x520")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 변수
        self.var_port = tk.StringVar(value=self.config.get("port", "COM1"))
        self.var_baudrate = tk.StringVar(value=str(self.config.get("baudrate", 9600)))

        # GUI
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame, text="Communication Settings", font=("Arial", 11, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # COM Port
        ttk.Label(frame, text="COM Port:").grid(
            row=1, column=0, sticky=tk.E, pady=5, padx=10
        )

        # 사용 가능한 포트 목록 가져오기
        available_ports = SerialCommunicator.get_available_ports()
        if not available_ports:
            available_ports = [
                "COM1",
                "COM2",
                "COM3",
                "COM4",
                "COM5",
                "COM6",
                "COM7",
                "COM8",
            ]

        self.combo_port = ttk.Combobox(
            frame, textvariable=self.var_port, width=15, values=available_ports
        )
        self.combo_port.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.combo_port.bind("<<ComboboxSelected>>", self._on_port_selected)

        # Baudrate
        ttk.Label(frame, text="Baudrate:").grid(
            row=2, column=0, sticky=tk.E, pady=5, padx=10
        )
        self.combo_baudrate = ttk.Combobox(
            frame,
            textvariable=self.var_baudrate,
            width=15,
            values=self.BAUDRATES,
            state="readonly",
        )
        self.combo_baudrate.grid(row=2, column=1, sticky=tk.W, pady=5)

        # 포트 상세정보 라벨
        self.lbl_port_desc = ttk.Label(frame, text="", foreground="gray")
        self.lbl_port_desc.grid(row=3, column=0, columnspan=2, pady=5)

        # --- 포트 목록 Treeview ---
        tree_label = ttk.Label(frame, text="Detected Ports:", font=("Arial", 9, "bold"))
        tree_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 2))

        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=2)

        self.port_tree = ttk.Treeview(
            tree_frame,
            columns=("port", "description"),
            show="headings",
            height=5,
            selectmode="browse",
        )
        self.port_tree.heading("port", text="Port")
        self.port_tree.heading("description", text="Description")
        self.port_tree.column("port", width=80, anchor=tk.W)
        self.port_tree.column("description", width=380, anchor=tk.W)
        self.port_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.port_tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.port_tree.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.port_tree.configure(yscrollcommand=scrollbar.set)

        # 포트 상태 표시
        self.lbl_status = ttk.Label(frame, text="", foreground="gray")
        self.lbl_status.grid(row=6, column=0, columnspan=2, pady=5)

        # --- 버튼 행 1: Refresh + Test ---
        action_frame = ttk.Frame(frame)
        action_frame.grid(row=7, column=0, columnspan=2, pady=5)

        ttk.Button(
            action_frame, text="Refresh Ports", command=self._refresh_ports, width=14
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            action_frame,
            text="Test Connection",
            command=self._test_connection,
            width=14,
        ).pack(side=tk.LEFT, padx=5)

        # --- 버튼 행 2: Apply + Cancel ---
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=(10, 0))

        ttk.Button(btn_frame, text="Apply", command=self._apply, width=10).pack(
            side=tk.LEFT, padx=10
        )
        ttk.Button(
            btn_frame, text="Cancel", command=self.dialog.destroy, width=10
        ).pack(side=tk.LEFT, padx=10)

        # 초기 데이터 로드
        self._update_port_tree()
        self._on_port_selected()

        self.dialog.wait_window()

    def _get_port_list(self) -> List[str]:
        """사용 가능한 포트 목록 (device 이름만)"""
        self.port_details = SerialCommunicator.get_available_ports_detail()
        if self.port_details:
            return [p["device"] for p in self.port_details]
        return ["COM1", "COM2", "COM3", "COM4"]

    def _update_port_tree(self):
        """포트 상세 Treeview 업데이트"""
        for item in self.port_tree.get_children():
            self.port_tree.delete(item)

        self.port_details = SerialCommunicator.get_available_ports_detail()
        if self.port_details:
            for p in self.port_details:
                self.port_tree.insert(
                    "", tk.END, values=(p["device"], p["description"])
                )
            self.lbl_status.config(
                text=f"{len(self.port_details)} port(s) detected", foreground="green"
            )
        else:
            self.lbl_status.config(
                text="No serial ports detected. Check device connection.",
                foreground="red",
            )

    def _on_port_selected(self, event=None):
        """포트 선택 시 상세정보 표시"""
        selected_port = self.var_port.get()
        for p in self.port_details:
            if p["device"] == selected_port:
                desc = p["description"]
                if p["manufacturer"]:
                    desc += f" [{p['manufacturer']}]"
                self.lbl_port_desc.config(text=desc)
                return
        self.lbl_port_desc.config(text="")

    def _on_tree_select(self, event=None):
        """Treeview에서 포트 선택 시 combobox에 반영"""
        selection = self.port_tree.selection()
        if selection:
            item = self.port_tree.item(selection[0])
            port_device = item["values"][0]
            self.var_port.set(port_device)
            self._on_port_selected()

    def _refresh_ports(self):
        """포트 목록 새로고침"""
        available_ports = SerialCommunicator.get_available_ports()
        if not available_ports:
            available_ports = [
                "COM1",
                "COM2",
                "COM3",
                "COM4",
                "COM5",
                "COM6",
                "COM7",
                "COM8",
            ]
        self.combo_port["values"] = available_ports
        self._update_port_tree()

    def _test_connection(self):
        """선택된 포트의 연결 테스트"""
        port = self.var_port.get()
        baudrate = int(self.var_baudrate.get())
        if not port:
            messagebox.showwarning("Warning", "포트를 선택하세요.")
            return

        self.lbl_status.config(text=f"Testing {port}...", foreground="orange")
        self.dialog.update()

        success, message = SerialCommunicator.test_port(port, baudrate)
        if success:
            self.lbl_status.config(text=f"{port}: {message}", foreground="green")
        else:
            self.lbl_status.config(text=f"{port}: {message}", foreground="red")

    def _apply(self):
        """설정 적용"""
        self.config["port"] = self.var_port.get()
        self.config["baudrate"] = int(self.var_baudrate.get())

        if self.callback:
            self.callback(self.config)

        messagebox.showinfo(
            "Success",
            f"Settings applied:\nPort: {self.config['port']}\nBaudrate: {self.config['baudrate']}",
        )
        self.dialog.destroy()

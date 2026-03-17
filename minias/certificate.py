"""PDF 인증서 출력 모듈"""

import os
import traceback
from typing import List, Optional

# PDF 인증서 출력
try:
    from reportlab.lib.pagesizes import A4, A5
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        Image,
    )
    from reportlab.lib.units import mm

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: reportlab not installed. PDF certificate disabled.")

from minias.models import TestResult, AxisResult, CodeInfo, format_microns, format_2sigma_microns


class CertificateGenerator:
    """PDF 인증서 생성 (form.xlsx 양식 기반)"""

    def __init__(self):
        # 리소스 경로 — CWD 기준 (프로젝트 루트에서 실행)
        self.script_dir = os.getcwd()
        self.logo_path = os.path.join(self.script_dir, "resources", "logo.png")

    def generate(
        self,
        result: TestResult,
        axis_results: List[AxisResult],
        code_info: CodeInfo,
        output_path: str,
    ) -> bool:
        """인증서 PDF 생성 (form.xlsx 레이아웃과 동일)"""
        if not PDF_AVAILABLE:
            print("PDF generation not available - reportlab not installed")
            return False

        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=10 * mm,
                leftMargin=10 * mm,
                topMargin=10 * mm,
                bottomMargin=10 * mm,
            )

            styles = self._setup_styles()
            elements = []

            self._build_header(elements, styles, result, code_info)
            self._build_data_table(elements, styles, result, axis_results)
            self._build_footer(elements, styles, result)

            doc.build(elements)
            print(f"PDF saved to: {output_path}")
            return True

        except Exception as e:
            import traceback

            print(f"PDF generation error: {e}")
            traceback.print_exc()
            return False

    def _setup_styles(self) -> dict:
        """PDF 스타일 설정"""
        styles = getSampleStyleSheet()

        custom = {
            "base": styles,
            "center": ParagraphStyle(
                "CenterCell",
                parent=styles["Normal"],
                fontSize=7,
                alignment=TA_CENTER,
            ),
            "bold_center": ParagraphStyle(
                "BoldCenterCell",
                parent=styles["Normal"],
                fontSize=7,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            ),
            "title": ParagraphStyle(
                "TitleCell",
                parent=styles["Heading1"],
                fontSize=16,
                alignment=TA_CENTER,
                leading=20,
            ),
            "section": ParagraphStyle(
                "Section",
                parent=styles["Heading2"],
                fontSize=11,
                alignment=TA_LEFT,
                spaceAfter=3,
                spaceBefore=5,
                textColor=colors.black,
                backColor=colors.Color(0.9, 0.9, 0.9),
            ),
            "cycle_desc": ParagraphStyle(
                "CycleDesc",
                parent=styles["Normal"],
                fontSize=7,
                alignment=TA_CENTER,
                spaceBefore=3,
                spaceAfter=3,
            ),
        }
        return custom

    def _build_header(
        self,
        elements: list,
        styles: dict,
        result: TestResult,
        code_info: CodeInfo,
    ) -> None:
        """헤더 섹션 — 로고, 타이틀, 프로브 정보"""
        # ========== Row 1: 로고 (좌측) + INSPECTION SHEET (가운데) ==========
        logo_cell = ""
        if os.path.exists(self.logo_path):
            try:
                logo_cell = Image(self.logo_path, width=25 * mm, height=25 * mm)
            except Exception as e:
                print(f"Logo load error: {e}")
                logo_cell = ""

        title_para = Paragraph("<b>INSPECTION SHEET</b>", styles["title"])

        header_data = [[logo_cell, title_para]]
        header_table = Table(header_data, colWidths=[30 * mm, 150 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ]
            )
        )
        elements.append(header_table)
        elements.append(Spacer(1, 5 * mm))

        # ========== Probe Model / Code / Serial (셀 병합 및 가운데정렬) ==========
        probe_type = code_info.probe_type if code_info else ""
        info_data = [
            [
                "Probe Model",
                probe_type,
                "Code",
                result.code,
                "Serial",
                result.serial_number,
            ],
        ]
        info_table = Table(
            info_data,
            colWidths=[25 * mm, 45 * mm, 15 * mm, 40 * mm, 15 * mm, 40 * mm],
        )
        info_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
                    ("FONTNAME", (4, 0), (4, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (4, 0), (4, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (0, 0), (0, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (4, 0), (4, 0), colors.Color(0.85, 0.85, 0.85)),
                ]
            )
        )
        elements.append(info_table)
        elements.append(Spacer(1, 5 * mm))

    def _build_data_table(
        self,
        elements: list,
        styles: dict,
        result: TestResult,
        axis_results: List[AxisResult],
    ) -> None:
        """데이터 테이블 섹션 — 테스트 사이클 설명 및 축별 결과"""
        # ========== TEST CYCLE DESCRIPTION ==========
        elements.append(Paragraph("TEST CYCLE DESCRIPTION", styles["section"]))

        # ========== Cycle sequence 설명 ==========
        ncycles = 100
        if axis_results and len(axis_results) > 0:
            ncycles = axis_results[0].ncycles or 100
            # Fix: If old data or off-by-one stored ncycles as 99, display 100
            if ncycles == 99:
                ncycles = 100

        cycle_desc = (
            f"Cycle sequence: X+ X- Y+ Y- Z- touch direction repeated {ncycles} times"
        )
        elements.append(Paragraph(cycle_desc, styles["base"]["Normal"]))
        elements.append(Spacer(1, 3 * mm))

        # ========== Direction / Range 테이블 (셀 병합 및 가운데정렬) ==========
        dir_labels = ["Y-", "X+", "Y+", "X-"]

        # 축별 Range 데이터 (소수점 1자리)
        axis_ranges = []
        axis_2sigmas = []
        for i in range(4):
            if i < len(axis_results):
                axis_ranges.append(f"{format_microns(axis_results[i].range_val)}")
                axis_2sigmas.append(f"{format_2sigma_microns(axis_results[i].sigma)}")
            else:
                axis_ranges.append("-")
                axis_2sigmas.append("-")

        # Mean Range 계산
        mean_range_val = f"{format_microns(result.mean_range)}"

        # micron 단위를 데이터 셀에 병합 (9열 → 5열)
        def _fmt_micron(val: str) -> str:
            """데이터 값에 micron 단위 병합 (빈 값이면 그대로 반환)"""
            return f"{val} micron" if val and val != "-" else val

        axis_data = [
            [
                "Direction",
                dir_labels[0],
                dir_labels[1],
                dir_labels[2],
                dir_labels[3],
            ],
            [
                f"R({ncycles})={int(result.worst_range_limit)} micron",
                _fmt_micron(axis_ranges[0]),
                _fmt_micron(axis_ranges[1]),
                _fmt_micron(axis_ranges[2]),
                _fmt_micron(axis_ranges[3]),
            ],
            [
                f"R({ncycles})={int(result.worst_range_limit)} micron",
                f"{mean_range_val} micron",
                f"{sum([float(val) for val in axis_ranges])/len(axis_ranges)} micron",
            ],
        ]

        col_w = 32 * mm
        axis_table = Table(
            axis_data,
            colWidths=[40 * mm, col_w, col_w, col_w, col_w],
        )
        axis_table.setStyle(
            TableStyle( #세번째행은 합하여 평균값으로 표시, 첫번째열은 R(ncycles)=worst_range_limit micron으로 표시
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (1, 0), (1, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (3, 0), (3, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (4, 0), (4, 0), colors.Color(0.85, 0.85, 0.85)),
                    
                    
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    # 3번쨰 행의 1, 2, 3, 4열을 병합
                    ("SPAN", (1, 2), (4, 2)),
                    ("SPAN", (1, 3), (4, 3)),
                    ("SPAN", (1, 4), (4, 4)),
                ]
            )
        )
        elements.append(axis_table)
        elements.append(Spacer(1, 3 * mm))

        self._build_z_table(elements)

    def _build_z_table(self, elements: list) -> None:
        """Z축 방향 테이블 — Un direct direction (Z-) 및 Dia"""
        # ========== Row 11-12: Un direct direction (Z-) — 3열 구조 ==========
        col_w = 32 * mm *2
        z_data = [
            ["Un direct direction", "Z-", "Dia"], #가운데 정렬된 헤더
            ["", "micron", "micron"],
        ]
        z_table = Table(
            z_data,
            colWidths=[40 * mm, col_w, col_w],
        )
        z_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BACKGROUND", (0, 0), (0, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (1, 0), (1, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BACKGROUND", (2, 0), (2, 0), colors.Color(0.85, 0.85, 0.85)),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(z_table)
        elements.append(Spacer(1, 8 * mm))

    def _build_footer(
        self,
        elements: list,
        styles: dict,
        result: TestResult,
    ) -> None:
        """푸터 섹션 — 날짜, 판정 결과, 작업자"""
        # ========== 날짜 / TEST OK or NG / 작업자 (가운데정렬) ==========
        result_text = "TEST OK" if result.result == "OK" else "TEST NG"
        result_color = colors.darkgreen if result.result == "OK" else colors.red

        result_para_style = ParagraphStyle(
            "ResultText",
            parent=styles["base"]["Normal"],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=result_color,
            fontName="Helvetica-Bold",
        )

        footer_data = [
            [
                result.date.strftime("%Y-%m-%d"),
                Paragraph(f"<b>{result_text}</b>", result_para_style),
                f"operator: {result.operator}",
            ]
        ]
        footer_table = Table(footer_data, colWidths=[50 * mm, 60 * mm, 70 * mm])
        footer_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(footer_table)

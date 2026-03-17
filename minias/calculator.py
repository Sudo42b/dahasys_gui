"""테스트 계산 로직"""

import statistics
from typing import List

from minias.models import LimitInfo


class TestCalculator:
    """측정값 분석 및 합격/불합격 판정"""

    @staticmethod
    def calculate_sigma(values: List[float]) -> float:
        """표준편차 계산 (샘플)"""
        if len(values) < 2:
            return 0.0
        return statistics.stdev(values)

    @staticmethod
    def calculate_range(values: List[float]) -> float:
        """범위 계산 (최대 - 최소)"""
        if not values:
            return 0.0
        return max(values) - min(values)

    @staticmethod
    def calculate_mean(values: List[float]) -> float:
        """평균 계산"""
        if not values:
            return 0.0
        return statistics.mean(values)

    @staticmethod
    def evaluate_axis_result(
        sigma: float,
        range_val: float,
        limits: LimitInfo,
        check_sigma: bool = True,
        check_range: bool = True,
    ) -> str:
        """축별 합격/불합격 판정"""
        if check_sigma and sigma > limits.mean_sigma:
            return "NG"
        if check_range and range_val > limits.worst_range:
            return "NG"
        return "OK"

    @staticmethod
    def evaluate_overall_result(
        mean_sigma: float,
        mean_range: float,
        worst_range: float,
        limits: LimitInfo,
        check_sigma: bool = True,
        check_range: bool = True,
    ) -> str:
        """전체 합격/불합격 판정"""
        if check_sigma and mean_sigma > limits.mean_sigma:
            return "NG"
        if check_range:
            if mean_range > limits.mean_range:
                return "NG"
            if worst_range > limits.worst_range:
                return "NG"
        return "OK"

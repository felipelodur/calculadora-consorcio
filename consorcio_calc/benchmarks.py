from abc import ABC, abstractmethod


class Benchmark(ABC):
    @abstractmethod
    def get_monthly_rate(self, month_index: int) -> float:
        """Return the monthly rate for the given month index (0-based)."""
        ...


class FixedRateBenchmark(Benchmark):
    def __init__(self, annual_rate: float):
        self.annual_rate = annual_rate
        self._monthly_rate = (1 + annual_rate) ** (1 / 12) - 1 if annual_rate != 0 else 0.0

    def get_monthly_rate(self, month_index: int) -> float:
        return self._monthly_rate

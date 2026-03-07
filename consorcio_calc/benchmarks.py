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


class HistoricalBenchmark(Benchmark):
    def __init__(self, monthly_rates: list[float]):
        self._rates = monthly_rates

    def get_monthly_rate(self, month_index: int) -> float:
        if month_index >= len(self._rates):
            raise IndexError(
                f"No data for month {month_index}. "
                f"Only {len(self._rates)} months available."
            )
        return self._rates[month_index]

    @classmethod
    def from_daily_data(cls, daily_data: list[dict]) -> "HistoricalBenchmark":
        from consorcio_calc.data_provider import BCBDataProvider

        provider = BCBDataProvider()
        monthly = provider.aggregate_to_monthly(daily_data)
        return cls(monthly_rates=[m["value"] for m in monthly])

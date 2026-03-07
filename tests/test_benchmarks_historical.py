import math
from consorcio_calc.benchmarks import HistoricalBenchmark


def test_historical_benchmark_returns_rates_in_order():
    monthly_rates = [0.008, 0.009, 0.007, 0.010, 0.008, 0.009]
    bench = HistoricalBenchmark(monthly_rates=monthly_rates)
    assert bench.get_monthly_rate(0) == 0.008
    assert bench.get_monthly_rate(3) == 0.010
    assert bench.get_monthly_rate(5) == 0.009


def test_historical_benchmark_out_of_range_raises():
    monthly_rates = [0.008, 0.009]
    bench = HistoricalBenchmark(monthly_rates=monthly_rates)
    try:
        bench.get_monthly_rate(5)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass


def test_historical_benchmark_from_daily_data():
    """Build a HistoricalBenchmark from raw daily BCB data."""
    daily_data = [
        {"date": "02/01/2024", "value": 0.05},
        {"date": "03/01/2024", "value": 0.05},
        {"date": "01/02/2024", "value": 0.04},
        {"date": "02/02/2024", "value": 0.04},
    ]
    bench = HistoricalBenchmark.from_daily_data(daily_data)
    assert bench.get_monthly_rate(0) == (1.0005 * 1.0005) - 1
    assert bench.get_monthly_rate(1) == (1.0004 * 1.0004) - 1

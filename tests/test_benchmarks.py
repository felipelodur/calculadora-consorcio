import math
from consorcio_calc.benchmarks import FixedRateBenchmark


def test_fixed_rate_monthly_conversion():
    # 12% annual -> ~0.9489% monthly
    bench = FixedRateBenchmark(annual_rate=0.12)
    monthly = bench.get_monthly_rate(0)
    expected = (1.12) ** (1 / 12) - 1
    assert math.isclose(monthly, expected, rel_tol=1e-9)


def test_fixed_rate_same_every_month():
    bench = FixedRateBenchmark(annual_rate=0.10)
    rates = [bench.get_monthly_rate(i) for i in range(12)]
    assert all(math.isclose(r, rates[0], rel_tol=1e-9) for r in rates)


def test_fixed_rate_zero():
    bench = FixedRateBenchmark(annual_rate=0.0)
    assert bench.get_monthly_rate(0) == 0.0


def test_fixed_rate_compounding():
    """12 months of compounding at monthly rate should equal annual rate."""
    annual = 0.15
    bench = FixedRateBenchmark(annual_rate=annual)
    monthly = bench.get_monthly_rate(0)
    compounded = (1 + monthly) ** 12 - 1
    assert math.isclose(compounded, annual, rel_tol=1e-9)

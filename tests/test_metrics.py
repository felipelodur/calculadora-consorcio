import math
from consorcio_calc.metrics import compute_npv, compute_cet
from consorcio_calc.benchmarks import FixedRateBenchmark


def test_npv_zero_rate():
    """With 0% discount, NPV = sum of cashflows."""
    outflows = [-1000.0] * 12
    inflow_month = 6
    inflow_value = 12000.0
    cashflows = list(outflows)
    cashflows[inflow_month - 1] += inflow_value

    bench = FixedRateBenchmark(annual_rate=0.0)
    npv = compute_npv(cashflows, bench)
    assert math.isclose(npv, sum(cashflows), rel_tol=1e-9)


def test_npv_positive_rate_reduces_future_values():
    """Positive discount rate should reduce NPV compared to simple sum."""
    cashflows = [-1000.0] * 12
    cashflows[11] += 15000.0

    bench = FixedRateBenchmark(annual_rate=0.10)
    npv = compute_npv(cashflows, bench)
    assert npv < sum(cashflows)


def test_cet_known_scenario():
    """CET of a simple loan-like cashflow should be computable."""
    cashflows = [1000.0] + [-100.0] * 12
    cet = compute_cet(cashflows)
    assert cet > 0


def test_cet_no_cost():
    """If you pay exactly what you receive, CET ≈ 0."""
    cashflows = [1200.0] + [-100.0] * 12
    cet = compute_cet(cashflows)
    assert math.isclose(cet, 0.0, abs_tol=0.001)

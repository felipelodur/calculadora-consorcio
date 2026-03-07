from scipy.optimize import brentq

from consorcio_calc.benchmarks import Benchmark


def compute_npv(cashflows: list[float], benchmark: Benchmark) -> float:
    """Compute NPV of cashflows discounted at benchmark rates.

    Each cashflow[i] is discounted by the product of (1 + rate) for months 0..i-1.
    """
    npv = 0.0
    discount_factor = 1.0
    for i, cf in enumerate(cashflows):
        if i > 0:
            discount_factor *= (1 + benchmark.get_monthly_rate(i - 1))
        npv += cf / discount_factor
    return npv


def compute_cet(cashflows: list[float]) -> float:
    """Compute the CET (Custo Efetivo Total) as an annual rate.

    CET is the IRR that makes NPV = 0. Returns annual rate.
    """

    def npv_at_rate(monthly_rate: float) -> float:
        npv = 0.0
        for i, cf in enumerate(cashflows):
            npv += cf / (1 + monthly_rate) ** i
        return npv

    try:
        monthly_irr = brentq(npv_at_rate, -0.5, 10.0, xtol=1e-10)
        annual_rate = (1 + monthly_irr) ** 12 - 1
        return annual_rate
    except ValueError:
        return float("nan")

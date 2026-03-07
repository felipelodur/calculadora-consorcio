import math
from consorcio_calc.models import ConsorcioParams
from consorcio_calc.benchmarks import FixedRateBenchmark
from consorcio_calc.simulator import simulate


def _simple_params() -> ConsorcioParams:
    return ConsorcioParams(
        carta_credito=100_000.0,
        num_months=60,
        parcela_pos_contemplacao=2_000.0,
    )


def test_simulate_total_paid_no_meia_parcela():
    """Without meia-parcela, total paid = parcela * num_months."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert result.total_paid == 2_000.0 * 60


def test_simulate_total_paid_with_meia_parcela():
    """With meia-parcela, total = meia * (C-1) + cheia * (N-C+1)."""
    params = _simple_params()
    params.parcela_pre_contemplacao = 1_000.0
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=10, benchmark=bench)
    expected = 1_000.0 * 9 + 2_000.0 * 51
    assert result.total_paid == expected


def test_simulate_cashflows_length():
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert len(result.monthly_cashflows) == 60


def test_simulate_contemplation_month_1():
    """Contemplated immediately: max yield time on carta de credito."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=1, benchmark=bench)
    assert result.contemplation_month == 1
    # Consorcio value should be > carta_credito due to yield
    assert result.consorcio_final_value > 100_000.0


def test_simulate_contemplation_last_month():
    """Contemplated at last month: no yield time."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=60, benchmark=bench)
    # No time to compound, so final value = carta_credito
    assert math.isclose(result.consorcio_final_value, 100_000.0, rel_tol=1e-9)


def test_simulate_investment_grows():
    """Investment should be > total paid when rate > 0."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert result.investment_final_value > result.total_paid


def test_simulate_zero_rate():
    """With 0% rate, investment = total paid, consorcio yield = 0."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.0)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert math.isclose(result.investment_final_value, result.total_paid, rel_tol=1e-9)
    assert math.isclose(result.consorcio_final_value, 100_000.0, rel_tol=1e-9)


def test_simulate_net_cost():
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert math.isclose(
        result.net_cost,
        result.total_paid - result.carta_credito_final,
        rel_tol=1e-9,
    )


def test_simulate_opportunity_cost():
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert math.isclose(
        result.opportunity_cost,
        result.investment_final_value - result.consorcio_final_value,
        rel_tol=1e-9,
    )


def test_simulate_npv_is_computed():
    """NPV should be nonzero when rate > 0."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert result.npv != 0.0


def test_simulate_cet_is_computed():
    """CET should be a positive number (consorcio has a cost)."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=30, benchmark=bench)
    assert result.cet > 0

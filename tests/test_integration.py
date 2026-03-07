"""Integration tests with hand-calculated scenarios to validate the full pipeline."""
import math
from consorcio_calc.models import ConsorcioParams
from consorcio_calc.benchmarks import FixedRateBenchmark
from consorcio_calc.simulator import simulate
from consorcio_calc.sweep import run_sweep


def test_simple_scenario_hand_calculated():
    """
    Scenario: R$100k carta, 12 months, R$10k/month, 10% annual rate.
    Contemplated at month 1.

    Investment path: 10k/month invested at ~0.7974%/month for 12 months.
    Consorcio path: receive 100k at month 1, compounds for 11 months.

    Hand calculation:
    - Monthly rate = (1.10)^(1/12) - 1 = 0.007974...
    - Consorcio final = 100000 * (1.007974)^11 = 100000 * 1.09116... ≈ 109116
    - Investment: sum of 10000 * (1.007974)^(12-i) for i=1..12
    """
    params = ConsorcioParams(
        carta_credito=100_000.0,
        num_months=12,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pos_contemplacao=10_000.0,
    )
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = simulate(params, contemplation_month=1, benchmark=bench)

    monthly_rate = (1.10) ** (1 / 12) - 1

    # Verify consorcio final value
    expected_consorcio = 100_000.0 * (1 + monthly_rate) ** 11
    assert math.isclose(result.consorcio_final_value, expected_consorcio, rel_tol=1e-6)

    # Verify total paid
    assert result.total_paid == 120_000.0

    # Verify investment value
    expected_investment = sum(
        10_000.0 * (1 + monthly_rate) ** (12 - i) for i in range(1, 13)
    )
    assert math.isclose(result.investment_final_value, expected_investment, rel_tol=1e-6)


def test_meia_parcela_scenario():
    """Verify meia-parcela correctly splits payments."""
    params = ConsorcioParams(
        carta_credito=100_000.0,
        num_months=12,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pre_contemplacao=5_000.0,
        parcela_pos_contemplacao=10_000.0,
    )
    bench = FixedRateBenchmark(annual_rate=0.10)

    # Contemplated at month 6: months 1-5 pay 5k, months 6-12 pay 10k
    result = simulate(params, contemplation_month=6, benchmark=bench)
    expected_total = 5_000.0 * 5 + 10_000.0 * 7
    assert math.isclose(result.total_paid, expected_total, rel_tol=1e-9)


def test_sweep_monotonic_consorcio_value():
    """Earlier contemplation should always yield >= consorcio value than later."""
    params = ConsorcioParams(
        carta_credito=100_000.0,
        num_months=24,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pos_contemplacao=5_000.0,
    )
    bench = FixedRateBenchmark(annual_rate=0.12)
    sweep = run_sweep(params, bench)

    for i in range(len(sweep.results) - 1):
        assert sweep.results[i].consorcio_final_value >= sweep.results[i + 1].consorcio_final_value

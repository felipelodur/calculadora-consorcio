from consorcio_calc.models import ConsorcioParams
from consorcio_calc.benchmarks import FixedRateBenchmark
from consorcio_calc.sweep import run_sweep


def _simple_params() -> ConsorcioParams:
    return ConsorcioParams(
        carta_credito=100_000.0,
        num_months=60,
        parcela_pos_contemplacao=2_000.0,
    )


def test_sweep_returns_all_months():
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = run_sweep(params, bench)
    assert len(result.results) == 60


def test_sweep_results_ordered_by_contemplation_month():
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = run_sweep(params, bench)
    months = [r.contemplation_month for r in result.results]
    assert months == list(range(1, 61))


def test_sweep_early_contemplation_better_than_late():
    """Earlier contemplation should yield higher consorcio value."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = run_sweep(params, bench)
    early = result.results[0].consorcio_final_value   # month 1
    late = result.results[59].consorcio_final_value    # month 60
    assert early > late


def test_sweep_break_even_month():
    """Break-even month should be None or a valid month."""
    params = _simple_params()
    bench = FixedRateBenchmark(annual_rate=0.10)
    result = run_sweep(params, bench)
    if result.break_even_month is not None:
        assert 1 <= result.break_even_month <= 60

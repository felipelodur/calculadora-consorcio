# tests/test_package.py
def test_top_level_imports():
    """Verify all key classes/functions are importable from the package."""
    from consorcio_calc import (
        ConsorcioParams,
        SimulationResult,
        SweepResult,
        FixedRateBenchmark,
        HistoricalBenchmark,
        simulate,
        run_sweep,
        run_backtest,
    )
    assert ConsorcioParams is not None
    assert simulate is not None
    assert run_sweep is not None
    assert run_backtest is not None

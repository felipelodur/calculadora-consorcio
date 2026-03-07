from datetime import datetime, timedelta

from consorcio_calc.benchmarks import HistoricalBenchmark
from consorcio_calc.data_provider import BCBDataProvider, BCBSeries
from consorcio_calc.models import ConsorcioParams, SimulationResult
from consorcio_calc.simulator import simulate


def run_backtest(
    params: ConsorcioParams,
    contemplation_month: int,
    start_date: str,
    series: BCBSeries = BCBSeries.CDI,
    cache_dir: str = "data/cache",
) -> SimulationResult:
    """Run a backtest using historical BCB data.

    Args:
        params: Consorcio plan parameters.
        contemplation_month: Month when contemplation occurs (1-indexed).
        start_date: Start date in dd/mm/yyyy format.
        series: Which BCB series to use as benchmark.
        cache_dir: Directory for cached data.

    Returns:
        SimulationResult computed with historical rates.
    """
    provider = BCBDataProvider(cache_dir=cache_dir)

    # Calculate end date from start + num_months
    start = datetime.strptime(start_date, "%d/%m/%Y")
    end = start + timedelta(days=params.num_months * 31)  # overshoot to be safe
    end_date = end.strftime("%d/%m/%Y")

    raw_data = provider.get(series, start_date, end_date)

    if series.frequency == "daily":
        monthly_data = provider.aggregate_to_monthly(raw_data)
    else:
        monthly_data = [{"month": d["date"], "value": d["value"] / 100} for d in raw_data]

    monthly_rates = [m["value"] for m in monthly_data]

    # Ensure we have enough months
    if len(monthly_rates) < params.num_months:
        raise ValueError(
            f"Not enough historical data: need {params.num_months} months, "
            f"got {len(monthly_rates)}."
        )

    monthly_rates = monthly_rates[: params.num_months]
    benchmark = HistoricalBenchmark(monthly_rates=monthly_rates)

    return simulate(params, contemplation_month=contemplation_month, benchmark=benchmark)

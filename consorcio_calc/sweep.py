from consorcio_calc.models import ConsorcioParams, SweepResult
from consorcio_calc.benchmarks import Benchmark
from consorcio_calc.simulator import simulate


def run_sweep(params: ConsorcioParams, benchmark: Benchmark) -> SweepResult:
    """Run simulation for every possible contemplation month.

    Returns a SweepResult with results for each month and the break-even month.
    """
    results = []
    for month in range(1, params.num_months + 1):
        result = simulate(params, contemplation_month=month, benchmark=benchmark)
        results.append(result)

    # Break-even: latest month where consorcio >= investment
    break_even_month = None
    for result in results:
        if result.consorcio_final_value >= result.investment_final_value:
            break_even_month = result.contemplation_month

    return SweepResult(results=results, break_even_month=break_even_month)

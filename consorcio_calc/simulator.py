from consorcio_calc.models import ConsorcioParams, SimulationResult
from consorcio_calc.benchmarks import Benchmark


def simulate(
    params: ConsorcioParams,
    contemplation_month: int,
    benchmark: Benchmark,
) -> SimulationResult:
    """Simulate a consorcio vs. investment for a fixed contemplation month.

    Args:
        params: Consorcio plan parameters.
        contemplation_month: Month when contemplation occurs (1-indexed).
        benchmark: Benchmark for investment returns and fund yield.

    Returns:
        SimulationResult with all computed values.
    """
    n = params.num_months
    c = contemplation_month

    # Step 1: Build cash flow schedule
    cashflows = []
    for month in range(1, n + 1):
        contemplated = month >= c
        installment = params.get_installment(contemplated)

        # Apply reajuste: adjust installment annually
        if params.reajuste_anual is not None:
            years_elapsed = (month - 1) // 12
            installment *= (1 + params.reajuste_anual) ** years_elapsed

        cashflows.append(installment)

    total_paid = sum(cashflows)

    # Carta de credito value at contemplation (adjusted if reajuste)
    carta_at_contemplation = params.carta_credito
    if params.reajuste_anual is not None:
        years_at_contemplation = (c - 1) // 12
        carta_at_contemplation *= (1 + params.reajuste_anual) ** years_at_contemplation

    # Step 2: Consorcio outcome
    # At month C you receive the carta. From C+1 to N it compounds.
    consorcio_value = carta_at_contemplation
    for month_idx in range(c, n):  # months after contemplation (0-indexed: c to n-1)
        monthly_rate = benchmark.get_monthly_rate(month_idx)
        fund_rate = monthly_rate * params.rendimento_fundo
        consorcio_value *= (1 + fund_rate)

    # Step 3: Alternative investment outcome
    # Each monthly installment is invested and compounds to the end
    investment_value = 0.0
    for month_idx in range(n):  # 0-indexed
        contribution = cashflows[month_idx]
        # Compound from month_idx+1 to n-1
        accumulated = contribution
        for future_idx in range(month_idx + 1, n):
            monthly_rate = benchmark.get_monthly_rate(future_idx)
            accumulated *= (1 + monthly_rate)
        investment_value += accumulated

    # Step 4: Compute basic metrics
    net_cost = total_paid - carta_at_contemplation
    opportunity_cost = investment_value - consorcio_value

    return SimulationResult(
        contemplation_month=c,
        total_paid=total_paid,
        carta_credito_final=carta_at_contemplation,
        consorcio_final_value=consorcio_value,
        investment_final_value=investment_value,
        net_cost=net_cost,
        opportunity_cost=opportunity_cost,
        npv=0.0,  # Computed in metrics module (Task 7/8)
        cet=0.0,  # Computed in metrics module (Task 7/8)
        monthly_cashflows=cashflows,
    )

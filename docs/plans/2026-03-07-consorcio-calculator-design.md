# Consorcio Calculator - Design Document

## Goal

A backtestable calculator that evaluates the financial return of joining a Brazilian consorcio versus investing the same money independently. Generic/configurable engine that works for any consorcio type (imoveis, veiculos, etc.).

## Project Structure

```
calculadora-consorcio/
├── consorcio_calc/           # Pure Python logic - no UI dependencies
│   ├── __init__.py
│   ├── models.py             # Data classes for inputs/outputs
│   ├── simulator.py          # Main simulation engine
│   ├── benchmarks.py         # Investment benchmark (fixed rate or historical)
│   ├── data_provider.py      # BCB API client + local cache
│   ├── metrics.py            # NPV, CET, break-even, net cost, opportunity cost
│   └── sweep.py              # Scenario sweep across contemplation months
├── app/                      # Frontend interface (later phase)
├── data/
│   └── cache/                # Cached historical data from BCB
├── tests/
└── docs/
    └── plans/
```

`consorcio_calc` is fully standalone - importable, testable, and backtestable without any UI. `app/` depends on `consorcio_calc` but not the other way around.

## Core Concepts

### Comparison Model

- **Option A: Consorcio** - pay monthly installments, get contemplated at some point, receive the carta de credito, which continues yielding returns in the fund until plan end.
- **Option B: Invest independently** - take the same monthly installment amount and invest it at a benchmark rate.

### Input Parameters (`ConsorcioParams`)

| Parameter | Type | Description |
|---|---|---|
| `carta_credito` | float | Credit letter value (R$) |
| `num_months` | int | Plan duration in months |
| `taxa_admin` | float | Total admin fee as decimal (e.g., 0.18 = 18%) |
| `fundo_reserva` | float | Reserve fund as decimal |
| `seguro` | float | Insurance as decimal |
| `parcela_pre_contemplacao` | float or None | Half-installment before contemplation (None = same as full) |
| `parcela_pos_contemplacao` | float | Full installment after contemplation |
| `rendimento_fundo` | float | Yield on fund post-contemplation as fraction of benchmark (e.g., 0.96 = 96% of CDI) |
| `reajuste_anual` | float or None | Optional annual adjustment rate for carta de credito |

### Payment Structure

Supports meia-parcela: some plans charge half installment before contemplation, switching to parcela-cheia after. Configurable via the two parcela fields.

## Simulation Flow

For a single scenario (fixed contemplation month C, plan duration N):

### Step 1 - Build Cash Flow Schedule
- For each month 1..N, compute the installment paid
- Meia-parcela for months 1..C-1, parcela-cheia for months C..N (if applicable)
- Apply reajuste annually if configured (adjusts carta de credito and installments)

### Step 2 - Consorcio Outcome
- At month C, receive carta de credito value (adjusted if reajuste is on)
- From month C to N, that value compounds at `rendimento_fundo` x benchmark monthly rate
- Final consorcio value = carta de credito + accumulated yield from C to N

### Step 3 - Alternative Investment Outcome
- Each month, invest the installment amount at the benchmark rate
- Uses either a fixed annual rate OR historical series (CDI, IPCA, etc.)
- Each contribution compounds from its deposit month to month N
- Final investment value = sum of all compounded contributions

### Step 4 - Compute Metrics
- Net cost, opportunity cost, NPV, CET, break-even month, and the delta between paths

### Sweep Mode
Run Steps 1-4 for C = 1, 2, ..., N. Returns the full curve of results across all possible contemplation months.

## Benchmarks & Data

### BCB API Integration

Fetches historical series from the SGS API (free, no authentication):

| Series | BCB Code | Frequency |
|---|---|---|
| CDI | 12 | Daily |
| IPCA | 433 | Monthly |
| INCC | 192 | Monthly |
| Poupanca | 195 | Monthly |

- Cached locally as CSV in `data/cache/`
- Cache invalidation: re-fetch if older than 1 day

### Benchmark Modes

1. **Fixed rate** - user provides annual rate (e.g., 12% a.a.), converted to monthly compounding
2. **Historical series** - given a start date, pulls actual monthly returns from cache/API

Both implement the same interface: `get_monthly_rate(month_index) -> float`

Backtesting = pick a start date in the past + use historical rates.

## Output Metrics

| Metric | Definition |
|---|---|
| Net cost | Total installments paid - carta de credito value received |
| Opportunity cost | Final investment value - final consorcio value |
| Break-even month | Latest contemplation month where consorcio >= investment |
| NPV | All cash flows discounted at the benchmark rate |
| CET | IRR that makes NPV of consorcio cash flows = 0 (effective annual cost) |

In sweep mode, each metric is computed per contemplation month, producing a curve.

## Testing Strategy

- **Unit tests** for each module (simulator, metrics, benchmarks)
- **Integration tests** with hand-calculated known scenarios
- **Backtest harness** - function that takes a consorcio proposal + historical period + actual contemplation month, computes what the real outcome would have been

Example: "If I entered this consorcio in Jan 2018 and was contemplated in month 24, how would it compare to CDI over that period?"

## Future Work (Out of Scope for Now)

- Frontend interface in `app/`
- Post-contemplation asset modeling (property appreciation, car depreciation)
- Bid strategy simulation (lance optimization)
- Multiple consorcio comparison

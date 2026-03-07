# CLAUDE.md

## Quick Reference

- **Python 3.11+**, uses `setuptools` build backend
- Install: `pip install -e ".[dev,app]"`
- Tests: `pytest -v` (40+ tests, all should pass)
- App: `streamlit run app/app.py`

## Architecture

Two independent layers:

1. **`consorcio_calc/`** — pure Python engine, no UI deps. Entry points: `simulate()`, `run_sweep()`, `run_backtest()`.
2. **`app/app.py`** — Streamlit UI that imports from `consorcio_calc`. Single file, Portuguese BR.

## Important Patterns

- **Benchmarks are decoupled**: investment benchmark (what you'd earn investing independently) vs fund benchmark (what the carta yields post-contemplation). Simulator accepts both via `benchmark` and `fund_benchmark` params.
- **BCB data has two cache layers**: disk CSV cache in `data/cache/` + Streamlit `@st.cache_data`. The `BCBDataProvider.get()` method checks disk cache first.
- **Daily CDI → monthly**: `aggregate_to_monthly()` compounds daily rates. Monthly → annual: `(1 + r)^12 - 1`.
- **CET computation**: uses only cashflows up to contemplation month (not full plan duration).
- **Sweep**: iterates every contemplation month 1..N. Break-even = latest month where consórcio >= investment.

## Testing

- Tests are in `tests/`, one file per module. `test_integration.py` tests end-to-end flows.
- `test_data_provider.py` mocks HTTP calls (no real BCB API calls in tests).
- Run a single test: `pytest tests/test_simulator.py -v`

## Common Tasks

- **Add a new benchmark type**: implement `Benchmark` ABC in `benchmarks.py`, add tests in `tests/test_benchmarks.py`.
- **Add a UI section**: edit `app/app.py`, keep all UI in that single file.
- **Change simulation logic**: edit `simulator.py`, verify with `pytest tests/test_simulator.py tests/test_integration.py`.

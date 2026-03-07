# Calculadora de Consórcio

Compare a Brazilian consórcio proposal against investing the same money independently. Supports fixed-rate and historical CDI backtesting, scenario sweep across all contemplation months, and key financial metrics (NPV, CET, break-even, opportunity cost).

**Live app:** [calculadora-consorcio.streamlit.app](https://calculadora-consorcio.streamlit.app) (if deployed)

## Project Structure

```
consorcio_calc/          # Pure Python engine (no UI dependencies)
  models.py              # ConsorcioParams, SimulationResult, SweepResult dataclasses
  simulator.py           # Core simulation: consórcio vs investment for a given contemplation month
  sweep.py               # Run simulation for every possible contemplation month
  benchmarks.py          # Benchmark interface, FixedRateBenchmark, HistoricalBenchmark
  metrics.py             # NPV and CET (IRR) computation
  data_provider.py       # BCB SGS API client with disk caching (CDI, IPCA, INCC, Poupança)
  backtest.py            # Historical backtest harness connecting BCB data to simulator

app/
  app.py                 # Streamlit single-page web app (Portuguese BR)

tests/                   # pytest suite (40+ tests)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate    # or .venv\Scripts\activate on Windows
pip install -e ".[dev,app]"
```

## Run Tests

```bash
pytest -v
```

## Run the App

```bash
streamlit run app/app.py
```

## Key Concepts

- **Carta de crédito**: the lump sum you receive upon contemplation
- **Meia-parcela / Parcela-cheia**: half installment (pre-contemplation) vs full installment (post-contemplation)
- **Contemplação**: the month you receive the carta de crédito
- **Rendimento do fundo**: post-contemplation, the carta yields a % of CDI in the consortium fund
- **Reajuste anual**: yearly adjustment applied to installments and carta value
- **Benchmark**: the alternative investment return (fixed rate or historical CDI)
- **Sweep**: simulates every possible contemplation month to find break-even and distribution

## Deploy on Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Point to `app/app.py` as the main file
4. `requirements.txt` in the repo root handles dependencies

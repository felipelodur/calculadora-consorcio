# Consorcio Calculator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a backtestable Python engine that compares the financial return of a Brazilian consorcio against investing the same money independently.

**Architecture:** Pure Python library (`consorcio_calc/`) with dataclass-based inputs/outputs, stateless simulation functions, and a benchmark system that supports both fixed rates and historical BCB data. All calculations are monthly time-stepped.

**Tech Stack:** Python 3.11+, dataclasses, requests (BCB API), scipy (IRR/CET), pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `consorcio_calc/__init__.py`
- Create: `tests/__init__.py`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `data/cache/.gitkeep`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "consorcio-calc"
version = "0.1.0"
description = "Backtestable Brazilian consorcio financial calculator"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "scipy>=1.11",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"
```

**Step 2: Create .gitignore**

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/
data/cache/*.csv
.pytest_cache/
```

**Step 3: Create empty __init__.py files**

```python
# consorcio_calc/__init__.py
```

```python
# tests/__init__.py
```

**Step 4: Create cache directory**

```bash
mkdir -p data/cache
touch data/cache/.gitkeep
```

**Step 5: Install the project**

Run: `pip install -e ".[dev]"`
Expected: Successful installation

**Step 6: Commit**

```bash
git add pyproject.toml .gitignore consorcio_calc/__init__.py tests/__init__.py data/cache/.gitkeep
git commit -m "feat: project scaffolding with pyproject.toml and directory structure"
```

---

### Task 2: Data Models

**Files:**
- Create: `consorcio_calc/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
from consorcio_calc.models import ConsorcioParams, SimulationResult, SweepResult


def test_consorcio_params_defaults():
    params = ConsorcioParams(
        carta_credito=200_000.0,
        num_months=180,
        taxa_admin=0.18,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pos_contemplacao=1_500.0,
    )
    assert params.carta_credito == 200_000.0
    assert params.num_months == 180
    assert params.parcela_pre_contemplacao is None
    assert params.rendimento_fundo == 1.0
    assert params.reajuste_anual is None


def test_consorcio_params_meia_parcela():
    params = ConsorcioParams(
        carta_credito=200_000.0,
        num_months=180,
        taxa_admin=0.18,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pre_contemplacao=750.0,
        parcela_pos_contemplacao=1_500.0,
    )
    assert params.parcela_pre_contemplacao == 750.0
    assert params.parcela_pos_contemplacao == 1_500.0


def test_consorcio_params_get_installment():
    params = ConsorcioParams(
        carta_credito=200_000.0,
        num_months=180,
        taxa_admin=0.18,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pre_contemplacao=750.0,
        parcela_pos_contemplacao=1_500.0,
    )
    # Before contemplation (month < contemplation_month)
    assert params.get_installment(contemplated=False) == 750.0
    # After contemplation
    assert params.get_installment(contemplated=True) == 1_500.0


def test_consorcio_params_no_meia_parcela():
    params = ConsorcioParams(
        carta_credito=200_000.0,
        num_months=180,
        taxa_admin=0.18,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pos_contemplacao=1_500.0,
    )
    # Without meia-parcela, both should return full installment
    assert params.get_installment(contemplated=False) == 1_500.0
    assert params.get_installment(contemplated=True) == 1_500.0


def test_simulation_result():
    result = SimulationResult(
        contemplation_month=24,
        total_paid=270_000.0,
        carta_credito_final=210_000.0,
        consorcio_final_value=225_000.0,
        investment_final_value=290_000.0,
        net_cost=60_000.0,
        opportunity_cost=65_000.0,
        npv=-15_000.0,
        cet=0.08,
        monthly_cashflows=[],
    )
    assert result.contemplation_month == 24
    assert result.opportunity_cost == 65_000.0


def test_sweep_result():
    sim = SimulationResult(
        contemplation_month=1,
        total_paid=0, carta_credito_final=0, consorcio_final_value=0,
        investment_final_value=0, net_cost=0, opportunity_cost=0,
        npv=0, cet=0, monthly_cashflows=[],
    )
    sweep = SweepResult(results=[sim], break_even_month=None)
    assert len(sweep.results) == 1
    assert sweep.break_even_month is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/models.py
from dataclasses import dataclass, field


@dataclass
class ConsorcioParams:
    carta_credito: float
    num_months: int
    taxa_admin: float
    fundo_reserva: float
    seguro: float
    parcela_pos_contemplacao: float
    parcela_pre_contemplacao: float | None = None
    rendimento_fundo: float = 1.0
    reajuste_anual: float | None = None

    def get_installment(self, contemplated: bool) -> float:
        if not contemplated and self.parcela_pre_contemplacao is not None:
            return self.parcela_pre_contemplacao
        return self.parcela_pos_contemplacao


@dataclass
class SimulationResult:
    contemplation_month: int
    total_paid: float
    carta_credito_final: float
    consorcio_final_value: float
    investment_final_value: float
    net_cost: float
    opportunity_cost: float
    npv: float
    cet: float
    monthly_cashflows: list[float]


@dataclass
class SweepResult:
    results: list[SimulationResult]
    break_even_month: int | None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/models.py tests/test_models.py
git commit -m "feat: add data models for consorcio params and simulation results"
```

---

### Task 3: Benchmarks (Fixed Rate + Interface)

**Files:**
- Create: `consorcio_calc/benchmarks.py`
- Create: `tests/test_benchmarks.py`

**Step 1: Write the failing test**

```python
# tests/test_benchmarks.py
import math
from consorcio_calc.benchmarks import FixedRateBenchmark


def test_fixed_rate_monthly_conversion():
    # 12% annual -> ~0.9489% monthly
    bench = FixedRateBenchmark(annual_rate=0.12)
    monthly = bench.get_monthly_rate(0)
    expected = (1.12) ** (1 / 12) - 1
    assert math.isclose(monthly, expected, rel_tol=1e-9)


def test_fixed_rate_same_every_month():
    bench = FixedRateBenchmark(annual_rate=0.10)
    rates = [bench.get_monthly_rate(i) for i in range(12)]
    assert all(math.isclose(r, rates[0], rel_tol=1e-9) for r in rates)


def test_fixed_rate_zero():
    bench = FixedRateBenchmark(annual_rate=0.0)
    assert bench.get_monthly_rate(0) == 0.0


def test_fixed_rate_compounding():
    """12 months of compounding at monthly rate should equal annual rate."""
    annual = 0.15
    bench = FixedRateBenchmark(annual_rate=annual)
    monthly = bench.get_monthly_rate(0)
    compounded = (1 + monthly) ** 12 - 1
    assert math.isclose(compounded, annual, rel_tol=1e-9)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_benchmarks.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/benchmarks.py
from abc import ABC, abstractmethod


class Benchmark(ABC):
    @abstractmethod
    def get_monthly_rate(self, month_index: int) -> float:
        """Return the monthly rate for the given month index (0-based)."""
        ...


class FixedRateBenchmark(Benchmark):
    def __init__(self, annual_rate: float):
        self.annual_rate = annual_rate
        self._monthly_rate = (1 + annual_rate) ** (1 / 12) - 1 if annual_rate != 0 else 0.0

    def get_monthly_rate(self, month_index: int) -> float:
        return self._monthly_rate
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_benchmarks.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/benchmarks.py tests/test_benchmarks.py
git commit -m "feat: add benchmark interface and fixed-rate implementation"
```

---

### Task 4: BCB Data Provider

**Files:**
- Create: `consorcio_calc/data_provider.py`
- Create: `tests/test_data_provider.py`

**Step 1: Write the failing test**

```python
# tests/test_data_provider.py
import json
from unittest.mock import patch, MagicMock
from consorcio_calc.data_provider import BCBDataProvider, BCBSeries


def test_bcb_series_enum():
    assert BCBSeries.CDI.code == 12
    assert BCBSeries.IPCA.code == 433
    assert BCBSeries.INCC.code == 192
    assert BCBSeries.POUPANCA.code == 195


def test_fetch_parses_response():
    """Test that the provider correctly parses BCB API JSON response."""
    mock_response_data = [
        {"data": "02/01/2024", "valor": "0.050307"},
        {"data": "03/01/2024", "valor": "0.050307"},
    ]
    provider = BCBDataProvider(cache_dir="/tmp/test_cache")

    with patch("consorcio_calc.data_provider.requests.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with patch("consorcio_calc.data_provider.os.path.exists", return_value=False):
            with patch("builtins.open", MagicMock()):
                with patch("consorcio_calc.data_provider.csv.writer"):
                    data = provider.fetch(BCBSeries.CDI, "01/01/2024", "03/01/2024")

    assert len(data) == 2
    assert data[0]["date"] == "02/01/2024"
    assert data[0]["value"] == 0.050307


def test_aggregate_daily_to_monthly():
    """Test aggregation of daily CDI rates to monthly compounded rates."""
    provider = BCBDataProvider(cache_dir="/tmp/test_cache")
    daily_data = [
        {"date": "02/01/2024", "value": 0.05},  # ~0.05% daily
        {"date": "03/01/2024", "value": 0.05},
        {"date": "15/02/2024", "value": 0.04},
        {"date": "16/02/2024", "value": 0.04},
    ]
    monthly = provider.aggregate_to_monthly(daily_data)
    assert len(monthly) == 2  # Jan and Feb
    # Jan: (1+0.0005)*(1+0.0005) - 1
    jan_expected = (1 + 0.0005) * (1 + 0.0005) - 1
    assert abs(monthly[0]["value"] - jan_expected) < 1e-10
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_data_provider.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/data_provider.py
import csv
import os
import time
from collections import defaultdict
from enum import Enum

import requests


class BCBSeries(Enum):
    CDI = (12, "daily")
    IPCA = (433, "monthly")
    INCC = (192, "monthly")
    POUPANCA = (195, "monthly")

    def __init__(self, code: int, frequency: str):
        self.code = code
        self.frequency = frequency


class BCBDataProvider:
    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados"

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir

    def _cache_path(self, series: BCBSeries) -> str:
        return os.path.join(self.cache_dir, f"{series.name.lower()}.csv")

    def _cache_is_valid(self, series: BCBSeries, max_age_seconds: int = 86400) -> bool:
        path = self._cache_path(series)
        if not os.path.exists(path):
            return False
        age = time.time() - os.path.getmtime(path)
        return age < max_age_seconds

    def _save_cache(self, series: BCBSeries, data: list[dict]) -> None:
        os.makedirs(self.cache_dir, exist_ok=True)
        path = self._cache_path(series)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "value"])
            for row in data:
                writer.writerow([row["date"], row["value"]])

    def _load_cache(self, series: BCBSeries) -> list[dict]:
        path = self._cache_path(series)
        data = []
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({"date": row["date"], "value": float(row["value"])})
        return data

    def fetch(self, series: BCBSeries, start_date: str, end_date: str) -> list[dict]:
        """Fetch series data from BCB API. Dates in dd/mm/yyyy format."""
        url = self.BASE_URL.format(code=series.code)
        params = {"formato": "json", "dataInicial": start_date, "dataFinal": end_date}
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        raw = resp.json()
        data = [{"date": item["data"], "value": float(item["valor"])} for item in raw]
        self._save_cache(series, data)
        return data

    def get(self, series: BCBSeries, start_date: str, end_date: str) -> list[dict]:
        """Get series data, using cache if valid, otherwise fetching."""
        if self._cache_is_valid(series):
            return self._load_cache(series)
        return self.fetch(series, start_date, end_date)

    def aggregate_to_monthly(self, daily_data: list[dict]) -> list[dict]:
        """Aggregate daily percentage rates to monthly compounded rates.
        Daily values are in percentage (e.g., 0.05 means 0.05% = 0.0005 as decimal).
        Returns monthly rates as decimals (e.g., 0.01 means 1%).
        """
        months: dict[str, list[float]] = defaultdict(list)
        for entry in daily_data:
            # date format: dd/mm/yyyy
            parts = entry["date"].split("/")
            month_key = f"{parts[1]}/{parts[2]}"  # mm/yyyy
            months[month_key].append(entry["value"])

        result = []
        for month_key in months:
            daily_rates = months[month_key]
            # Compound daily rates: product of (1 + rate/100) - 1
            compounded = 1.0
            for rate in daily_rates:
                compounded *= (1 + rate / 100)
            compounded -= 1
            result.append({"month": month_key, "value": compounded})
        return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_data_provider.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/data_provider.py tests/test_data_provider.py
git commit -m "feat: add BCB data provider with API client and caching"
```

---

### Task 5: Historical Benchmark

**Files:**
- Modify: `consorcio_calc/benchmarks.py`
- Create: `tests/test_benchmarks_historical.py`

**Step 1: Write the failing test**

```python
# tests/test_benchmarks_historical.py
import math
from consorcio_calc.benchmarks import HistoricalBenchmark


def test_historical_benchmark_returns_rates_in_order():
    monthly_rates = [0.008, 0.009, 0.007, 0.010, 0.008, 0.009]
    bench = HistoricalBenchmark(monthly_rates=monthly_rates)
    assert bench.get_monthly_rate(0) == 0.008
    assert bench.get_monthly_rate(3) == 0.010
    assert bench.get_monthly_rate(5) == 0.009


def test_historical_benchmark_out_of_range_raises():
    monthly_rates = [0.008, 0.009]
    bench = HistoricalBenchmark(monthly_rates=monthly_rates)
    try:
        bench.get_monthly_rate(5)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass


def test_historical_benchmark_from_daily_data():
    """Build a HistoricalBenchmark from raw daily BCB data."""
    daily_data = [
        {"date": "02/01/2024", "value": 0.05},
        {"date": "03/01/2024", "value": 0.05},
        {"date": "01/02/2024", "value": 0.04},
        {"date": "02/02/2024", "value": 0.04},
    ]
    bench = HistoricalBenchmark.from_daily_data(daily_data)
    assert bench.get_monthly_rate(0) == (1.0005 * 1.0005) - 1
    assert bench.get_monthly_rate(1) == (1.0004 * 1.0004) - 1
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_benchmarks_historical.py -v`
Expected: FAIL with ImportError

**Step 3: Add HistoricalBenchmark to benchmarks.py**

Append to `consorcio_calc/benchmarks.py`:

```python
from consorcio_calc.data_provider import BCBDataProvider


class HistoricalBenchmark(Benchmark):
    def __init__(self, monthly_rates: list[float]):
        self._rates = monthly_rates

    def get_monthly_rate(self, month_index: int) -> float:
        if month_index >= len(self._rates):
            raise IndexError(
                f"No data for month {month_index}. "
                f"Only {len(self._rates)} months available."
            )
        return self._rates[month_index]

    @classmethod
    def from_daily_data(cls, daily_data: list[dict]) -> "HistoricalBenchmark":
        provider = BCBDataProvider()
        monthly = provider.aggregate_to_monthly(daily_data)
        return cls(monthly_rates=[m["value"] for m in monthly])
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_benchmarks_historical.py -v`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/benchmarks.py tests/test_benchmarks_historical.py
git commit -m "feat: add historical benchmark with daily-to-monthly aggregation"
```

---

### Task 6: Core Simulator

**Files:**
- Create: `consorcio_calc/simulator.py`
- Create: `tests/test_simulator.py`

This is the heart of the engine. It computes the cash flow schedule, consorcio outcome, and investment outcome for a single contemplation month.

**Step 1: Write the failing test**

```python
# tests/test_simulator.py
import math
from consorcio_calc.models import ConsorcioParams
from consorcio_calc.benchmarks import FixedRateBenchmark
from consorcio_calc.simulator import simulate


def _simple_params() -> ConsorcioParams:
    return ConsorcioParams(
        carta_credito=100_000.0,
        num_months=60,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
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
    # No time to compound, so final value ≈ carta_credito
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_simulator.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/simulator.py
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
    # From contemplation month to end, carta earns rendimento_fundo * benchmark rate
    consorcio_value = carta_at_contemplation
    for month_idx in range(c - 1, n):  # month c through n (0-indexed: c-1 to n-1)
        if month_idx >= c - 1:  # post-contemplation (inclusive of contemplation month)
            monthly_rate = benchmark.get_monthly_rate(month_idx)
            fund_rate = monthly_rate * params.rendimento_fundo
            consorcio_value *= (1 + fund_rate)
    # Undo the first month's compounding (contemplation month itself doesn't compound)
    # Actually, let's say: at month C you receive the carta. From C+1 to N it compounds.
    # Recalculate:
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
        npv=0.0,  # Computed in metrics module
        cet=0.0,  # Computed in metrics module
        monthly_cashflows=cashflows,
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_simulator.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/simulator.py tests/test_simulator.py
git commit -m "feat: add core simulator for consorcio vs investment comparison"
```

---

### Task 7: Metrics (NPV, CET, Break-Even)

**Files:**
- Create: `consorcio_calc/metrics.py`
- Create: `tests/test_metrics.py`

**Step 1: Write the failing test**

```python
# tests/test_metrics.py
import math
from consorcio_calc.metrics import compute_npv, compute_cet
from consorcio_calc.benchmarks import FixedRateBenchmark


def test_npv_zero_rate():
    """With 0% discount, NPV = sum of cashflows."""
    # Cashflows: pay 1000/month for 12 months, receive 12000 at month 6
    outflows = [-1000.0] * 12
    inflow_month = 6
    inflow_value = 12000.0
    cashflows = list(outflows)
    cashflows[inflow_month - 1] += inflow_value  # net at month 6

    bench = FixedRateBenchmark(annual_rate=0.0)
    npv = compute_npv(cashflows, bench)
    assert math.isclose(npv, sum(cashflows), rel_tol=1e-9)


def test_npv_positive_rate_reduces_future_values():
    """Positive discount rate should reduce NPV compared to simple sum."""
    cashflows = [-1000.0] * 12
    cashflows[11] += 15000.0  # Big inflow at end

    bench = FixedRateBenchmark(annual_rate=0.10)
    npv = compute_npv(cashflows, bench)
    assert npv < sum(cashflows)  # Discounting reduces future values


def test_cet_known_scenario():
    """CET of a simple loan-like cashflow should be computable."""
    # Pay 100/month for 12 months to receive 1000 at month 0
    # This is like a loan: receive 1000 now, pay back 1200 over 12 months
    cashflows = [1000.0] + [-100.0] * 12
    cet = compute_cet(cashflows)
    # CET should be positive (you're paying more than you received)
    assert cet > 0


def test_cet_no_cost():
    """If you pay exactly what you receive, CET ≈ 0."""
    # Receive 1200 at month 0, pay 100/month for 12 months
    cashflows = [1200.0] + [-100.0] * 12
    cet = compute_cet(cashflows)
    assert math.isclose(cet, 0.0, abs_tol=0.001)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_metrics.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/metrics.py
import numpy as np
from scipy.optimize import brentq

from consorcio_calc.benchmarks import Benchmark


def compute_npv(cashflows: list[float], benchmark: Benchmark) -> float:
    """Compute NPV of cashflows discounted at benchmark rates.

    Each cashflow[i] is discounted by the product of (1 + rate) for months 0..i-1.
    """
    npv = 0.0
    discount_factor = 1.0
    for i, cf in enumerate(cashflows):
        if i > 0:
            discount_factor *= (1 + benchmark.get_monthly_rate(i - 1))
        npv += cf / discount_factor
    return npv


def compute_cet(cashflows: list[float]) -> float:
    """Compute the CET (Custo Efetivo Total) as an annual rate.

    CET is the IRR that makes NPV = 0. Returns annual rate.
    """

    def npv_at_rate(monthly_rate: float) -> float:
        npv = 0.0
        for i, cf in enumerate(cashflows):
            npv += cf / (1 + monthly_rate) ** i
        return npv

    try:
        monthly_irr = brentq(npv_at_rate, -0.5, 10.0, xtol=1e-10)
        annual_rate = (1 + monthly_irr) ** 12 - 1
        return annual_rate
    except ValueError:
        return float("nan")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_metrics.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/metrics.py tests/test_metrics.py
git commit -m "feat: add NPV and CET metrics computation"
```

---

### Task 8: Integrate Metrics into Simulator

**Files:**
- Modify: `consorcio_calc/simulator.py`
- Modify: `tests/test_simulator.py`

**Step 1: Write the failing test**

Add to `tests/test_simulator.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_simulator.py::test_simulate_npv_is_computed tests/test_simulator.py::test_simulate_cet_is_computed -v`
Expected: FAIL (npv and cet are still 0.0)

**Step 3: Update simulator to compute metrics**

Add to the end of the `simulate` function in `consorcio_calc/simulator.py`, replacing the `npv=0.0` and `cet=0.0` lines:

```python
    from consorcio_calc.metrics import compute_npv, compute_cet

    # Build NPV cashflows: outflows are negative installments,
    # inflow is carta de credito at contemplation month
    npv_cashflows = [-cf for cf in cashflows]
    npv_cashflows[c - 1] += carta_at_contemplation
    npv = compute_npv(npv_cashflows, benchmark)

    # Build CET cashflows: same as NPV cashflows
    cet = compute_cet(npv_cashflows)
```

And update the return statement to use these computed values instead of 0.0.

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_simulator.py -v`
Expected: All 12 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/simulator.py tests/test_simulator.py
git commit -m "feat: integrate NPV and CET computation into simulator"
```

---

### Task 9: Sweep Mode

**Files:**
- Create: `consorcio_calc/sweep.py`
- Create: `tests/test_sweep.py`

**Step 1: Write the failing test**

```python
# tests/test_sweep.py
from consorcio_calc.models import ConsorcioParams
from consorcio_calc.benchmarks import FixedRateBenchmark
from consorcio_calc.sweep import run_sweep


def _simple_params() -> ConsorcioParams:
    return ConsorcioParams(
        carta_credito=100_000.0,
        num_months=60,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sweep.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/sweep.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sweep.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/sweep.py tests/test_sweep.py
git commit -m "feat: add sweep mode for scenario analysis across all contemplation months"
```

---

### Task 10: Integration Test with Hand-Calculated Scenario

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test with a fully hand-verified scenario**

```python
# tests/test_integration.py
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
```

**Step 2: Run test**

Run: `pytest tests/test_integration.py -v`
Expected: All 3 tests PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests with hand-calculated scenarios"
```

---

### Task 11: Backtest Harness

**Files:**
- Create: `consorcio_calc/backtest.py`
- Create: `tests/test_backtest.py`

**Step 1: Write the failing test**

```python
# tests/test_backtest.py
from unittest.mock import patch
from consorcio_calc.backtest import run_backtest
from consorcio_calc.models import ConsorcioParams


def test_backtest_with_mock_data():
    """Run a backtest using mocked historical data."""
    params = ConsorcioParams(
        carta_credito=100_000.0,
        num_months=6,
        taxa_admin=0.15,
        fundo_reserva=0.02,
        seguro=0.01,
        parcela_pos_contemplacao=2_000.0,
    )

    # Mock 6 months of monthly CDI data
    mock_monthly = [
        {"month": "01/2024", "value": 0.009},
        {"month": "02/2024", "value": 0.008},
        {"month": "03/2024", "value": 0.009},
        {"month": "04/2024", "value": 0.008},
        {"month": "05/2024", "value": 0.009},
        {"month": "06/2024", "value": 0.008},
    ]

    with patch("consorcio_calc.backtest.BCBDataProvider") as MockProvider:
        instance = MockProvider.return_value
        instance.get.return_value = []  # raw daily not used directly
        instance.aggregate_to_monthly.return_value = mock_monthly

        result = run_backtest(
            params=params,
            contemplation_month=3,
            start_date="01/01/2024",
        )

    assert result.contemplation_month == 3
    assert result.total_paid == 2_000.0 * 6
    assert result.consorcio_final_value > 100_000.0  # should have some yield
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_backtest.py -v`
Expected: FAIL with ImportError

**Step 3: Write minimal implementation**

```python
# consorcio_calc/backtest.py
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_backtest.py -v`
Expected: All 1 test PASS

**Step 5: Commit**

```bash
git add consorcio_calc/backtest.py tests/test_backtest.py
git commit -m "feat: add backtest harness for historical scenario analysis"
```

---

### Task 12: Package Exports and Final Wiring

**Files:**
- Modify: `consorcio_calc/__init__.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_package.py -v`
Expected: FAIL with ImportError

**Step 3: Update __init__.py**

```python
# consorcio_calc/__init__.py
from consorcio_calc.models import ConsorcioParams, SimulationResult, SweepResult
from consorcio_calc.benchmarks import FixedRateBenchmark, HistoricalBenchmark
from consorcio_calc.simulator import simulate
from consorcio_calc.sweep import run_sweep
from consorcio_calc.backtest import run_backtest

__all__ = [
    "ConsorcioParams",
    "SimulationResult",
    "SweepResult",
    "FixedRateBenchmark",
    "HistoricalBenchmark",
    "simulate",
    "run_sweep",
    "run_backtest",
]
```

**Step 4: Run ALL tests to verify everything works together**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add consorcio_calc/__init__.py tests/test_package.py
git commit -m "feat: add package exports for clean top-level API"
```

---

### Task 13: Run Full Test Suite and Final Verification

**Step 1: Run full test suite with coverage**

Run: `pytest tests/ -v --cov=consorcio_calc --cov-report=term-missing`
Expected: All tests PASS, reasonable coverage

**Step 2: Quick smoke test in Python REPL**

```python
from consorcio_calc import ConsorcioParams, FixedRateBenchmark, simulate, run_sweep

params = ConsorcioParams(
    carta_credito=200_000,
    num_months=180,
    taxa_admin=0.18,
    fundo_reserva=0.02,
    seguro=0.01,
    parcela_pos_contemplacao=1_800,
    parcela_pre_contemplacao=900,
    rendimento_fundo=0.96,
)
bench = FixedRateBenchmark(annual_rate=0.12)
result = simulate(params, contemplation_month=36, benchmark=bench)
print(f"Total paid: R${result.total_paid:,.2f}")
print(f"Consorcio value: R${result.consorcio_final_value:,.2f}")
print(f"Investment value: R${result.investment_final_value:,.2f}")
print(f"Opportunity cost: R${result.opportunity_cost:,.2f}")
print(f"CET: {result.cet:.2%}")

sweep = run_sweep(params, bench)
print(f"Break-even month: {sweep.break_even_month}")
```

**Step 3: Commit any final fixes if needed**

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

from consorcio_calc import (
    ConsorcioParams,
    FixedRateBenchmark,
    HistoricalBenchmark,
    simulate,
    run_sweep,
)
from consorcio_calc.data_provider import BCBDataProvider, BCBSeries

import numpy as np

app = Flask(__name__)

# Cache CDI data in memory (simple dict cache for POC)
_cdi_cache: dict[str, list[dict]] = {}


def _fetch_cdi_monthly(start_str: str, end_str: str) -> list[dict]:
    key = f"{start_str}|{end_str}"
    if key not in _cdi_cache:
        provider = BCBDataProvider()
        raw_data = provider.get(BCBSeries.CDI, start_str, end_str)
        _cdi_cache[key] = provider.aggregate_to_monthly(raw_data)
    return _cdi_cache[key]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def api_simulate():
    data = request.json

    params = ConsorcioParams(
        carta_credito=data["carta_credito"],
        num_months=data["num_months"],
        parcela_pre_contemplacao=data["meia_parcela"],
        parcela_pos_contemplacao=data["parcela_cheia"],
        rendimento_fundo=data["rendimento_fundo"] / 100,
        reajuste_anual=data["correcao_anual"] / 100 if data["correcao_anual"] > 0 else None,
    )

    num_months = data["num_months"]
    num_cotas = data["num_cotas"]
    contemplation_month = data["contemplation_month"]

    # Build benchmarks
    cdi_benchmark = None
    cdi_info = None
    if data["invest_mode"] == "cdi" or data["fund_mode"] == "cdi":
        start_date = datetime.strptime(data["cdi_start"], "%Y-%m-%d")
        end_dt = start_date + timedelta(days=num_months * 31)
        start_str = start_date.strftime("%d/%m/%Y")
        end_str = end_dt.strftime("%d/%m/%Y")

        monthly_data = _fetch_cdi_monthly(start_str, end_str)
        monthly_rates = [m["value"] for m in monthly_data]

        if len(monthly_rates) < num_months:
            avg_rate = sum(monthly_rates) / len(monthly_rates) if monthly_rates else 0
            monthly_rates.extend([avg_rate] * (num_months - len(monthly_rates)))

        cdi_benchmark = HistoricalBenchmark(monthly_rates=monthly_rates[:num_months])

        avg_monthly = sum(monthly_rates[:num_months]) / len(monthly_rates[:num_months])
        annual_equiv = (1 + avg_monthly) ** 12 - 1
        cdi_info = {
            "avg_monthly": round(avg_monthly * 100, 3),
            "annual_equiv": round(annual_equiv * 100, 2),
            "monthly_rates": monthly_rates[:num_months],
            "months_labels": [m["month"] for m in monthly_data[:num_months]],
        }

    if data["invest_mode"] == "fixed":
        benchmark = FixedRateBenchmark(annual_rate=data["taxa_anual"] / 100)
    else:
        benchmark = cdi_benchmark

    fund_benchmark = None
    if data["fund_mode"] == "cdi":
        fund_benchmark = cdi_benchmark
    elif data["fund_mode"] == "fixed":
        fund_benchmark = FixedRateBenchmark(annual_rate=data["fund_taxa"] / 100)

    # Run sweep and selected simulation
    sweep = run_sweep(params, benchmark, fund_benchmark=fund_benchmark)
    selected = simulate(params, contemplation_month=contemplation_month, benchmark=benchmark, fund_benchmark=fund_benchmark)

    scale = num_cotas
    cons_val = selected.consorcio_final_value * scale
    inv_val = selected.investment_final_value * scale
    diff_abs = cons_val - inv_val
    pct = diff_abs / inv_val * 100 if inv_val else 0
    be = sweep.break_even_month

    # Sweep data
    sweep_data = {
        "months": [r.contemplation_month for r in sweep.results],
        "consorcio": [round(r.consorcio_final_value * scale, 2) for r in sweep.results],
        "investment": [round(r.investment_final_value * scale, 2) for r in sweep.results],
    }

    # Distribution data
    pct_diffs = []
    abs_diffs = []
    for r in sweep.results:
        if r.investment_final_value != 0:
            pct_d = (r.consorcio_final_value - r.investment_final_value) / r.investment_final_value * 100
        else:
            pct_d = 0.0
        pct_diffs.append(round(pct_d, 2))
        abs_diffs.append(round((r.consorcio_final_value - r.investment_final_value) * scale, 0))

    pct_arr = np.array(pct_diffs)
    abs_arr = np.array(abs_diffs)

    # Portfolio diversification
    rng = np.random.default_rng(42)
    n_simulations = 5_000
    cota_counts = sorted(set([1, 2, 3, 5, 10, 15, 20, 30, 50] + [num_cotas]))
    portfolio_stats = []
    for n in cota_counts:
        drawn = rng.integers(0, len(pct_arr), size=(n_simulations, n))
        returns = pct_arr[drawn].mean(axis=1)
        portfolio_stats.append({
            "cotas": n,
            "p5": round(float(np.percentile(returns, 5)), 2),
            "p25": round(float(np.percentile(returns, 25)), 2),
            "p50": round(float(np.percentile(returns, 50)), 2),
            "p75": round(float(np.percentile(returns, 75)), 2),
            "p95": round(float(np.percentile(returns, 95)), 2),
        })

    # Milestones for table
    milestones = [12, 24, 36, 60, 84, 120, 180, 240]
    milestone_months = [m for m in milestones if m <= num_months]
    if be and be not in milestone_months:
        milestone_months.append(be)
        milestone_months.sort()

    table_rows = []
    for m in milestone_months:
        r = sweep.results[m - 1]
        if r.investment_final_value != 0:
            pct_diff = (r.consorcio_final_value - r.investment_final_value) / r.investment_final_value * 100
        else:
            pct_diff = 0.0
        table_rows.append({
            "month": m,
            "year": round(m / 12, 1),
            "total_paid": round(r.total_paid * scale, 0),
            "consorcio": round(r.consorcio_final_value * scale, 0),
            "investment": round(r.investment_final_value * scale, 0),
            "pct_diff": round(pct_diff, 1),
            "winner": "Consórcio" if r.opportunity_cost <= 0 else "Investimento",
            "is_breakeven": m == be,
        })

    # CDI historical data for chart
    cdi_chart = None
    if cdi_info:
        annual_pct = [round(((1 + r) ** 12 - 1) * 100, 2) for r in cdi_info["monthly_rates"]]
        cdi_arr = np.array(annual_pct)
        cdi_chart = {
            "labels": cdi_info["months_labels"],
            "values": annual_pct,
            "avg": round(float(cdi_arr.mean()), 2),
            "median": round(float(np.median(cdi_arr)), 2),
            "p25": round(float(np.percentile(cdi_arr, 25)), 2),
            "p75": round(float(np.percentile(cdi_arr, 75)), 2),
        }

    return jsonify({
        "metrics": {
            "cons_val": round(cons_val, 0),
            "inv_val": round(inv_val, 0),
            "diff_abs": round(diff_abs, 0),
            "pct": round(pct, 1),
            "total_paid": round(selected.total_paid * scale, 0),
            "break_even": be,
        },
        "sweep": sweep_data,
        "distribution": {
            "months": sweep_data["months"],
            "pct_diffs": pct_diffs,
            "p0": round(float(pct_arr.min()), 2),
            "p25": round(float(np.percentile(pct_arr, 25)), 2),
            "p50": round(float(np.percentile(pct_arr, 50)), 2),
            "p75": round(float(np.percentile(pct_arr, 75)), 2),
            "p100": round(float(pct_arr.max()), 2),
            "p0_abs": round(float(abs_arr.min()), 0),
            "p25_abs": round(float(np.percentile(abs_arr, 25)), 0),
            "p50_abs": round(float(np.percentile(abs_arr, 50)), 0),
            "p75_abs": round(float(np.percentile(abs_arr, 75)), 0),
            "p100_abs": round(float(abs_arr.max()), 0),
        },
        "portfolio": portfolio_stats,
        "table": table_rows,
        "cdi_chart": cdi_chart,
        "cdi_info": {"avg_monthly": cdi_info["avg_monthly"], "annual_equiv": cdi_info["annual_equiv"]} if cdi_info else None,
        "num_cotas": num_cotas,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

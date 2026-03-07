import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from consorcio_calc import (
    ConsorcioParams,
    FixedRateBenchmark,
    simulate,
    run_sweep,
)

st.set_page_config(
    page_title="Calculadora de Consórcio",
    page_icon="📊",
    layout="wide",
)

st.title("Calculadora de Consórcio")
st.caption("Compare consórcio vs. investimento direto")

# ── Sidebar: Inputs ──────────────────────────────────────────────────────────

st.sidebar.header("Dados do Consórcio")

carta_credito = st.sidebar.number_input(
    "Carta de crédito por cota (R$)", value=200_000.0, step=10_000.0, format="%.2f"
)
num_cotas = st.sidebar.number_input("Número de cotas", value=10, min_value=1, step=1)
num_months = st.sidebar.number_input("Prazo (meses)", value=238, min_value=12, step=1)

meia_parcela_cota = st.sidebar.number_input(
    "Meia parcela por cota (R$)", value=512.60, step=10.0, format="%.2f"
)
parcela_cheia_cota = st.sidebar.number_input(
    "Parcela cheia por cota (R$)", value=1_025.20, step=10.0, format="%.2f"
)

st.sidebar.subheader("Taxas")
taxa_admin = st.sidebar.number_input(
    "Taxa de administração (%)", value=18.0, step=0.5, format="%.1f"
) / 100
fundo_reserva = st.sidebar.number_input(
    "Fundo de reserva (%)", value=3.7, step=0.1, format="%.1f"
) / 100
seguro = st.sidebar.number_input(
    "Seguro (%)", value=0.0, step=0.1, format="%.1f"
) / 100
correcao_anual = st.sidebar.number_input(
    "Correção anual (%)", value=5.0, step=0.5, format="%.1f"
) / 100
rendimento_fundo = st.sidebar.number_input(
    "Rendimento do fundo (% do CDI)", value=96.0, step=1.0, format="%.0f"
) / 100

st.sidebar.header("Benchmark de Investimento")
taxa_anual = st.sidebar.number_input(
    "Taxa anual do benchmark (%)", value=13.25, step=0.25, format="%.2f"
) / 100

st.sidebar.header("Cenário Específico")
contemplation_month = st.sidebar.slider(
    "Mês de contemplação", min_value=1, max_value=num_months, value=60
)

# ── Build params & run simulation ────────────────────────────────────────────

params = ConsorcioParams(
    carta_credito=carta_credito,
    num_months=num_months,
    taxa_admin=taxa_admin,
    fundo_reserva=fundo_reserva,
    seguro=seguro,
    parcela_pre_contemplacao=meia_parcela_cota,
    parcela_pos_contemplacao=parcela_cheia_cota,
    rendimento_fundo=rendimento_fundo,
    reajuste_anual=correcao_anual if correcao_anual > 0 else None,
)

benchmark = FixedRateBenchmark(annual_rate=taxa_anual)

sweep = run_sweep(params, benchmark)
selected = simulate(params, contemplation_month=contemplation_month, benchmark=benchmark)

# ── Metrics cards ────────────────────────────────────────────────────────────

st.subheader(f"Métricas — Contemplação no mês {contemplation_month} ({contemplation_month / 12:.1f} anos)")

scale = num_cotas

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Pago", f"R$ {selected.total_paid * scale:,.0f}")
col2.metric("Valor Consórcio", f"R$ {selected.consorcio_final_value * scale:,.0f}")
col3.metric("Valor Investimento", f"R$ {selected.investment_final_value * scale:,.0f}")

opp_cost = selected.opportunity_cost * scale
col4.metric(
    "Custo de Oportunidade",
    f"R$ {abs(opp_cost):,.0f}",
    delta=f"{'Consórcio vence' if opp_cost <= 0 else 'Investimento vence'}",
    delta_color="normal" if opp_cost > 0 else "inverse",
)

pct = (selected.consorcio_final_value - selected.investment_final_value) / selected.investment_final_value * 100 if selected.investment_final_value else 0
col5.metric(
    "Retorno vs Investimento",
    f"{pct:+.1f}%",
    delta=f"{'a mais' if pct >= 0 else 'a menos'} no consórcio",
    delta_color="inverse" if pct >= 0 else "normal",
)

be = sweep.break_even_month
col6.metric(
    "Break-Even",
    f"Mês {be} ({be / 12:.1f} anos)" if be else "N/A",
)

# ── Sweep chart ──────────────────────────────────────────────────────────────

st.subheader("Análise de Cenários por Mês de Contemplação")

months = [r.contemplation_month for r in sweep.results]
consorcio_values = [r.consorcio_final_value * scale for r in sweep.results]
invest_values = [r.investment_final_value * scale for r in sweep.results]

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=months, y=consorcio_values,
    name="Consórcio",
    line=dict(color="#2563eb", width=2),
    hovertemplate="Mês %{x}<br>R$ %{y:,.0f}<extra>Consórcio</extra>",
))

fig.add_trace(go.Scatter(
    x=months, y=invest_values,
    name="Investimento",
    line=dict(color="#dc2626", width=2),
    hovertemplate="Mês %{x}<br>R$ %{y:,.0f}<extra>Investimento</extra>",
))

# Break-even and selected month lines — offset annotations when close together
lines_overlap = be and abs(contemplation_month - be) < 15

if be:
    fig.add_vline(
        x=be, line_dash="dash", line_color="gray",
        annotation_text=f"Break-even: mês {be}",
        annotation_position="top left",
        annotation_yshift=20 if lines_overlap else 0,
    )

fig.add_vline(
    x=contemplation_month, line_dash="dot", line_color="#f59e0b",
    annotation_text=f"Selecionado: mês {contemplation_month}",
    annotation_position="top right",
    annotation_yshift=-20 if lines_overlap else 0,
)

fig.update_layout(
    xaxis_title="Mês de Contemplação",
    yaxis_title=f"Valor Final ({num_cotas} cotas, R$)",
    yaxis_tickformat=",.",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500,
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig, use_container_width=True)

# ── Comparison table ─────────────────────────────────────────────────────────

st.subheader("Tabela Comparativa")

milestones = [12, 24, 36, 60, 84, 120, 180, 240]
milestone_months = [m for m in milestones if m <= num_months]
if be and be not in milestone_months:
    milestone_months.append(be)
    milestone_months.sort()

rows = []
for m in milestone_months:
    r = sweep.results[m - 1]
    winner = "Consórcio" if r.opportunity_cost <= 0 else "Investimento"
    # % difference: positive = consórcio ahead, negative = investment ahead
    if r.investment_final_value != 0:
        pct_diff = (r.consorcio_final_value - r.investment_final_value) / r.investment_final_value * 100
    else:
        pct_diff = 0.0
    rows.append({
        "Mês": m,
        "Ano": f"{m / 12:.1f}",
        "Total Pago": f"R$ {r.total_paid * scale:,.0f}",
        "Valor Consórcio": f"R$ {r.consorcio_final_value * scale:,.0f}",
        "Valor Investimento": f"R$ {r.investment_final_value * scale:,.0f}",
        "Diferença %": f"{pct_diff:+.1f}%",
        "Vencedor": winner,
    })

be_idx = None
if be:
    be_idx = next((i for i, row in enumerate(rows) if row["Mês"] == be), None)

df = pd.DataFrame(rows)
st.dataframe(
    df.style.apply(
        lambda row: ["background-color: #1e3a5f; color: #ffffff"] * len(row)
        if be_idx is not None and row.name == be_idx else [""] * len(row),
        axis=1,
    ),
    use_container_width=True,
    hide_index=True,
)

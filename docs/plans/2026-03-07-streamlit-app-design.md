# Streamlit App - Design Document

## Goal

Web UI for the consorcio calculator using Streamlit. Single-page layout with sidebar inputs and main area showing sweep chart, key metrics, and comparison table. All in Portuguese (BR).

## Layout

### Sidebar (Inputs)

**Dados do Consorcio:**
- Carta de credito (R$)
- Numero de cotas
- Prazo (meses)
- Meia parcela por cota (R$)
- Parcela cheia por cota (R$)
- Taxa de administracao (%)
- Fundo de reserva (%)
- Seguro (%)
- Correcao anual (%)
- Rendimento do fundo pos-contemplacao (% do CDI)

**Benchmark de Investimento:**
- Modo: Taxa Fixa or CDI Historico (dropdown)
- Taxa anual (%) - for fixed mode

**Cenario Especifico:**
- Slider to pick a contemplation month for metrics cards

All inputs pre-filled with XP proposal defaults:
- Carta: 200,000 / Cotas: 10 / Prazo: 238
- Meia parcela: 512.60 / Cheia: 1,025.20
- Admin: 18% / Reserva: 3.7% / Seguro: 0%
- Correcao: 5% / Rendimento: 96% CDI
- Benchmark: 13.25% a.a.

### Main Area (top to bottom)

1. **Metricas resumo** - st.metric cards: Total Pago, Valor Consorcio, Valor Investimento, Custo de Oportunidade, Mes de Break-Even. Updates with contemplation month slider.

2. **Grafico de Cenarios (Sweep)** - Plotly line chart, two lines (consorcio vs investimento) across all contemplation months. Vertical dashed line at break-even. Vertical marker at selected contemplation month.

3. **Tabela Comparativa** - DataFrame with results at year 1, 2, 3, 5, 7, 10, 15, 20 and at break-even month.

## Tech

- streamlit + plotly
- Single file: app/app.py
- Imports consorcio_calc directly
- Run: streamlit run app/app.py

## Data Flow

Sidebar inputs -> ConsorcioParams + FixedRateBenchmark -> run_sweep() -> render metrics, chart, table. Computed on each interaction (<1s for 238 months).

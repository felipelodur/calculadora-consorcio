let lastResponse = null;

// Toggle visibility based on radio selections
document.querySelectorAll('input[name="invest_mode"]').forEach(r => r.addEventListener('change', toggleFields));
document.querySelectorAll('input[name="fund_mode"]').forEach(r => r.addEventListener('change', toggleFields));

function toggleFields() {
    const investMode = document.querySelector('input[name="invest_mode"]:checked').value;
    const fundMode = document.querySelector('input[name="fund_mode"]:checked').value;
    const needsCdi = investMode === 'cdi' || fundMode === 'cdi';

    document.getElementById('taxa_anual_wrap').classList.toggle('hidden', investMode !== 'fixed');
    document.getElementById('fund_taxa_wrap').classList.toggle('hidden', fundMode !== 'fixed');
    document.getElementById('cdi_section').classList.toggle('hidden', !needsCdi);
}

function getInputs() {
    return {
        carta_credito: +document.getElementById('carta_credito').value,
        num_cotas: +document.getElementById('num_cotas').value,
        num_months: +document.getElementById('num_months').value,
        meia_parcela: +document.getElementById('meia_parcela').value,
        parcela_cheia: +document.getElementById('parcela_cheia').value,
        correcao_anual: +document.getElementById('correcao_anual').value,
        rendimento_fundo: +document.getElementById('rendimento_fundo').value,
        invest_mode: document.querySelector('input[name="invest_mode"]:checked').value,
        fund_mode: document.querySelector('input[name="fund_mode"]:checked').value,
        taxa_anual: +document.getElementById('taxa_anual').value,
        fund_taxa: +document.getElementById('fund_taxa').value,
        cdi_start: document.getElementById('cdi_start').value,
        contemplation_month: +document.getElementById('contemplation_month').value,
    };
}

function onSliderChange(val) {
    document.getElementById('slider-label').textContent = val;
    if (lastResponse) {
        updateFromSlider(+val);
    }
}

function updateFromSlider(month) {
    // Recompute metrics from sweep data for the selected month
    const d = lastResponse;
    const idx = month - 1;
    const scale = d.num_cotas;
    const consVal = d.sweep.consorcio[idx];
    const invVal = d.sweep.investment[idx];
    const diff = consVal - invVal;
    const pct = invVal ? (diff / invVal * 100) : 0;
    const be = d.metrics.break_even;

    renderMetrics(consVal, invVal, diff, pct, d.metrics.total_paid, be, month);
    renderSweepChart(d.sweep, be, month, scale);
}

async function runSimulation() {
    const btn = document.getElementById('btn-simulate');
    btn.disabled = true;
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');

    const inputs = getInputs();

    // Update slider max
    const slider = document.getElementById('contemplation_month');
    slider.max = inputs.num_months;
    if (+slider.value > inputs.num_months) slider.value = inputs.num_months;

    try {
        const resp = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(inputs),
        });
        const data = await resp.json();
        lastResponse = data;

        renderAll(data, inputs.contemplation_month);
        document.getElementById('results').classList.remove('hidden');
    } catch (e) {
        alert('Erro na simulação: ' + e.message);
    } finally {
        btn.disabled = false;
        document.getElementById('loading').classList.add('hidden');
    }
}

function fmtBrl(v) {
    return 'R$ ' + Math.round(v).toLocaleString('pt-BR');
}

function fmtDelta(v) {
    return (v >= 0 ? '+' : '-') + 'R$ ' + Math.abs(Math.round(v)).toLocaleString('pt-BR');
}

function renderMetrics(consVal, invVal, diff, pct, totalPaid, be, month) {
    document.getElementById('metrics-title').textContent =
        `Métricas — Contemplação no mês ${month} (${(month / 12).toFixed(1)} anos)`;

    const beText = be ? `Break-even: mês ${be} (${(be / 12).toFixed(1)} anos)` : 'Sem break-even';
    document.getElementById('metrics-cards').innerHTML = `
        <div class="metric-card">
            <div class="label">Valor Consórcio</div>
            <div class="value">${fmtBrl(consVal)}</div>
            <div class="delta ${diff >= 0 ? 'positive' : 'negative'}">${fmtDelta(diff)}</div>
        </div>
        <div class="metric-card">
            <div class="label">Valor Investimento</div>
            <div class="value">${fmtBrl(invVal)}</div>
            <div class="delta neutral">Total pago: ${fmtBrl(totalPaid)}</div>
        </div>
        <div class="metric-card">
            <div class="label">Consórcio vs Investimento</div>
            <div class="value">${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%</div>
            <div class="delta neutral">${beText}</div>
        </div>
    `;
}

function renderSweepChart(sweep, be, month, scale) {
    const traces = [
        {
            x: sweep.months, y: sweep.consorcio,
            name: 'Consórcio', line: { color: '#2563eb', width: 2 },
            hovertemplate: 'Mês %{x}<br>R$ %{y:,.0f}<extra>Consórcio</extra>',
        },
        {
            x: sweep.months, y: sweep.investment,
            name: 'Investimento', line: { color: '#dc2626', width: 2 },
            hovertemplate: 'Mês %{x}<br>R$ %{y:,.0f}<extra>Investimento</extra>',
        },
    ];

    const shapes = [];
    const annotations = [];

    if (be) {
        shapes.push({ type: 'line', x0: be, x1: be, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dash', color: 'gray' } });
        annotations.push({ x: be, y: 1, yref: 'paper', text: `Break-even: mês ${be}`, showarrow: false, yanchor: 'bottom', font: { color: 'gray' } });
    }
    shapes.push({ type: 'line', x0: month, x1: month, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dot', color: '#f59e0b' } });
    annotations.push({ x: month, y: 0, yref: 'paper', text: `Selecionado: mês ${month}`, showarrow: false, yanchor: 'top', font: { color: '#f59e0b' } });

    Plotly.react('chart-sweep', traces, {
        xaxis: { title: 'Mês de Contemplação', color: '#9ca3af', gridcolor: '#1f2229' },
        yaxis: { title: `Valor Final (R$)`, tickformat: ',', color: '#9ca3af', gridcolor: '#1f2229' },
        legend: { orientation: 'h', y: 1.08, x: 1, xanchor: 'right' },
        shapes, annotations,
        height: 480, paper_bgcolor: '#0e1117', plot_bgcolor: '#0e1117',
        font: { color: '#d1d5db' }, margin: { l: 70, r: 20, t: 40, b: 50 },
    }, { responsive: true });
}

function renderTable(rows) {
    let html = `<table>
        <thead><tr>
            <th>Mês</th><th>Ano</th><th>Total Pago</th>
            <th>Valor Consórcio</th><th>Valor Investimento</th>
            <th>Diferença %</th><th>Vencedor</th>
        </tr></thead><tbody>`;

    for (const r of rows) {
        const cls = r.is_breakeven ? ' class="breakeven-row"' : '';
        html += `<tr${cls}>
            <td>${r.month}</td>
            <td>${r.year}</td>
            <td>${fmtBrl(r.total_paid)}</td>
            <td>${fmtBrl(r.consorcio)}</td>
            <td>${fmtBrl(r.investment)}</td>
            <td>${r.pct_diff >= 0 ? '+' : ''}${r.pct_diff.toFixed(1)}%</td>
            <td>${r.winner}</td>
        </tr>`;
    }
    html += '</tbody></table>';
    document.getElementById('comparison-table').innerHTML = html;
}

function renderDistribution(dist) {
    const summary = `Assumindo probabilidade igual de contemplação em qualquer mês:`;
    document.getElementById('dist-summary').innerHTML = `<p class="muted">${summary}</p>`;

    const stats = [
        ['Pior cenário', dist.p0], ['Percentil 25%', dist.p25],
        ['Mediana (50%)', dist.p50], ['Percentil 75%', dist.p75],
        ['Melhor cenário', dist.p100],
    ];
    document.getElementById('dist-cards').innerHTML = stats.map(([label, val]) => `
        <div class="metric-card">
            <div class="label">${label}</div>
            <div class="value">${val >= 0 ? '+' : ''}${val.toFixed(2)}%</div>
        </div>
    `).join('');

    const colors = dist.pct_diffs.map(p => p >= 0 ? '#2563eb' : '#dc2626');
    const traces = [{
        x: dist.months, y: dist.pct_diffs, type: 'bar',
        marker: { color: colors },
        hovertemplate: 'Mês %{x}<br>Retorno: %{y:+.2f}%<extra></extra>',
    }];

    const shapes = [
        { type: 'line', y0: 0, y1: 0, x0: 0, x1: 1, xref: 'paper', line: { color: 'white', width: 1 } },
    ];
    const annotations = [];
    for (const [val, label, dash] of [[dist.p25, 'P25', 'dot'], [dist.p50, 'Mediana', 'solid'], [dist.p75, 'P75', 'dot']]) {
        shapes.push({ type: 'line', y0: val, y1: val, x0: 0, x1: 1, xref: 'paper', line: { dash, color: '#9ca3af', width: 1 } });
        annotations.push({ x: 0, xref: 'paper', y: val, text: `${label}: ${val >= 0 ? '+' : ''}${val.toFixed(2)}%`, showarrow: false, xanchor: 'left', font: { color: '#9ca3af', size: 11 } });
    }

    Plotly.react('chart-distribution', traces, {
        xaxis: { title: 'Mês de Contemplação', color: '#9ca3af', gridcolor: '#1f2229' },
        yaxis: { title: 'Retorno (%)', ticksuffix: '%', color: '#9ca3af', gridcolor: '#1f2229' },
        shapes, annotations,
        height: 400, paper_bgcolor: '#0e1117', plot_bgcolor: '#0e1117',
        font: { color: '#d1d5db' }, margin: { l: 60, r: 20, t: 20, b: 50 },
        showlegend: false,
    }, { responsive: true });
}

function renderPortfolio(stats, numCotas) {
    const xs = stats.map(s => s.cotas);

    const traces = [
        // P5-P95 band
        {
            x: xs.concat([...xs].reverse()),
            y: stats.map(s => s.p95).concat([...stats].reverse().map(s => s.p5)),
            fill: 'toself', fillcolor: 'rgba(37,99,235,0.1)',
            line: { color: 'rgba(0,0,0,0)' }, name: 'P5–P95', hoverinfo: 'skip',
        },
        // P25-P75 band
        {
            x: xs.concat([...xs].reverse()),
            y: stats.map(s => s.p75).concat([...stats].reverse().map(s => s.p25)),
            fill: 'toself', fillcolor: 'rgba(37,99,235,0.25)',
            line: { color: 'rgba(0,0,0,0)' }, name: 'P25–P75', hoverinfo: 'skip',
        },
        // Individual lines for hover
        { x: xs, y: stats.map(s => s.p95), name: 'P95', mode: 'lines', line: { width: 0 }, hovertemplate: 'P95: %{y:+.2f}%<extra></extra>' },
        { x: xs, y: stats.map(s => s.p5), name: 'P5', mode: 'lines', line: { width: 0 }, hovertemplate: 'P5: %{y:+.2f}%<extra></extra>' },
        { x: xs, y: stats.map(s => s.p75), name: 'P75', mode: 'lines', line: { width: 0 }, hovertemplate: 'P75: %{y:+.2f}%<extra></extra>' },
        { x: xs, y: stats.map(s => s.p25), name: 'P25', mode: 'lines', line: { width: 0 }, hovertemplate: 'P25: %{y:+.2f}%<extra></extra>' },
        // Median
        { x: xs, y: stats.map(s => s.p50), name: 'Mediana', line: { color: '#2563eb', width: 2 }, hovertemplate: 'Mediana: %{y:+.2f}%<extra></extra>' },
    ];

    const shapes = [
        { type: 'line', y0: 0, y1: 0, x0: 0, x1: 1, xref: 'paper', line: { color: 'white', width: 1 } },
        { type: 'line', x0: numCotas, x1: numCotas, y0: 0, y1: 1, yref: 'paper', line: { dash: 'dot', color: '#f59e0b' } },
    ];
    const annotations = [
        { x: Math.log10(numCotas), xref: 'paper', y: 1, yref: 'paper', text: `Suas cotas: ${numCotas}`, showarrow: false, font: { color: '#f59e0b' },
          // Use actual x position
          x: numCotas, xref: 'x', yanchor: 'bottom',
        },
    ];

    Plotly.react('chart-portfolio', traces, {
        xaxis: { title: 'Número de Cotas', type: 'log', color: '#9ca3af', gridcolor: '#1f2229' },
        yaxis: { title: 'Retorno (%)', ticksuffix: '%', color: '#9ca3af', gridcolor: '#1f2229' },
        shapes, annotations,
        height: 400, paper_bgcolor: '#0e1117', plot_bgcolor: '#0e1117',
        font: { color: '#d1d5db' }, margin: { l: 60, r: 20, t: 20, b: 50 },
        legend: { orientation: 'h', y: 1.08, x: 1, xanchor: 'right' },
    }, { responsive: true });
}

function renderCdiChart(cdi) {
    document.getElementById('cdi-historical-section').classList.remove('hidden');

    document.getElementById('cdi-hist-cards').innerHTML = [
        ['Média', cdi.avg], ['Mediana', cdi.median], ['P25', cdi.p25], ['P75', cdi.p75],
    ].map(([label, val]) => `
        <div class="metric-card">
            <div class="label">${label}</div>
            <div class="value">${val.toFixed(2)}% a.a.</div>
        </div>
    `).join('');

    const traces = [{
        x: cdi.labels, y: cdi.values, name: 'CDI anualizado',
        line: { color: '#2563eb', width: 1 },
        hovertemplate: '%{x}<br>%{y:.2f}% a.a.<extra>CDI</extra>',
    }];

    const shapes = [];
    const annotations = [];
    for (const [val, label, color, dash] of [
        [cdi.avg, 'Média', '#f59e0b', 'solid'],
        [cdi.median, 'Mediana', '#10b981', 'solid'],
        [cdi.p25, 'P25', '#9ca3af', 'dot'],
        [cdi.p75, 'P75', '#9ca3af', 'dot'],
    ]) {
        shapes.push({ type: 'line', y0: val, y1: val, x0: 0, x1: 1, xref: 'paper', line: { dash, color, width: 1 } });
        annotations.push({ x: 0, xref: 'paper', y: val, text: `${label}: ${val.toFixed(2)}%`, showarrow: false, xanchor: 'left', font: { color, size: 11 } });
    }

    Plotly.react('chart-cdi', traces, {
        xaxis: { title: 'Mês', color: '#9ca3af', gridcolor: '#1f2229' },
        yaxis: { title: 'CDI Anualizado (% a.a.)', ticksuffix: '%', color: '#9ca3af', gridcolor: '#1f2229' },
        shapes, annotations,
        height: 400, paper_bgcolor: '#0e1117', plot_bgcolor: '#0e1117',
        font: { color: '#d1d5db' }, margin: { l: 60, r: 20, t: 20, b: 50 },
        showlegend: false,
    }, { responsive: true });
}

function renderAll(data, month) {
    const m = data.metrics;
    const idx = month - 1;
    const consVal = data.sweep.consorcio[idx];
    const invVal = data.sweep.investment[idx];
    const diff = consVal - invVal;
    const pct = invVal ? (diff / invVal * 100) : 0;

    renderMetrics(consVal, invVal, diff, pct, m.total_paid, m.break_even, month);
    renderSweepChart(data.sweep, m.break_even, month, data.num_cotas);
    renderTable(data.table);
    renderDistribution(data.distribution);
    renderPortfolio(data.portfolio, data.num_cotas);

    // CDI info
    if (data.cdi_info) {
        const el = document.getElementById('cdi-info');
        el.textContent = `CDI histórico: taxa média mensal ${data.cdi_info.avg_monthly}% → ${data.cdi_info.annual_equiv}% a.a.`;
        el.classList.remove('hidden');
    } else {
        document.getElementById('cdi-info').classList.add('hidden');
    }

    // CDI chart
    if (data.cdi_chart) {
        renderCdiChart(data.cdi_chart);
    } else {
        document.getElementById('cdi-historical-section').classList.add('hidden');
    }
}

// Init field visibility
toggleFields();

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
    assert params.get_installment(contemplated=False) == 750.0
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

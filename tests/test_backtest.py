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

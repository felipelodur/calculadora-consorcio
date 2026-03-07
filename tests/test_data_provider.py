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

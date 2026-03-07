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

    def _fetch_chunk(self, series: BCBSeries, start_date: str, end_date: str) -> list[dict]:
        """Fetch a single chunk from BCB API."""
        url = self.BASE_URL.format(code=series.code)
        params = {"formato": "json", "dataInicial": start_date, "dataFinal": end_date}
        resp = requests.get(url, params=params, headers={"Accept": "application/json"})
        resp.raise_for_status()
        raw = resp.json()
        return [{"date": item["data"], "value": float(item["valor"])} for item in raw]

    def fetch(self, series: BCBSeries, start_date: str, end_date: str) -> list[dict]:
        """Fetch series data from BCB API. Dates in dd/mm/yyyy format.

        Automatically splits into 8-year chunks for large date ranges.
        """
        from datetime import datetime, timedelta

        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")
        chunk_days = 8 * 365  # ~8 years per chunk to stay under API limit

        all_data: list[dict] = []
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=chunk_days), end)
            chunk = self._fetch_chunk(
                series,
                chunk_start.strftime("%d/%m/%Y"),
                chunk_end.strftime("%d/%m/%Y"),
            )
            all_data.extend(chunk)
            chunk_start = chunk_end + timedelta(days=1)

        self._save_cache(series, all_data)
        return all_data

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

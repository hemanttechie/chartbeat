"""Thin wrapper around requests for calling the Chartbeat Historical Analytics API."""

from __future__ import annotations

from datetime import datetime

import requests


class ChartbeatAPIError(Exception):
    """Wraps HTTP/auth errors with a user-friendly message."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ChartbeatClient:
    """Stateless HTTP client for the Chartbeat Historical Analytics API."""

    BASE_URL = "https://api.chartbeat.com"

    def __init__(self, api_key: str, host: str):
        self.api_key = api_key
        self.host = host

    def get_referrers(self, start: datetime, end: datetime) -> list[dict]:
        """Fetch referrer-level metrics for the date range.

        Returns:
            List of dicts with keys: referrer, total_stories,
            total_engaged_min, avg_engaged_min, page_views,
            quality_page_views, uniques.

        Raises:
            ChartbeatAPIError: On HTTP or auth errors.
        """
        url = f"{self.BASE_URL}/referrers/"
        params = {
            "apikey": self.api_key,
            "host": self.host,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

        try:
            resp = requests.get(url, params=params)
        except requests.ConnectionError:
            raise ChartbeatAPIError(
                "Network connectivity failure — check your connection"
            )

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code in (401, 403):
            raise ChartbeatAPIError(
                "Invalid API key or unauthorized access",
                status_code=resp.status_code,
            )

        if resp.status_code == 404:
            raise ChartbeatAPIError(
                "Property not found — check your domain",
                status_code=404,
            )

        if resp.status_code >= 500:
            raise ChartbeatAPIError(
                "Chartbeat API is unavailable — try again later",
                status_code=resp.status_code,
            )

    def get_urls_for_referrer(
        self, referrer: str, start: datetime, end: datetime
    ) -> list[dict]:
        """Fetch URL-level metrics for a specific referrer.

        Returns:
            List of dicts with keys: url, page_views, uniques, engaged_minutes.

        Raises:
            ChartbeatAPIError: On HTTP or auth errors.
        """
        url = f"{self.BASE_URL}/referrers/urls/"
        params = {
            "apikey": self.api_key,
            "host": self.host,
            "referrer": referrer,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        }

        try:
            resp = requests.get(url, params=params)
        except requests.ConnectionError:
            raise ChartbeatAPIError(
                "Network connectivity failure — check your connection"
            )

        if resp.status_code == 200:
            return resp.json()

        if resp.status_code in (401, 403):
            raise ChartbeatAPIError(
                "Invalid API key or unauthorized access",
                status_code=resp.status_code,
            )

        if resp.status_code == 404:
            raise ChartbeatAPIError(
                "Property not found — check your domain",
                status_code=404,
            )

        if resp.status_code >= 500:
            raise ChartbeatAPIError(
                "Chartbeat API is unavailable — try again later",
                status_code=resp.status_code,
            )

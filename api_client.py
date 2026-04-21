"""Wrapper around the Chartbeat Historical Analytics (Advanced Queries) API.

Uses the 3-step flow: submit → poll status → fetch results.
API key is passed via the X-CB-AK header.
Docs: https://docs.chartbeat.com/cbp/api/historical-api/
"""

from __future__ import annotations

import time
from datetime import datetime

import requests


class ChartbeatAPIError(Exception):
    """Wraps HTTP/auth errors with a user-friendly message."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ChartbeatClient:
    """HTTP client for the Chartbeat Historical Analytics API."""

    BASE_URL = "https://api.chartbeat.com/query/v2"
    POLL_INTERVAL = 5  # seconds between status checks
    MAX_POLLS = 60  # max status checks before timeout

    def __init__(self, api_key: str, host: str):
        self.api_key = api_key
        self.host = host
        self._headers = {"X-CB-AK": api_key}

    def _handle_error(self, resp: requests.Response) -> None:
        """Raise ChartbeatAPIError for non-200 responses."""
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
        raise ChartbeatAPIError(
            f"Unexpected API error (HTTP {resp.status_code})",
            status_code=resp.status_code,
        )

    def _submit_query(self, params: dict) -> str:
        """Submit a query and return the query_id."""
        url = f"{self.BASE_URL}/submit/page/"
        try:
            resp = requests.get(url, params=params, headers=self._headers)
        except requests.ConnectionError:
            raise ChartbeatAPIError(
                "Network connectivity failure — check your connection"
            )

        if resp.status_code != 200:
            self._handle_error(resp)

        data = resp.json()
        query_id = data.get("query_id")
        if not query_id:
            raise ChartbeatAPIError("No query_id returned from submit endpoint")
        return query_id

    def _poll_status(self, query_id: str) -> None:
        """Poll until query status is 'completed'."""
        url = f"{self.BASE_URL}/status/"
        params = {"query_id": query_id, "host": self.host}

        for _ in range(self.MAX_POLLS):
            try:
                resp = requests.get(url, params=params, headers=self._headers)
            except requests.ConnectionError:
                raise ChartbeatAPIError(
                    "Network connectivity failure — check your connection"
                )

            if resp.status_code != 200:
                self._handle_error(resp)

            status = resp.json().get("status", "")
            if status == "completed":
                return
            if status == "deleted":
                raise ChartbeatAPIError("Query was deleted before completion")

            time.sleep(self.POLL_INTERVAL)

        raise ChartbeatAPIError("Query timed out waiting for completion")

    def _fetch_results(self, query_id: str) -> list[dict]:
        """Fetch completed query results as JSON."""
        url = f"{self.BASE_URL}/fetch/"
        params = {"query_id": query_id, "host": self.host, "format": "json"}

        try:
            resp = requests.get(url, params=params, headers=self._headers)
        except requests.ConnectionError:
            raise ChartbeatAPIError(
                "Network connectivity failure — check your connection"
            )

        if resp.status_code != 200:
            self._handle_error(resp)

        data = resp.json()
        if isinstance(data, list):
            return data
        # Some responses wrap data in a key
        if isinstance(data, dict):
            for key in ("data", "rows", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []

    def _run_query(self, params: dict) -> list[dict]:
        """Submit, poll, and fetch a query."""
        query_id = self._submit_query(params)
        self._poll_status(query_id)
        return self._fetch_results(query_id)

    def get_referrers(self, start: datetime, end: datetime) -> list[dict]:
        """Fetch referrer-level metrics for the date range.

        Queries the Historical API with canonical_referrer dimension and
        standard engagement metrics.

        Returns:
            List of dicts with keys including: canonical_referrer (mapped to
            'referrer'), page_views, page_uniques, total_engaged_sec, etc.

        Raises:
            ChartbeatAPIError: On HTTP or auth errors.
        """
        params = {
            "host": self.host,
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "metrics": "page_views,quality_page_views,page_uniques,total_engaged_sec",
            "dimensions": "canonical_referrer",
            "sort_column": "page_views",
            "sort_order": "desc",
            "limit": 500,
            "tz": "America/New_York",
        }

        rows = self._run_query(params)

        # Normalize column names to match our internal model
        normalized = []
        for row in rows:
            entry = {}
            entry["referrer"] = row.get("canonical_referrer", row.get("referrer", ""))
            entry["page_views"] = int(row.get("page_views", 0))
            entry["quality_page_views"] = int(row.get("quality_page_views", 0))
            entry["uniques"] = int(row.get("page_uniques", row.get("uniques", 0)))
            total_sec = float(row.get("total_engaged_sec", 0))
            entry["total_engaged_min"] = round(total_sec / 60, 2)
            # Estimate stories as 1 per referrer row in this aggregation
            entry["total_stories"] = int(row.get("total_stories", 1))
            entry["avg_engaged_min"] = (
                round(entry["total_engaged_min"] / entry["total_stories"], 2)
                if entry["total_stories"] > 0
                else 0.0
            )
            normalized.append(entry)

        return normalized

    def get_urls_for_referrer(
        self, referrer: str, start: datetime, end: datetime
    ) -> list[dict]:
        """Fetch URL-level metrics for a specific referrer.

        Returns:
            List of dicts with keys: url (from path), page_views, uniques,
            engaged_minutes.

        Raises:
            ChartbeatAPIError: On HTTP or auth errors.
        """
        params = {
            "host": self.host,
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "metrics": "page_views,page_uniques,total_engaged_sec",
            "dimensions": "path",
            "canonical_referrer": referrer,
            "sort_column": "page_views",
            "sort_order": "desc",
            "limit": 500,
            "tz": "America/New_York",
        }

        rows = self._run_query(params)

        normalized = []
        for row in rows:
            entry = {}
            path = row.get("path", row.get("url", ""))
            entry["url"] = f"{self.host}{path}" if path and not path.startswith("http") else path
            entry["page_views"] = int(row.get("page_views", 0))
            entry["uniques"] = int(row.get("page_uniques", row.get("uniques", 0)))
            total_sec = float(row.get("total_engaged_sec", 0))
            entry["engaged_minutes"] = round(total_sec / 60, 2)
            normalized.append(entry)

        return normalized

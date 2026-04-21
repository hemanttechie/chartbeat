"""Wrapper around the Chartbeat Real-Time API.

Uses /live/referrers/v3/ and /live/toppages/v3/ endpoints.
API key is passed as the 'apikey' query parameter.
Docs: https://docs.chartbeat.com/cbp/api/real-time-apis/traffic-data
"""

from __future__ import annotations

import requests


class ChartbeatAPIError(Exception):
    """Wraps HTTP/auth errors with a user-friendly message."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ChartbeatClient:
    """HTTP client for the Chartbeat Real-Time API."""

    BASE_URL = "https://api.chartbeat.com"

    def __init__(self, api_key: str, host: str):
        self.api_key = api_key
        self.host = host

    def _request(self, endpoint: str, extra_params: dict | None = None) -> dict | list:
        """Make a GET request and handle errors."""
        params = {"apikey": self.api_key, "host": self.host}
        headers = {"X-CB-AK": self.api_key}
        if extra_params:
            params.update(extra_params)

        try:
            resp = requests.get(f"{self.BASE_URL}{endpoint}", params=params, headers=headers)
        except requests.ConnectionError:
            raise ChartbeatAPIError(
                "Network connectivity failure — check your connection"
            )

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
        if resp.status_code != 200:
            raise ChartbeatAPIError(
                f"Unexpected API error (HTTP {resp.status_code})",
                status_code=resp.status_code,
            )

        return resp.json()

    def get_referrers(self) -> list[dict]:
        """Fetch live referrer data with concurrent visitor counts.

        Uses /live/referrers/v3/ endpoint.

        Returns:
            List of dicts with keys: referrer, page_views (concurrents),
            and placeholder metrics for compatibility.
        """
        data = self._request("/live/referrers/v3/", {"limit": 100})

        referrers_map = data.get("referrers", {})
        if not referrers_map:
            return []

        normalized = []
        for name, concurrents in referrers_map.items():
            normalized.append({
                "referrer": name if name.strip() else "Direct",
                "page_views": int(concurrents),
                "uniques": int(concurrents),
                "total_stories": 0,
                "total_engaged_min": 0.0,
                "avg_engaged_min": 0.0,
                "quality_page_views": 0,
            })

        # Sort by concurrents descending
        normalized.sort(key=lambda x: x["page_views"], reverse=True)
        return normalized

    def get_toppages(self, limit: int = 100) -> list[dict]:
        """Fetch top pages with referrer breakdown.

        Uses /live/toppages/v3/ endpoint.

        Returns:
            List of dicts with page path, visitors, and top referrers.
        """
        data = self._request("/live/toppages/v3/", {"limit": limit})
        pages = data.get("pages", [])

        normalized = []
        for page in pages:
            stats = page.get("stats", {})
            path = page.get("path", "")
            visitors = stats.get("people", 0)
            toprefs = stats.get("toprefs", [])

            engaged_time = stats.get("engaged_time", {})
            search = int(stats.get("search", 0))
            social = int(stats.get("social", 0))
            internal = int(stats.get("internal", 0))
            links = int(stats.get("links", 0))
            direct = int(visitors) - (search + social + internal + links)
            if direct < 0:
                direct = 0

            entry = {
                "url": path,
                "title": page.get("title", ""),
                "page_views": int(visitors),
                "avg_engaged_sec": round(engaged_time.get("avg", 0), 1),
                "new_visitors": int(stats.get("new", 0)),
                "returning": int(visitors) - int(stats.get("new", 0)),
                "top_referrers": [
                    {"referrer": r.get("domain", ""), "visitors": r.get("visitors", 0)}
                    for r in toprefs
                ],
                "search": search,
                "social": social,
                "direct": direct,
                "internal": internal,
                "links": links,
            }
            normalized.append(entry)

        return normalized

    def get_urls_for_referrer(self, referrer: str) -> list[dict]:
        """Get top pages filtered by a specific referrer.

        Fetches top pages and filters to those where the referrer
        appears in the top referrers list.

        Returns:
            List of dicts with url, page_views, uniques, engaged_minutes.
        """
        pages = self.get_toppages(limit=500)

        filtered = []
        for page in pages:
            for ref in page.get("top_referrers", []):
                if ref["referrer"].lower() == referrer.lower() and ref["visitors"] > 0:
                    filtered.append({
                        "url": page["url"],
                        "page_views": ref["visitors"],
                        "avg_engaged_sec": page.get("avg_engaged_sec", 0),
                    })
                    break

        filtered.sort(key=lambda x: x["page_views"], reverse=True)
        return filtered

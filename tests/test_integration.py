"""Integration tests for the end-to-end data pipeline.

Tests the full flow: API client (real-time) → categorizer → transforms,
plus empty data and error scenarios.

Requirements referenced: 2.1, 2.3, 5.1, 5.5
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from api_client import ChartbeatAPIError, ChartbeatClient
from categorizer import categorize_dataframe
from transforms import add_section_column, aggregate_by_category


@pytest.fixture
def client():
    return ChartbeatClient(api_key="test-key", host="example.com")


def _mock_referrers_response(referrers_map):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"referrers": referrers_map}
    return resp


def _mock_toppages_response(pages):
    resp = MagicMock(status_code=200)
    resp.json.return_value = {"pages": pages}
    return resp


class TestFullPipeline:
    def test_referrer_pipeline_produces_categorized_dataframe(self, client):
        referrers = {"Google Search": 150, "Facebook": 80, "Google Discover": 40, "ChatGPT": 10, "unknown-site": 5}
        with patch("api_client.requests.get", return_value=_mock_referrers_response(referrers)):
            raw = client.get_referrers()

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)

        assert {"referrer", "page_views", "uniques", "category"}.issubset(set(df.columns))

        expected = {
            "Google Search": "Search",
            "Facebook": "Social",
            "Google Discover": "Discovery",
            "ChatGPT": "AI",
            "unknown-site": "Direct/Other",
        }
        for _, row in df.iterrows():
            assert row["category"] == expected[row["referrer"]]

    def test_aggregation_after_categorization(self, client):
        referrers = {"Google Search": 150, "Facebook": 80, "Google Discover": 40, "ChatGPT": 10, "unknown-site": 5}
        with patch("api_client.requests.get", return_value=_mock_referrers_response(referrers)):
            raw = client.get_referrers()

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)
        agg = aggregate_by_category(df)

        assert len(agg) == 5
        assert set(agg["category"]) == {"Search", "Social", "Discovery", "AI", "Direct/Other"}

    def test_url_level_pipeline_adds_section(self, client):
        pages = [
            {"path": "example.com/news/article.html", "stats": {"people": 100, "engaged_time": {"avg": 30}, "toprefs": [{"domain": "Google Search", "visitors": 60}], "search": 60, "social": 0, "direct": 20, "internal": 10, "links": 10}},
            {"path": "example.com/sports/game.html", "stats": {"people": 50, "engaged_time": {"avg": 45}, "toprefs": [{"domain": "Google Search", "visitors": 30}], "search": 30, "social": 10, "direct": 5, "internal": 3, "links": 2}},
        ]
        with patch("api_client.requests.get", return_value=_mock_toppages_response(pages)):
            raw = client.get_urls_for_referrer("Google Search")

        df = pd.DataFrame(raw)
        df = add_section_column(df)

        assert "section" in df.columns
        assert df["section"].tolist() == ["news", "sports"]


class TestEmptyDataScenarios:
    def test_empty_referrers(self, client):
        with patch("api_client.requests.get", return_value=_mock_referrers_response({})):
            raw = client.get_referrers()
        assert raw == []

    def test_empty_toppages(self, client):
        with patch("api_client.requests.get", return_value=_mock_toppages_response([])):
            raw = client.get_urls_for_referrer("Google Search")
        assert raw == []

    def test_empty_referrer_data_aggregation(self):
        df = pd.DataFrame(columns=["referrer", "total_stories", "total_engaged_min", "avg_engaged_min", "page_views", "quality_page_views", "uniques", "category"])
        agg = aggregate_by_category(df)
        assert agg.empty


class TestErrorScenarios:
    def test_401_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 401

    def test_500_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=500)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 500

    def test_url_endpoint_401(self, client):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search")
        assert exc_info.value.status_code == 401

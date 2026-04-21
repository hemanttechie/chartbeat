"""Integration tests for the end-to-end data pipeline.

Tests the full flow: API client (submit→status→fetch) → categorizer → transforms,
plus empty data and error scenarios.

Requirements referenced: 2.1, 2.3, 5.1, 5.5
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from api_client import ChartbeatAPIError, ChartbeatClient
from categorizer import categorize_dataframe
from transforms import add_section_column, aggregate_by_category


@pytest.fixture
def client():
    return ChartbeatClient(api_key="test-key", host="example.com")


@pytest.fixture
def date_range():
    return datetime(2024, 1, 1), datetime(2024, 1, 31)


def _mock_3step(api_data):
    """Return 3 mock responses for submit → status → fetch."""
    submit = MagicMock(status_code=200)
    submit.json.return_value = {"query_id": "q1"}
    status = MagicMock(status_code=200)
    status.json.return_value = {"status": "completed"}
    fetch = MagicMock(status_code=200)
    fetch.json.return_value = api_data
    return [submit, status, fetch]


@pytest.fixture
def sample_referrer_api_data():
    """Realistic API response with canonical_referrer dimension."""
    return [
        {"canonical_referrer": "Google Search", "page_views": 5000, "quality_page_views": 4000, "page_uniques": 3000, "total_engaged_sec": 15000},
        {"canonical_referrer": "Facebook", "page_views": 2000, "quality_page_views": 1500, "page_uniques": 1200, "total_engaged_sec": 5400},
        {"canonical_referrer": "Google Discover", "page_views": 800, "quality_page_views": 700, "page_uniques": 500, "total_engaged_sec": 3600},
        {"canonical_referrer": "ChatGPT", "page_views": 200, "quality_page_views": 150, "page_uniques": 100, "total_engaged_sec": 900},
        {"canonical_referrer": "some-unknown-source", "page_views": 50, "quality_page_views": 30, "page_uniques": 20, "total_engaged_sec": 240},
    ]


@pytest.fixture
def sample_url_api_data():
    return [
        {"path": "/news/breaking-story.html", "page_views": 500, "page_uniques": 300, "total_engaged_sec": 1500},
        {"path": "/sports/game-recap.html", "page_views": 200, "page_uniques": 150, "total_engaged_sec": 600},
    ]


class TestFullPipeline:
    def test_referrer_pipeline_produces_categorized_dataframe(self, client, date_range, sample_referrer_api_data):
        with patch("api_client.requests.get", side_effect=_mock_3step(sample_referrer_api_data)):
            raw = client.get_referrers(*date_range)

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)

        required_cols = {"referrer", "page_views", "uniques", "category"}
        assert required_cols.issubset(set(df.columns))

        expected = {
            "Google Search": "Search",
            "Facebook": "Social",
            "Google Discover": "Discovery",
            "ChatGPT": "AI",
            "some-unknown-source": "Direct/Other",
        }
        for _, row in df.iterrows():
            assert row["category"] == expected[row["referrer"]]

    def test_aggregation_after_categorization(self, client, date_range, sample_referrer_api_data):
        with patch("api_client.requests.get", side_effect=_mock_3step(sample_referrer_api_data)):
            raw = client.get_referrers(*date_range)

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)
        agg = aggregate_by_category(df)

        assert len(agg) == 5
        assert set(agg["category"]) == {"Search", "Social", "Discovery", "AI", "Direct/Other"}
        search_row = agg[agg["category"] == "Search"].iloc[0]
        assert search_row["page_views"] == 5000

    def test_url_level_pipeline_adds_section(self, client, date_range, sample_url_api_data):
        with patch("api_client.requests.get", side_effect=_mock_3step(sample_url_api_data)):
            raw = client.get_urls_for_referrer("Google Search", *date_range)

        df = pd.DataFrame(raw)
        df = add_section_column(df)

        assert "section" in df.columns
        sections = df["section"].tolist()
        assert sections == ["news", "sports"]


class TestEmptyDataScenarios:
    def test_empty_referrer_list(self, client, date_range):
        with patch("api_client.requests.get", side_effect=_mock_3step([])):
            raw = client.get_referrers(*date_range)
        assert raw == []
        assert pd.DataFrame(raw).empty

    def test_empty_url_level_response(self, client, date_range):
        with patch("api_client.requests.get", side_effect=_mock_3step([])):
            raw = client.get_urls_for_referrer("Google Search", *date_range)
        assert raw == []

    def test_empty_referrer_data_aggregation(self):
        df = pd.DataFrame(columns=["referrer", "total_stories", "total_engaged_min", "avg_engaged_min", "page_views", "quality_page_views", "uniques", "category"])
        agg = aggregate_by_category(df)
        assert agg.empty
        assert "category" in agg.columns


class TestErrorScenarios:
    def test_401_raises_api_error(self, client, date_range):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code == 401

    def test_500_raises_api_error(self, client, date_range):
        mock_resp = MagicMock(status_code=500)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code == 500

    def test_url_endpoint_401_raises_api_error(self, client, date_range):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)
        assert exc_info.value.status_code == 401

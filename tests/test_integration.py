"""Integration tests for the end-to-end data pipeline.

Tests the full flow: API client → categorizer → transforms,
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


@pytest.fixture
def sample_referrer_data():
    """Realistic referrer data spanning multiple categories."""
    return [
        {
            "referrer": "Google Search",
            "total_stories": 50,
            "total_engaged_min": 250.0,
            "avg_engaged_min": 5.0,
            "page_views": 5000,
            "quality_page_views": 4000,
            "uniques": 3000,
        },
        {
            "referrer": "Facebook",
            "total_stories": 30,
            "total_engaged_min": 90.0,
            "avg_engaged_min": 3.0,
            "page_views": 2000,
            "quality_page_views": 1500,
            "uniques": 1200,
        },
        {
            "referrer": "Google Discover",
            "total_stories": 10,
            "total_engaged_min": 60.0,
            "avg_engaged_min": 6.0,
            "page_views": 800,
            "quality_page_views": 700,
            "uniques": 500,
        },
        {
            "referrer": "ChatGPT",
            "total_stories": 5,
            "total_engaged_min": 15.0,
            "avg_engaged_min": 3.0,
            "page_views": 200,
            "quality_page_views": 150,
            "uniques": 100,
        },
        {
            "referrer": "some-unknown-source",
            "total_stories": 2,
            "total_engaged_min": 4.0,
            "avg_engaged_min": 2.0,
            "page_views": 50,
            "quality_page_views": 30,
            "uniques": 20,
        },
    ]


@pytest.fixture
def sample_url_data():
    """Realistic URL-level data for a referrer."""
    return [
        {
            "url": "example.com/news/breaking-story.html",
            "page_views": 500,
            "uniques": 300,
            "engaged_minutes": 25.0,
        },
        {
            "url": "example.com/sports/game-recap.html",
            "page_views": 200,
            "uniques": 150,
            "engaged_minutes": 10.0,
        },
    ]


class TestFullPipeline:
    """Test the complete data flow: api_client → categorizer → transforms."""

    def test_referrer_pipeline_produces_categorized_dataframe(
        self, client, date_range, sample_referrer_data
    ):
        """Validates: Requirements 2.1, 2.2 — data flows through the full pipeline correctly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_referrer_data

        with patch("api_client.requests.get", return_value=mock_resp):
            raw = client.get_referrers(*date_range)

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)

        # All required columns present
        required_cols = {
            "referrer", "total_stories", "total_engaged_min",
            "avg_engaged_min", "page_views", "quality_page_views",
            "uniques", "category",
        }
        assert required_cols.issubset(set(df.columns))

        # Correct categories assigned
        expected_categories = {
            "Google Search": "Search",
            "Facebook": "Social",
            "Google Discover": "Discovery",
            "ChatGPT": "AI",
            "some-unknown-source": "Direct/Other",
        }
        for _, row in df.iterrows():
            assert row["category"] == expected_categories[row["referrer"]]

    def test_aggregation_after_categorization(
        self, client, date_range, sample_referrer_data
    ):
        """Validates: Requirements 2.1, 4.1 — aggregation produces correct per-category sums."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_referrer_data

        with patch("api_client.requests.get", return_value=mock_resp):
            raw = client.get_referrers(*date_range)

        df = pd.DataFrame(raw)
        df = categorize_dataframe(df)
        agg = aggregate_by_category(df)

        # One row per unique category
        assert len(agg) == 5
        assert set(agg["category"]) == {"Search", "Social", "Discovery", "AI", "Direct/Other"}

        # Verify Search category sums (only Google Search in sample)
        search_row = agg[agg["category"] == "Search"].iloc[0]
        assert search_row["page_views"] == 5000
        assert search_row["total_stories"] == 50

    def test_url_level_pipeline_adds_section(
        self, client, date_range, sample_url_data
    ):
        """Validates: Requirements 5.1, 5.3 — URL data flows through and gets section column."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = sample_url_data

        with patch("api_client.requests.get", return_value=mock_resp):
            raw = client.get_urls_for_referrer("Google Search", *date_range)

        df = pd.DataFrame(raw)
        df = add_section_column(df)

        assert "section" in df.columns
        sections = df["section"].tolist()
        assert sections == ["news", "sports"]

        # Original columns preserved
        assert "url" in df.columns
        assert "page_views" in df.columns
        assert "uniques" in df.columns
        assert "engaged_minutes" in df.columns


class TestEmptyDataScenarios:
    """Test pipeline behavior when API returns empty data."""

    def test_empty_referrer_list_produces_empty_dataframe(
        self, client, date_range
    ):
        """Validates: Requirements 2.3 — empty API response handled gracefully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []

        with patch("api_client.requests.get", return_value=mock_resp):
            raw = client.get_referrers(*date_range)

        assert raw == []

        # Pipeline should handle empty list without errors
        df = pd.DataFrame(raw)
        assert df.empty

    def test_empty_url_level_response(self, client, date_range):
        """Validates: Requirements 5.5 — empty URL-level response handled gracefully."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []

        with patch("api_client.requests.get", return_value=mock_resp):
            raw = client.get_urls_for_referrer("Google Search", *date_range)

        assert raw == []

        df = pd.DataFrame(raw)
        assert df.empty

    def test_empty_referrer_data_aggregation(self):
        """Validates: Requirements 2.3 — aggregation on empty data returns empty with correct schema."""
        df = pd.DataFrame(
            columns=[
                "referrer", "total_stories", "total_engaged_min",
                "avg_engaged_min", "page_views", "quality_page_views",
                "uniques", "category",
            ]
        )
        agg = aggregate_by_category(df)

        assert agg.empty
        assert "category" in agg.columns
        assert "page_views" in agg.columns


class TestErrorScenarios:
    """Test that API errors propagate correctly through the pipeline."""

    def test_401_raises_api_error_with_message(self, client, date_range):
        """Validates: Requirements 2.3 — 401 produces ChartbeatAPIError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    def test_500_raises_api_error_with_message(self, client, date_range):
        """Validates: Requirements 2.3 — 500 produces ChartbeatAPIError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code == 500
        assert "unavailable" in exc_info.value.message

    def test_url_endpoint_401_raises_api_error(self, client, date_range):
        """Validates: Requirements 5.1, 2.3 — URL endpoint 401 produces ChartbeatAPIError."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

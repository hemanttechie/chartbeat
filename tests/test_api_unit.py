"""Unit tests for API client error handling.

Requirements referenced: 2.3, 1.3
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from api_client import ChartbeatAPIError, ChartbeatClient


@pytest.fixture
def client():
    return ChartbeatClient(api_key="test-key", host="example.com")


@pytest.fixture
def date_range():
    return datetime(2024, 1, 1), datetime(2024, 1, 31)


class TestGetReferrersErrorHandling:
    """Test error handling for get_referrers method."""

    def test_401_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 401 → ChartbeatAPIError with auth message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code == 401
        assert "Invalid API key or unauthorized access" in exc_info.value.message

    def test_404_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 404 → ChartbeatAPIError with property message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code == 404
        assert "Property not found" in exc_info.value.message

    def test_500_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 500 → ChartbeatAPIError with unavailable message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code == 500
        assert "Chartbeat API is unavailable" in exc_info.value.message

    def test_connection_error_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get raising ConnectionError → ChartbeatAPIError with network message."""
        import requests

        with patch("api_client.requests.get", side_effect=requests.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)

        assert exc_info.value.status_code is None
        assert "Network connectivity failure" in exc_info.value.message

    def test_200_returns_list_of_dicts(self, client, date_range):
        """Mock requests.get returning 200 with valid JSON → returns list of dicts."""
        expected_data = [
            {
                "referrer": "Google Search",
                "total_stories": 10,
                "total_engaged_min": 50.0,
                "avg_engaged_min": 5.0,
                "page_views": 100,
                "quality_page_views": 80,
                "uniques": 60,
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = expected_data

        with patch("api_client.requests.get", return_value=mock_resp):
            result = client.get_referrers(*date_range)

        assert result == expected_data


class TestGetUrlsForReferrerErrorHandling:
    """Test error handling for get_urls_for_referrer method."""

    def test_401_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 401 → ChartbeatAPIError with auth message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)

        assert exc_info.value.status_code == 401
        assert "Invalid API key or unauthorized access" in exc_info.value.message

    def test_404_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 404 → ChartbeatAPIError with property message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)

        assert exc_info.value.status_code == 404
        assert "Property not found" in exc_info.value.message

    def test_500_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get returning 500 → ChartbeatAPIError with unavailable message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)

        assert exc_info.value.status_code == 500
        assert "Chartbeat API is unavailable" in exc_info.value.message

    def test_connection_error_raises_chartbeat_api_error(self, client, date_range):
        """Mock requests.get raising ConnectionError → ChartbeatAPIError with network message."""
        import requests

        with patch("api_client.requests.get", side_effect=requests.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)

        assert exc_info.value.status_code is None
        assert "Network connectivity failure" in exc_info.value.message

    def test_200_returns_list_of_dicts(self, client, date_range):
        """Mock requests.get returning 200 with valid JSON → returns list of dicts."""
        expected_data = [
            {
                "url": "example.com/news/article-1",
                "page_views": 50,
                "uniques": 30,
                "engaged_minutes": 12.5,
            }
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = expected_data

        with patch("api_client.requests.get", return_value=mock_resp):
            result = client.get_urls_for_referrer("Google Search", *date_range)

        assert result == expected_data

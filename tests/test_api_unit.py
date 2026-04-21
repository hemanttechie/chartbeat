"""Unit tests for API client error handling.

Tests the 3-step Historical API flow: submit → status → fetch.
Requirements referenced: 2.3, 1.3
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, call

import pytest

from api_client import ChartbeatAPIError, ChartbeatClient


@pytest.fixture
def client():
    return ChartbeatClient(api_key="test-key", host="example.com")


@pytest.fixture
def date_range():
    return datetime(2024, 1, 1), datetime(2024, 1, 31)


def _mock_submit_response(query_id="test-query-id"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"query_id": query_id}
    return resp


def _mock_status_response(status="completed"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"status": status}
    return resp


def _mock_fetch_response(data):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = data
    return resp


def _mock_error_response(status_code):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


class TestGetReferrersErrorHandling:
    """Test error handling for get_referrers method."""

    def test_401_on_submit_raises_api_error(self, client, date_range):
        with patch("api_client.requests.get", return_value=_mock_error_response(401)):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    def test_404_on_submit_raises_api_error(self, client, date_range):
        with patch("api_client.requests.get", return_value=_mock_error_response(404)):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code == 404
        assert "Property not found" in exc_info.value.message

    def test_500_on_submit_raises_api_error(self, client, date_range):
        with patch("api_client.requests.get", return_value=_mock_error_response(500)):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code == 500
        assert "unavailable" in exc_info.value.message

    def test_connection_error_raises_api_error(self, client, date_range):
        import requests as req
        with patch("api_client.requests.get", side_effect=req.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers(*date_range)
        assert exc_info.value.status_code is None
        assert "Network connectivity failure" in exc_info.value.message

    def test_successful_flow_returns_normalized_data(self, client, date_range):
        """Full submit → status → fetch flow with normalized output."""
        api_data = [
            {
                "canonical_referrer": "Google Search",
                "page_views": 100,
                "quality_page_views": 80,
                "page_uniques": 60,
                "total_engaged_sec": 3000,
            }
        ]
        responses = [
            _mock_submit_response("q1"),
            _mock_status_response("completed"),
            _mock_fetch_response(api_data),
        ]
        with patch("api_client.requests.get", side_effect=responses):
            result = client.get_referrers(*date_range)

        assert len(result) == 1
        assert result[0]["referrer"] == "Google Search"
        assert result[0]["page_views"] == 100
        assert result[0]["uniques"] == 60
        assert result[0]["total_engaged_min"] == 50.0  # 3000s / 60

    def test_empty_response_returns_empty_list(self, client, date_range):
        responses = [
            _mock_submit_response("q1"),
            _mock_status_response("completed"),
            _mock_fetch_response([]),
        ]
        with patch("api_client.requests.get", side_effect=responses):
            result = client.get_referrers(*date_range)
        assert result == []


class TestGetUrlsForReferrerErrorHandling:
    """Test error handling for get_urls_for_referrer method."""

    def test_401_on_submit_raises_api_error(self, client, date_range):
        with patch("api_client.requests.get", return_value=_mock_error_response(401)):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    def test_500_on_submit_raises_api_error(self, client, date_range):
        with patch("api_client.requests.get", return_value=_mock_error_response(500)):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)
        assert exc_info.value.status_code == 500
        assert "unavailable" in exc_info.value.message

    def test_connection_error_raises_api_error(self, client, date_range):
        import requests as req
        with patch("api_client.requests.get", side_effect=req.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search", *date_range)
        assert exc_info.value.status_code is None
        assert "Network connectivity failure" in exc_info.value.message

    def test_successful_flow_returns_normalized_url_data(self, client, date_range):
        api_data = [
            {
                "path": "/news/article-1.html",
                "page_views": 50,
                "page_uniques": 30,
                "total_engaged_sec": 750,
            }
        ]
        responses = [
            _mock_submit_response("q2"),
            _mock_status_response("completed"),
            _mock_fetch_response(api_data),
        ]
        with patch("api_client.requests.get", side_effect=responses):
            result = client.get_urls_for_referrer("Google Search", *date_range)

        assert len(result) == 1
        assert result[0]["url"] == "example.com/news/article-1.html"
        assert result[0]["page_views"] == 50
        assert result[0]["uniques"] == 30
        assert result[0]["engaged_minutes"] == 12.5  # 750s / 60

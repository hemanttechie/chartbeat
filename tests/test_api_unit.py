"""Unit tests for API client error handling.

Tests the real-time API endpoints: /live/referrers/v3/ and /live/toppages/v3/.
Requirements referenced: 2.3, 1.3
"""

from unittest.mock import MagicMock, patch

import pytest

from api_client import ChartbeatAPIError, ChartbeatClient


@pytest.fixture
def client():
    return ChartbeatClient(api_key="test-key", host="example.com")


class TestGetReferrersErrorHandling:

    def test_401_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.message

    def test_403_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=403)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 403

    def test_404_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=404)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 404
        assert "Property not found" in exc_info.value.message

    def test_500_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=500)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code == 500
        assert "unavailable" in exc_info.value.message

    def test_connection_error_raises_api_error(self, client):
        import requests as req
        with patch("api_client.requests.get", side_effect=req.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_referrers()
        assert exc_info.value.status_code is None
        assert "Network connectivity failure" in exc_info.value.message

    def test_successful_response_returns_normalized_data(self, client):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "referrers": {"Google Search": 150, "Facebook": 80, "Direct": 50}
        }
        with patch("api_client.requests.get", return_value=mock_resp):
            result = client.get_referrers()

        assert len(result) == 3
        assert result[0]["referrer"] == "Google Search"
        assert result[0]["page_views"] == 150
        assert result[1]["referrer"] == "Facebook"
        assert result[2]["referrer"] == "Direct"

    def test_empty_referrers_returns_empty_list(self, client):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"referrers": {}}
        with patch("api_client.requests.get", return_value=mock_resp):
            result = client.get_referrers()
        assert result == []


class TestGetUrlsForReferrerErrorHandling:

    def test_401_raises_api_error(self, client):
        mock_resp = MagicMock(status_code=401)
        with patch("api_client.requests.get", return_value=mock_resp):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search")
        assert exc_info.value.status_code == 401

    def test_connection_error_raises_api_error(self, client):
        import requests as req
        with patch("api_client.requests.get", side_effect=req.ConnectionError()):
            with pytest.raises(ChartbeatAPIError) as exc_info:
                client.get_urls_for_referrer("Google Search")
        assert exc_info.value.status_code is None

    def test_successful_response_filters_by_referrer(self, client):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {
            "pages": [
                {
                    "path": "example.com/news/article-1.html",
                    "stats": {
                        "people": 100,
                        "engaged_time": {"avg": 30},
                        "toprefs": [
                            {"domain": "Google Search", "visitors": 60},
                            {"domain": "Facebook", "visitors": 20},
                        ],
                        "search": 60, "social": 20, "direct": 10,
                        "internal": 5, "links": 5,
                    },
                },
                {
                    "path": "example.com/sports/game.html",
                    "stats": {
                        "people": 50,
                        "engaged_time": {"avg": 45},
                        "toprefs": [
                            {"domain": "Facebook", "visitors": 30},
                        ],
                        "search": 10, "social": 30, "direct": 5,
                        "internal": 3, "links": 2,
                    },
                },
            ]
        }
        with patch("api_client.requests.get", return_value=mock_resp):
            result = client.get_urls_for_referrer("Google Search")

        # Only the first page has Google Search as a referrer
        assert len(result) == 1
        assert result[0]["url"] == "example.com/news/article-1.html"
        assert result[0]["page_views"] == 60

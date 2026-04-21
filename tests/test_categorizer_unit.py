"""Unit tests for categorizer known mappings.

Tests each named referrer maps to the correct category and unknown referrers
fall back to "Direct/Other".

Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

import pytest

from categorizer import categorize_referrer


# --- Search (Req 3.2) ---

@pytest.mark.parametrize(
    "referrer",
    [
        "Google Search",
        "Bing",
        "Yahoo Search",
        "DuckDuckGo",
        "Brave Search",
        "Ecosia",
        "Petal Search",
    ],
)
def test_search_referrers(referrer: str) -> None:
    assert categorize_referrer(referrer) == "Search"


# --- Social (Req 3.3) ---

@pytest.mark.parametrize(
    "referrer",
    ["Facebook", "Instagram", "Twitter", "Reddit", "YouTube"],
)
def test_social_referrers(referrer: str) -> None:
    assert categorize_referrer(referrer) == "Social"


# --- Discovery (Req 3.4) ---

@pytest.mark.parametrize(
    "referrer",
    ["Google Discover", "Google News", "JioNews"],
)
def test_discovery_referrers(referrer: str) -> None:
    assert categorize_referrer(referrer) == "Discovery"


# --- AMP (Req 3.5) ---

@pytest.mark.parametrize(
    "referrer",
    [
        "example.cdn.ampproject.org",
        "news.cdn.ampproject.org",
        "abc123.cdn.ampproject.org",
    ],
)
def test_amp_referrers(referrer: str) -> None:
    assert categorize_referrer(referrer) == "AMP"


# --- AI (Req 3.6) ---

@pytest.mark.parametrize(
    "referrer",
    ["ChatGPT", "Google Gemini"],
)
def test_ai_referrers(referrer: str) -> None:
    assert categorize_referrer(referrer) == "AI"


# --- Direct/Other fallback (Req 3.7) ---

@pytest.mark.parametrize(
    "referrer",
    ["unknown-referrer", "", "some random site"],
)
def test_direct_other_fallback(referrer: str) -> None:
    assert categorize_referrer(referrer) == "Direct/Other"

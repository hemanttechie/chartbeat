"""Unit tests for transforms module edge cases.

Tests extract_section with trailing slashes, query strings, fragments, no-path URLs.
Tests aggregate_by_category with empty DataFrame and single-category DataFrame.

Requirements: 4.1, 5.3
"""

import pandas as pd
import pytest

from transforms import aggregate_by_category, extract_section


# --- extract_section edge cases ---


@pytest.mark.parametrize(
    "url,expected",
    [
        ("example.com/", ""),
        ("example.com/news/article.html", "news"),
        ("example.com/sports/", "sports"),
        ("https://example.com/tech/page?id=1", "tech"),
        ("https://example.com/world/story#section", "world"),
        ("example.com", ""),
        ("http://example.com", ""),
    ],
    ids=[
        "trailing-slash-only",
        "nested-path",
        "trailing-slash-after-segment",
        "query-string",
        "fragment",
        "no-scheme-no-path",
        "scheme-no-path",
    ],
)
def test_extract_section(url: str, expected: str) -> None:
    """extract_section handles trailing slashes, query strings, fragments, and no-path URLs."""
    assert extract_section(url) == expected


# --- aggregate_by_category edge cases ---


def test_aggregate_by_category_empty_dataframe() -> None:
    """aggregate_by_category returns empty DataFrame with correct columns for empty input."""
    df = pd.DataFrame(
        columns=[
            "category",
            "total_stories",
            "total_engaged_min",
            "page_views",
            "quality_page_views",
            "uniques",
        ]
    )
    result = aggregate_by_category(df)

    assert result.empty
    expected_cols = [
        "category",
        "total_stories",
        "total_engaged_min",
        "page_views",
        "quality_page_views",
        "uniques",
        "avg_engaged_min",
    ]
    assert list(result.columns) == expected_cols


def test_aggregate_by_category_single_category() -> None:
    """aggregate_by_category returns one row with correct sums for single-category input."""
    df = pd.DataFrame(
        {
            "category": ["Search", "Search", "Search"],
            "total_stories": [10, 20, 30],
            "total_engaged_min": [100.0, 200.0, 300.0],
            "page_views": [1000, 2000, 3000],
            "quality_page_views": [500, 600, 700],
            "uniques": [100, 200, 300],
        }
    )
    result = aggregate_by_category(df)

    assert len(result) == 1
    row = result.iloc[0]
    assert row["category"] == "Search"
    assert row["total_stories"] == 60
    assert row["total_engaged_min"] == 600.0
    assert row["page_views"] == 6000
    assert row["quality_page_views"] == 1800
    assert row["uniques"] == 600
    assert row["avg_engaged_min"] == pytest.approx(10.0)


def test_aggregate_by_category_multiple_categories() -> None:
    """aggregate_by_category returns correct number of rows for multiple categories."""
    df = pd.DataFrame(
        {
            "category": ["Search", "Social", "Search", "AI"],
            "total_stories": [10, 5, 20, 8],
            "total_engaged_min": [100.0, 50.0, 200.0, 80.0],
            "page_views": [1000, 500, 2000, 800],
            "quality_page_views": [400, 200, 600, 300],
            "uniques": [100, 50, 200, 80],
        }
    )
    result = aggregate_by_category(df)

    assert len(result) == 3
    assert set(result["category"]) == {"Search", "Social", "AI"}

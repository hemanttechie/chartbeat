"""Pure-function module for data shaping: aggregation, section extraction, and metric computation."""

from urllib.parse import urlparse

import pandas as pd


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Group by 'category' and sum numeric metrics.

    Returns DataFrame with columns: category, total_stories,
    total_engaged_min, page_views, quality_page_views, uniques.
    avg_engaged_min is recomputed as total_engaged_min / total_stories.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "category",
                "total_stories",
                "total_engaged_min",
                "page_views",
                "quality_page_views",
                "uniques",
                "avg_engaged_min",
            ]
        )

    sum_cols = [
        "total_stories",
        "total_engaged_min",
        "page_views",
        "quality_page_views",
        "uniques",
    ]
    grouped = df.groupby("category", as_index=False)[sum_cols].sum()
    avg = grouped["total_engaged_min"] / grouped["total_stories"]
    grouped["avg_engaged_min"] = avg.where(grouped["total_stories"] != 0, 0.0)

    return grouped


def extract_section(url: str) -> str:
    """Extract the first path segment from a URL.

    Example: 'malayalamtv9.com/india/article-slug.html' → 'india'
    Returns '' if no path segment exists.
    """
    # If the URL has no scheme, prepend one so urlparse can handle it
    if "://" not in url:
        url = "http://" + url

    parsed = urlparse(url)
    # Split path into segments, filtering out empty strings from leading/trailing slashes
    segments = [s for s in parsed.path.split("/") if s]
    if segments:
        return segments[0]
    return ""


def add_section_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'section' column by applying extract_section to the 'url' column."""
    result = df.copy()
    result["section"] = result["url"].apply(extract_section)
    return result

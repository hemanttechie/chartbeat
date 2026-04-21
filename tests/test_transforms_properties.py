# Feature: chartbeat-referrer-dashboard, Property 5: Category aggregation correctness
"""Property-based tests for category aggregation correctness.

Validates: Requirements 4.1
"""

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames

from transforms import aggregate_by_category

CATEGORIES = ["Search", "Social", "Direct/Other"]


@st.composite
def category_dataframes(draw):
    """Generate DataFrames with random categories and numeric metrics."""
    n_rows = draw(st.integers(min_value=1, max_value=30))
    categories = draw(
        st.lists(st.sampled_from(CATEGORIES), min_size=n_rows, max_size=n_rows)
    )
    total_stories = draw(
        st.lists(st.integers(min_value=0, max_value=1000), min_size=n_rows, max_size=n_rows)
    )
    total_engaged_min = draw(
        st.lists(st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False), min_size=n_rows, max_size=n_rows)
    )
    page_views = draw(
        st.lists(st.integers(min_value=0, max_value=100000), min_size=n_rows, max_size=n_rows)
    )
    quality_page_views = draw(
        st.lists(st.integers(min_value=0, max_value=100000), min_size=n_rows, max_size=n_rows)
    )
    uniques = draw(
        st.lists(st.integers(min_value=0, max_value=100000), min_size=n_rows, max_size=n_rows)
    )

    df = pd.DataFrame({
        "category": categories,
        "total_stories": total_stories,
        "total_engaged_min": total_engaged_min,
        "page_views": page_views,
        "quality_page_views": quality_page_views,
        "uniques": uniques,
    })
    return df


@settings(max_examples=100, deadline=None)
@given(df=category_dataframes())
def test_aggregate_by_category_one_row_per_category(df: pd.DataFrame) -> None:
    """aggregate_by_category produces exactly one row per unique category.

    **Validates: Requirements 4.1**
    """
    result = aggregate_by_category(df)
    unique_categories = set(df["category"].unique())
    result_categories = set(result["category"].values)

    assert result_categories == unique_categories, (
        f"Expected categories {unique_categories}, got {result_categories}"
    )
    assert len(result) == len(unique_categories), (
        f"Expected {len(unique_categories)} rows, got {len(result)}"
    )


@settings(max_examples=100, deadline=None)
@given(df=category_dataframes())
def test_aggregate_by_category_correct_page_views_sum(df: pd.DataFrame) -> None:
    """The summed page_views for each category equals the sum in the original DataFrame.

    **Validates: Requirements 4.1**
    """
    result = aggregate_by_category(df)

    for _, row in result.iterrows():
        cat = row["category"]
        expected_sum = df[df["category"] == cat]["page_views"].sum()
        assert row["page_views"] == expected_sum, (
            f"For category {cat!r}: expected page_views sum {expected_sum}, "
            f"got {row['page_views']}"
        )


# Feature: chartbeat-referrer-dashboard, Property 7: Section extraction from URLs
"""Property-based tests for section extraction from URLs.

Validates: Requirements 5.3
"""

from transforms import extract_section


@st.composite
def url_with_known_segment(draw):
    """Generate a URL with a known first path segment."""
    domain = draw(st.from_regex(r"[a-z]+\.[a-z]+", fullmatch=True))
    segment = draw(st.from_regex(r"[a-z0-9]+", fullmatch=True))
    # Optionally add a rest-of-path after the segment
    rest = draw(st.from_regex(r"(/[a-z0-9\-]+)*", fullmatch=True))
    url = f"{domain}/{segment}{rest}"
    return url, segment


@settings(max_examples=100, deadline=None)
@given(data=url_with_known_segment())
def test_extract_section_returns_first_path_segment(data) -> None:
    """For any URL with a path, extract_section returns the first path segment.

    **Validates: Requirements 5.3**
    """
    url, expected_segment = data
    result = extract_section(url)
    assert result == expected_segment, (
        f"For URL {url!r}: expected section {expected_segment!r}, got {result!r}"
    )


@settings(max_examples=100, deadline=None)
@given(domain=st.from_regex(r"[a-z]+\.[a-z]+", fullmatch=True))
def test_extract_section_returns_empty_for_no_path(domain: str) -> None:
    """For any URL with no path (just a domain), extract_section returns empty string.

    **Validates: Requirements 5.3**
    """
    result = extract_section(domain)
    assert result == "", (
        f"For domain-only URL {domain!r}: expected empty string, got {result!r}"
    )

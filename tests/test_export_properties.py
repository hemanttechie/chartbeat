# Feature: chartbeat-referrer-dashboard, Property 8: CSV export round-trip
"""Property-based tests for CSV export round-trip preservation of column headers."""

import io

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from export import to_csv_bytes


# **Validates: Requirements 6.3**

STANDARD_COLUMNS = [
    "referrer",
    "total_stories",
    "total_engaged_min",
    "page_views",
    "quality_page_views",
    "uniques",
]


@st.composite
def metric_dataframes(draw):
    """Generate DataFrames with the standard metric columns and random data."""
    n_rows = draw(st.integers(min_value=1, max_value=20))

    data = {
        "referrer": draw(
            st.lists(
                st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\r\n")),
                min_size=n_rows,
                max_size=n_rows,
            )
        ),
        "total_stories": draw(
            st.lists(st.integers(min_value=0, max_value=10000), min_size=n_rows, max_size=n_rows)
        ),
        "total_engaged_min": draw(
            st.lists(st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False), min_size=n_rows, max_size=n_rows)
        ),
        "page_views": draw(
            st.lists(st.integers(min_value=0, max_value=1000000), min_size=n_rows, max_size=n_rows)
        ),
        "quality_page_views": draw(
            st.lists(st.integers(min_value=0, max_value=1000000), min_size=n_rows, max_size=n_rows)
        ),
        "uniques": draw(
            st.lists(st.integers(min_value=0, max_value=1000000), min_size=n_rows, max_size=n_rows)
        ),
    }

    return pd.DataFrame(data)


@given(df=metric_dataframes())
@settings(max_examples=100, deadline=None)
def test_csv_export_roundtrip_preserves_column_headers(df):
    """For any DataFrame with standard metric columns, exporting via to_csv_bytes
    and parsing back preserves column headers."""
    csv_bytes = to_csv_bytes(df)
    parsed_df = pd.read_csv(io.BytesIO(csv_bytes))
    assert list(parsed_df.columns) == list(df.columns)

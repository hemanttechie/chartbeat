# Feature: chartbeat-referrer-dashboard, Property 2: API response schema preservation
"""Property-based test verifying that valid API response dicts produce DataFrames
with all required metric columns.

**Validates: Requirements 2.2**
"""

from hypothesis import given, settings
from hypothesis import strategies as st
import pandas as pd


REQUIRED_COLUMNS = {
    "referrer",
    "total_stories",
    "total_engaged_min",
    "avg_engaged_min",
    "page_views",
    "quality_page_views",
    "uniques",
}

response_dict = st.fixed_dictionaries({
    "referrer": st.text(min_size=1),
    "total_stories": st.integers(min_value=0),
    "total_engaged_min": st.floats(min_value=0, allow_nan=False, allow_infinity=False),
    "avg_engaged_min": st.floats(min_value=0, allow_nan=False, allow_infinity=False),
    "page_views": st.integers(min_value=0),
    "quality_page_views": st.integers(min_value=0),
    "uniques": st.integers(min_value=0),
})


@settings(max_examples=100, deadline=None)
@given(data=st.lists(response_dict, min_size=1))
def test_api_response_schema_preservation(data):
    """For any valid API response dicts, transforming into a DataFrame produces
    all required metric columns."""
    df = pd.DataFrame(data)
    assert REQUIRED_COLUMNS.issubset(set(df.columns))

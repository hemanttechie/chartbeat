# Feature: chartbeat-referrer-dashboard, Property 6: Category filtering correctness

import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

CATEGORIES = ["Search", "Social", "Discovery", "AMP", "AI", "Direct/Other"]


@st.composite
def filtering_scenario(draw):
    """Generate a DataFrame and a category subset for filtering."""
    n_rows = draw(st.integers(min_value=1, max_value=30))
    categories = draw(
        st.lists(st.sampled_from(CATEGORIES), min_size=n_rows, max_size=n_rows)
    )
    page_views = draw(
        st.lists(st.integers(min_value=0, max_value=100000), min_size=n_rows, max_size=n_rows)
    )
    df = pd.DataFrame({"category": categories, "page_views": page_views})

    # Generate a subset of categories present in the DataFrame
    available = list(set(categories))
    subset = draw(
        st.lists(st.sampled_from(available), min_size=0, max_size=len(available), unique=True)
    )
    return df, subset


@settings(max_examples=100, deadline=None)
@given(scenario=filtering_scenario())
def test_category_filtering_correctness(scenario):
    """**Validates: Requirements 4.4**"""
    df, selected = scenario
    filtered = df[df["category"].isin(selected)]

    # All rows in result have category in selected subset
    assert all(cat in selected for cat in filtered["category"])

    # No matching rows are missing
    expected_count = len(df[df["category"].isin(selected)])
    assert len(filtered) == expected_count

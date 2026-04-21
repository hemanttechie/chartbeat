# Feature: chartbeat-referrer-dashboard, Property 3: Categorizer output validity and fallback
"""Property-based tests for categorizer output validity.

Validates: Requirements 3.1, 3.7
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from categorizer import categorize_referrer, DEFAULT_RULES

VALID_CATEGORIES = {"Search", "Social", "Discovery", "AMP", "AI", "Direct/Other"}


@settings(max_examples=100, deadline=None)
@given(referrer=st.text())
def test_categorize_referrer_returns_valid_category(referrer: str) -> None:
    """For any arbitrary string, categorize_referrer returns exactly one of the six valid categories.

    **Validates: Requirements 3.1, 3.7**
    """
    result = categorize_referrer(referrer)
    assert result in VALID_CATEGORIES, (
        f"categorize_referrer({referrer!r}) returned {result!r}, "
        f"which is not in {VALID_CATEGORIES}"
    )


@settings(max_examples=100, deadline=None)
@given(referrer=st.text())
def test_categorize_referrer_fallback_with_empty_rules(referrer: str) -> None:
    """For any string with no matching rules (empty rules list), the result is 'Direct/Other'.

    **Validates: Requirements 3.1, 3.7**
    """
    result = categorize_referrer(referrer, rules=[])
    assert result == "Direct/Other", (
        f"categorize_referrer({referrer!r}, rules=[]) returned {result!r}, "
        f"expected 'Direct/Other'"
    )


# Feature: chartbeat-referrer-dashboard, Property 4: AMP pattern categorization
@settings(max_examples=100, deadline=None)
@given(
    subdomain=st.text(
        alphabet=st.characters(whitelist_categories=("L", "N")),
        min_size=1,
    )
)
def test_amp_pattern_categorized_as_amp(subdomain: str) -> None:
    """For any string matching {subdomain}.cdn.ampproject.org, categorize_referrer returns 'AMP'.

    **Validates: Requirements 3.5**
    """
    referrer = f"{subdomain}.cdn.ampproject.org"
    result = categorize_referrer(referrer)
    assert result == "AMP", (
        f"categorize_referrer({referrer!r}) returned {result!r}, expected 'AMP'"
    )

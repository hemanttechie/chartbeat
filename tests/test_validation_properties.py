# Feature: chartbeat-referrer-dashboard, Property 1: Input validation correctness
"""Property-based test for input validation correctness.

**Validates: Requirements 1.2**

Property 1: For any tuple of (api_key, property, start_date, end_date),
validation returns success iff all strings non-empty and start < end.
"""

import sys
from unittest.mock import MagicMock, patch
from datetime import date, timedelta

# Mock streamlit before importing app
mock_st = MagicMock()
# Make date_input return real date objects so module-level code works
mock_st.date_input.side_effect = [date.today() - timedelta(days=7), date.today()]
# Make text_input return empty strings
mock_st.text_input.return_value = ''
# Make button return False so the submit block doesn't execute
mock_st.button.return_value = False
sys.modules['streamlit'] = mock_st

from app import validate_inputs

from hypothesis import given, settings
from hypothesis import strategies as st
from datetime import date


@settings(max_examples=100, deadline=None)
@given(
    api_key=st.text(),
    property_domain=st.text(),
    start_date=st.dates(),
    end_date=st.dates(),
)
def test_validation_correctness(api_key, property_domain, start_date, end_date):
    """Property 1: Input validation correctness.

    Validation returns (True, '') iff api_key.strip() != '' AND
    property_domain.strip() != '' AND start_date < end_date.
    """
    result = validate_inputs(api_key, property_domain, start_date, end_date)
    is_valid, msg = result

    all_fields_valid = (
        api_key.strip() != ''
        and property_domain.strip() != ''
        and start_date < end_date
    )

    if all_fields_valid:
        assert is_valid is True, (
            f"Expected valid for api_key={api_key!r}, "
            f"property_domain={property_domain!r}, "
            f"start_date={start_date}, end_date={end_date}"
        )
        assert msg == ''
    else:
        assert is_valid is False, (
            f"Expected invalid for api_key={api_key!r}, "
            f"property_domain={property_domain!r}, "
            f"start_date={start_date}, end_date={end_date}"
        )
        assert msg != ''

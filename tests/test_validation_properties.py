# Feature: chartbeat-referrer-dashboard, Property 1: Input validation correctness
"""Property-based test for input validation correctness.

**Validates: Requirements 1.2**

Property 1: For any tuple of (api_key, property),
validation returns success iff all strings non-empty.
"""

import sys
from unittest.mock import MagicMock
from datetime import date, timedelta

# Mock streamlit before importing app
mock_st = MagicMock()
mock_st.text_input.return_value = ''
mock_st.button.return_value = False
sys.modules['streamlit'] = mock_st

from app import validate_inputs

from hypothesis import given, settings
from hypothesis import strategies as st


@settings(max_examples=100, deadline=None)
@given(
    api_key=st.text(),
    property_domain=st.text(),
)
def test_validation_correctness(api_key, property_domain):
    """Property 1: Input validation correctness.

    Validation returns (True, '') iff api_key.strip() != '' AND
    property_domain.strip() != ''.
    """
    is_valid, msg = validate_inputs(api_key, property_domain)

    all_fields_valid = (
        api_key.strip() != ''
        and property_domain.strip() != ''
    )

    if all_fields_valid:
        assert is_valid is True
        assert msg == ''
    else:
        assert is_valid is False
        assert msg != ''

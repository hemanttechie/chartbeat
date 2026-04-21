# Implementation Plan: Chartbeat Referrer Dashboard

## Overview

Incremental implementation of a Streamlit dashboard that fetches Chartbeat referrer data, categorizes referrers, displays aggregated and URL-level views, and supports CSV export. Built across five Python modules: `api_client.py`, `categorizer.py`, `transforms.py`, `export.py`, and `app.py`. Each task builds on the previous, wiring components together progressively.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create project root with `api_client.py`, `categorizer.py`, `transforms.py`, `export.py`, `app.py`, and `tests/` directory
  - Create `requirements.txt` with `streamlit`, `pandas`, `requests`, `hypothesis`, `pytest`
  - Define `ChartbeatAPIError` exception class in `api_client.py`
  - _Requirements: 1.1, 2.1_

- [x] 2. Implement categorizer module
  - [x] 2.1 Implement `CategoryRule` dataclass, `DEFAULT_RULES`, and `categorize_referrer()`
    - Define `CategoryRule` with `category`, `match_type`, `value` fields
    - Implement `DEFAULT_RULES` list covering Search, Social, Discovery, AMP, AI categories
    - Implement `categorize_referrer()` with ordered first-match-wins logic and "Direct/Other" fallback
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 2.2 Implement `categorize_dataframe()`
    - Apply `categorize_referrer()` to each row's `referrer` column, adding a `category` column
    - _Requirements: 3.1_

  - [x] 2.3 Write property test for categorizer output validity (Property 3)
    - **Property 3: Categorizer output validity and fallback**
    - For any arbitrary string, `categorize_referrer` returns exactly one of the six valid categories; non-matching strings return "Direct/Other"
    - **Validates: Requirements 3.1, 3.7**

  - [x] 2.4 Write property test for AMP pattern categorization (Property 4)
    - **Property 4: AMP pattern categorization**
    - For any string matching `{subdomain}.cdn.ampproject.org`, `categorize_referrer` returns "AMP"
    - **Validates: Requirements 3.5**

  - [x] 2.5 Write unit tests for categorizer known mappings
    - Test each named referrer maps to the correct category (Google Search → Search, Facebook → Social, Google Discover → Discovery, ChatGPT → AI, etc.)
    - Test unknown referrer strings fall back to "Direct/Other"
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 3. Implement transforms module
  - [x] 3.1 Implement `aggregate_by_category()`
    - Group DataFrame by `category`, sum numeric metrics, recompute `avg_engaged_min` as `total_engaged_min / total_stories`
    - _Requirements: 4.1_

  - [x] 3.2 Implement `extract_section()` and `add_section_column()`
    - Extract first path segment from URL string; return empty string for URLs with no path
    - Apply extraction across DataFrame `url` column to add `section` column
    - _Requirements: 5.3_

  - [x] 3.3 Write property test for category aggregation correctness (Property 5)
    - **Property 5: Category aggregation correctness**
    - For any DataFrame with a `category` column and numeric metrics, `aggregate_by_category` produces one row per unique category with correct sums
    - **Validates: Requirements 4.1**

  - [x] 3.4 Write property test for section extraction (Property 7)
    - **Property 7: Section extraction from URLs**
    - For any URL of the form `domain/{segment}/...`, `extract_section` returns `{segment}`; for URLs with no path, returns empty string
    - **Validates: Requirements 5.3**

  - [x] 3.5 Write unit tests for transforms edge cases
    - Test `extract_section` with trailing slashes, query strings, fragments, no-path URLs
    - Test `aggregate_by_category` with empty DataFrame and single-category DataFrame
    - _Requirements: 4.1, 5.3_

- [x] 4. Implement export module
  - [x] 4.1 Implement `to_csv_bytes()`
    - Convert DataFrame to UTF-8 CSV bytes using `df.to_csv(index=False).encode("utf-8")`
    - _Requirements: 6.3_

  - [x] 4.2 Write property test for CSV export round-trip (Property 8)
    - **Property 8: CSV export round-trip**
    - For any DataFrame with standard metric columns, exporting via `to_csv_bytes` and parsing back preserves column headers
    - **Validates: Requirements 6.3**

- [x] 5. Checkpoint - Ensure all pure-function module tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement API client module
  - [x] 6.1 Implement `ChartbeatClient.__init__()` and `get_referrers()`
    - Store `api_key` and `host`; construct GET request to Chartbeat `/referrers/` endpoint with `apikey`, `host`, `start_date`, `end_date` query params
    - Parse JSON response into list of dicts; raise `ChartbeatAPIError` on HTTP errors (401, 404, 5xx) and connection failures
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 6.2 Implement `get_urls_for_referrer()`
    - Construct GET request to URL-level endpoint with referrer, date range params
    - Parse JSON response; raise `ChartbeatAPIError` on errors
    - _Requirements: 5.1_

  - [x] 6.3 Write property test for API response schema preservation (Property 2)
    - **Property 2: API response schema preservation**
    - For any valid API response dicts, transforming into a DataFrame produces all required metric columns
    - **Validates: Requirements 2.2**

  - [x] 6.4 Write unit tests for API client error handling
    - Mock `requests.get` returning 401, 404, 500, empty body, and connection errors
    - Verify `ChartbeatAPIError` raised with correct messages and status codes
    - _Requirements: 2.3, 1.3_

- [x] 7. Implement Streamlit app - Configuration Panel and validation
  - [x] 7.1 Implement sidebar configuration panel in `app.py`
    - Render `st.text_input` for API key and property, `st.date_input` for start/end dates
    - Store values in `st.session_state` for persistence across reruns
    - _Requirements: 1.1, 1.4_

  - [x] 7.2 Implement input validation logic
    - Validate all fields non-empty and start date before end date
    - Display `st.error()` with specific messages on validation failure
    - _Requirements: 1.2, 1.3_

  - [x] 7.3 Write property test for input validation correctness (Property 1)
    - **Property 1: Input validation correctness**
    - For any tuple of (api_key, property, start_date, end_date), validation returns success iff all strings non-empty and start < end
    - **Validates: Requirements 1.2**

- [x] 8. Implement Streamlit app - Aggregated Performance View
  - [x] 8.1 Wire data fetching pipeline
    - On valid config submission, call `ChartbeatClient.get_referrers()`, convert to DataFrame, apply `categorize_dataframe()`, compute aggregations
    - Cache results with `@st.cache_data`; show `st.spinner` during fetch
    - Catch `ChartbeatAPIError` and display `st.error()` with the error message
    - _Requirements: 2.1, 2.4, 3.1_

  - [x] 8.2 Render category summary table and referrer detail table
    - Display aggregated metrics per category in a summary table
    - Display per-referrer detail table, sortable by any metric column
    - _Requirements: 4.1, 4.2_

  - [x] 8.3 Render bar charts and category filter
    - Display bar charts comparing `page_views` and `uniques` across categories
    - Add `st.multiselect` for filtering by one or more categories
    - _Requirements: 4.3, 4.4_

  - [x] 8.4 Write property test for category filtering correctness (Property 6)
    - **Property 6: Category filtering correctness**
    - For any DataFrame and category subset, filtering returns exactly the matching rows with no omissions
    - **Validates: Requirements 4.4**

- [x] 9. Implement Streamlit app - URL-Level Drill-Down and Export
  - [x] 9.1 Implement referrer selection and URL-level data display
    - On referrer selection, call `ChartbeatClient.get_urls_for_referrer()`, convert to DataFrame, add section column
    - Display URL-level table with url, page_views, uniques, engaged_minutes, section columns, sortable by any column
    - Show "No URL-level data available" message when response is empty
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 9.2 Implement CSV export download buttons
    - Add `st.download_button` for referrer summary CSV export
    - Add `st.download_button` for URL-level data CSV export
    - Use `to_csv_bytes()` for formatting
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 9.3 Write integration tests for end-to-end pipeline
    - Mock API responses and verify full pipeline from config to rendered tables
    - Test empty data scenarios display correct messages
    - _Requirements: 2.1, 2.3, 5.1, 5.5_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis with `max_examples=100` and `deadline=None`
- Checkpoints at tasks 5 and 10 ensure incremental validation
- All 8 correctness properties from the design are covered by property test sub-tasks

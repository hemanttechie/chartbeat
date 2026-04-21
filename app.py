"""Streamlit entry point for the Chartbeat Referrer Dashboard.

Uses the Chartbeat Real-Time API to show live referrer data
with categorization, drill-down, and CSV export.
"""

import streamlit as st
import pandas as pd

from api_client import ChartbeatClient, ChartbeatAPIError
from categorizer import categorize_dataframe
from transforms import aggregate_by_category, add_section_column
from export import to_csv_bytes


def validate_inputs(api_key: str, property_domain: str) -> tuple[bool, str]:
    """Validate configuration inputs.

    Returns (True, '') if valid, (False, error_message) if invalid.
    """
    if not api_key or not api_key.strip():
        return False, "API Key is required"
    if not property_domain or not property_domain.strip():
        return False, "Property (domain) is required"
    return True, ""


def fetch_referrer_data(api_key: str, host: str):
    """Fetch and process live referrer data."""
    client = ChartbeatClient(api_key=api_key, host=host)
    raw_data = client.get_referrers()
    if not raw_data:
        return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(raw_data)
    if "referrer" not in df.columns:
        return pd.DataFrame(), pd.DataFrame()
    df = categorize_dataframe(df)
    agg_df = aggregate_by_category(df)
    return df, agg_df


st.set_page_config(page_title="Chartbeat Referrer Dashboard", layout="wide")
st.title("Chartbeat Referrer Dashboard")
st.caption("Live referrer data from the Chartbeat Real-Time API")

# Sidebar configuration panel
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Chartbeat API Key", type="password", key="api_key")
    property_domain = st.text_input("Property (domain)", placeholder="e.g. tv9marathi.com", key="property_domain")
    submit = st.button("Fetch Live Data")

if submit:
    is_valid, error_msg = validate_inputs(api_key, property_domain)
    if not is_valid:
        st.error(error_msg)
    else:
        with st.spinner("Fetching live data from Chartbeat..."):
            try:
                df, agg_df = fetch_referrer_data(api_key, property_domain)
                if df.empty:
                    st.warning("No referrer data found")
                else:
                    st.session_state["referrer_df"] = df
                    st.session_state["agg_df"] = agg_df
            except ChartbeatAPIError as e:
                st.error(e.message)

# Display data if available in session state
if "referrer_df" in st.session_state and "agg_df" in st.session_state:
    df = st.session_state["referrer_df"]
    agg_df = st.session_state["agg_df"]

    # Category filter
    all_categories = sorted(df["category"].unique().tolist())
    selected_categories = st.multiselect(
        "Filter by Category",
        options=all_categories,
        default=all_categories,
    )

    # Filter data
    filtered_df = df[df["category"].isin(selected_categories)]
    filtered_agg = agg_df[agg_df["category"].isin(selected_categories)]

    # Only show columns with meaningful data — rename for clarity
    agg_display = filtered_agg[["category", "page_views", "uniques"]].copy()
    agg_display = agg_display.rename(columns={"page_views": "concurrents", "uniques": "concurrents_unique"})

    st.subheader("Category Summary (Live Concurrents)")
    st.dataframe(agg_display, use_container_width=True)

    detail_display = filtered_df[["referrer", "category", "page_views", "uniques"]].copy()
    detail_display = detail_display.rename(columns={"page_views": "concurrents", "uniques": "concurrents_unique"})

    st.subheader("Referrer Details")
    st.dataframe(
        detail_display.sort_values("concurrents", ascending=False),
        use_container_width=True,
    )

    st.download_button(
        label="Download Referrer Summary CSV",
        data=to_csv_bytes(filtered_df),
        file_name="referrer_summary.csv",
        mime="text/csv",
    )

    # Bar charts
    st.subheader("Concurrents by Category")
    st.bar_chart(agg_display.set_index("category")["concurrents"])

    # URL-level drill-down
    st.subheader("URL-Level Drill-Down")
    referrer_list = sorted(filtered_df["referrer"].unique().tolist())
    selected_referrer = st.selectbox("Select a Referrer", options=referrer_list)

    if selected_referrer:
        with st.spinner(f"Fetching URL data for {selected_referrer}..."):
            try:
                client = ChartbeatClient(
                    api_key=st.session_state["api_key"],
                    host=st.session_state["property_domain"],
                )
                url_data = client.get_urls_for_referrer(selected_referrer)
                if not url_data:
                    st.info("No URL-level data available for this referrer")
                else:
                    url_df = pd.DataFrame(url_data)
                    url_df = add_section_column(url_df)
                    url_display = url_df[["url", "page_views", "uniques", "engaged_minutes", "section"]].copy()
                    url_display = url_display.rename(columns={
                        "page_views": "visitors",
                        "uniques": "visitors_unique",
                        "engaged_minutes": "avg_engaged_min",
                    })
                    st.dataframe(url_display, use_container_width=True)
                    st.download_button(
                        label="Download URL Data CSV",
                        data=to_csv_bytes(url_df),
                        file_name="url_level_data.csv",
                        mime="text/csv",
                    )
                    st.session_state["url_df"] = url_df
            except ChartbeatAPIError as e:
                st.error(e.message)

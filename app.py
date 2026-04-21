"""Streamlit entry point for the Chartbeat Referrer Dashboard."""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from api_client import ChartbeatClient, ChartbeatAPIError
from categorizer import categorize_dataframe
from transforms import aggregate_by_category, add_section_column
from export import to_csv_bytes


def validate_inputs(api_key: str, property_domain: str, start_date, end_date) -> tuple[bool, str]:
    """Validate configuration inputs.

    Returns (True, '') if valid, (False, error_message) if invalid.
    """
    if not api_key or not api_key.strip():
        return False, "API Key is required"
    if not property_domain or not property_domain.strip():
        return False, "Property (domain) is required"
    if start_date >= end_date:
        return False, "Start date must be before end date"
    return True, ""


@st.cache_data
def fetch_referrer_data(api_key: str, host: str, start: str, end: str):
    """Fetch and process referrer data. Cached by Streamlit."""
    client = ChartbeatClient(api_key=api_key, host=host)
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    raw_data = client.get_referrers(start_dt, end_dt)
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

# Sidebar configuration panel
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Chartbeat API Key", type="password", key="api_key")
    property_domain = st.text_input("Property (domain)", key="property_domain")
    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=7), key="start_date")
    end_date = st.date_input("End Date", value=date.today(), key="end_date")
    submit = st.button("Fetch Data")

if submit:
    is_valid, error_msg = validate_inputs(api_key, property_domain, start_date, end_date)
    if not is_valid:
        st.error(error_msg)
    else:
        with st.spinner("Fetching data from Chartbeat..."):
            try:
                df, agg_df = fetch_referrer_data(
                    api_key, property_domain,
                    str(start_date), str(end_date)
                )
                if df.empty:
                    st.warning("No referrer data found for this date range")
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

    st.subheader("Category Summary")
    st.dataframe(filtered_agg, use_container_width=True)

    st.subheader("Referrer Details")
    st.dataframe(
        filtered_df.sort_values("page_views", ascending=False),
        use_container_width=True,
    )

    st.download_button(
        label="Download Referrer Summary CSV",
        data=to_csv_bytes(filtered_df),
        file_name="referrer_summary.csv",
        mime="text/csv",
    )

    # Bar charts
    st.subheader("Page Views by Category")
    st.bar_chart(filtered_agg.set_index("category")["page_views"])

    st.subheader("Uniques by Category")
    st.bar_chart(filtered_agg.set_index("category")["uniques"])

    # URL-level drill-down
    st.subheader("URL-Level Drill-Down")
    referrer_list = sorted(filtered_df["referrer"].unique().tolist())
    selected_referrer = st.selectbox("Select a Referrer", options=referrer_list)

    if selected_referrer:
        with st.spinner(f"Fetching URL data for {selected_referrer}..."):
            try:
                client = ChartbeatClient(api_key=st.session_state["api_key"], host=st.session_state["property_domain"])
                url_data = client.get_urls_for_referrer(
                    selected_referrer,
                    datetime.fromisoformat(str(st.session_state["start_date"])),
                    datetime.fromisoformat(str(st.session_state["end_date"])),
                )
                if not url_data:
                    st.info("No URL-level data available for this referrer")
                else:
                    url_df = pd.DataFrame(url_data)
                    url_df = add_section_column(url_df)
                    display_columns = ["url", "page_views", "uniques", "engaged_minutes", "section"]
                    # Only show columns that exist in the data
                    display_columns = [c for c in display_columns if c in url_df.columns]
                    st.dataframe(url_df[display_columns], use_container_width=True)
                    st.download_button(
                        label="Download URL Data CSV",
                        data=to_csv_bytes(url_df),
                        file_name="url_level_data.csv",
                        mime="text/csv",
                    )
                    st.session_state["url_df"] = url_df
            except ChartbeatAPIError as e:
                st.error(e.message)

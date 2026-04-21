"""Streamlit entry point for the Chartbeat Referrer Dashboard.

Uses the Chartbeat Real-Time API to show live referrer data
with section breakdown, referrer categorization, drill-down, and CSV export.
"""

import streamlit as st
import pandas as pd

from api_client import ChartbeatClient, ChartbeatAPIError
from categorizer import categorize_dataframe
from transforms import aggregate_by_category, add_section_column
from export import to_csv_bytes

# Available domains
DOMAINS = [
    "tv9telugu.com",
    "tv9marathi.com",
    "tv9kannada.com",
    "tv9bangla.com",
    "tv9hindi.com",
    "malayalamtv9.com",
    "news9live.com",
    "money9live.com",
    "tv9gujarati.com",
    "tv9tamilnews.com",
    "tv9up.com"
]


def get_api_key() -> str:
    """Get API key from Streamlit secrets or session state."""
    try:
        return st.secrets["CHARTBEAT_API_KEY"]
    except (KeyError, FileNotFoundError):
        return st.session_state.get("api_key", "")


def validate_inputs(api_key: str, property_domain: str) -> tuple[bool, str]:
    """Validate configuration inputs."""
    if not api_key or not api_key.strip():
        return False, "API Key is required"
    if not property_domain or not property_domain.strip():
        return False, "Property (domain) is required"
    return True, ""


def make_clickable(url: str) -> str:
    """Make a URL clickable in Streamlit dataframe."""
    if not url.startswith("http"):
        url = f"https://{url}"
    return f'<a href="{url}" target="_blank">{url}</a>'


def fetch_all_data(api_key: str, host: str):
    """Fetch referrer data and top pages data."""
    client = ChartbeatClient(api_key=api_key, host=host)

    raw_referrers = client.get_referrers()
    ref_df = pd.DataFrame()
    agg_df = pd.DataFrame()
    if raw_referrers:
        ref_df = pd.DataFrame(raw_referrers)
        if "referrer" in ref_df.columns:
            ref_df = categorize_dataframe(ref_df)
            agg_df = aggregate_by_category(ref_df)

    raw_pages = client.get_toppages(limit=500)
    pages_df = pd.DataFrame()
    if raw_pages:
        pages_df = pd.DataFrame(raw_pages)
        pages_df = add_section_column(pages_df)

    return ref_df, agg_df, pages_df


st.set_page_config(page_title="Chartbeat Referrer Dashboard", layout="wide")
st.title("Chartbeat Referrer Dashboard")
st.caption("Live data from the Chartbeat Real-Time API")

# Check if API key is in secrets
has_secret_key = False
try:
    secret_key = st.secrets["CHARTBEAT_API_KEY"]
    has_secret_key = bool(secret_key)
except (KeyError, FileNotFoundError):
    pass

with st.sidebar:
    st.header("Configuration")
    if has_secret_key:
        st.success("API Key loaded from secrets")
        api_key = secret_key
    else:
        api_key = st.text_input("Chartbeat API Key", type="password", key="api_key")

    property_domain = st.selectbox(
        "Property (domain)",
        options=DOMAINS,
        key="property_domain",
    )
    submit = st.button("Fetch Live Data")

if submit:
    is_valid, error_msg = validate_inputs(api_key, property_domain)
    if not is_valid:
        st.error(error_msg)
    else:
        with st.spinner("Fetching live data from Chartbeat..."):
            try:
                ref_df, agg_df, pages_df = fetch_all_data(api_key, property_domain)
                if ref_df.empty and pages_df.empty:
                    st.warning("No data found")
                else:
                    st.session_state["referrer_df"] = ref_df
                    st.session_state["agg_df"] = agg_df
                    st.session_state["pages_df"] = pages_df
                    st.session_state["active_api_key"] = api_key
                    st.session_state["active_domain"] = property_domain
            except ChartbeatAPIError as e:
                st.error(e.message)

# --- Total Concurrents ---
if "pages_df" in st.session_state and not st.session_state["pages_df"].empty:
    pages_df = st.session_state["pages_df"]
    total = int(pages_df["page_views"].sum())
    st.metric("Total Concurrents", f"{total:,}")

# --- Section Breakdown ---
if "pages_df" in st.session_state and not st.session_state["pages_df"].empty:
    pages_df = st.session_state["pages_df"]

    st.subheader("Concurrents by Section")
    section_agg = (
        pages_df[pages_df["section"] != ""]
        .groupby("section", as_index=False)
        .agg(
            concurrents=("page_views", "sum"),
            pages=("url", "count"),
            avg_engaged_sec=("avg_engaged_sec", "mean"),
            from_search=("search", "sum"),
            from_social=("social", "sum"),
            from_direct=("direct", "sum"),
            from_internal=("internal", "sum"),
            from_links=("links", "sum"),
            new_visitors=("new_visitors", "sum"),
        )
        .sort_values("concurrents", ascending=False)
    )
    section_agg["avg_engaged_sec"] = section_agg["avg_engaged_sec"].round(1)

    import altair as alt

    section_chart = alt.Chart(section_agg).mark_bar().encode(
        x=alt.X("section", sort="-y", title="Section"),
        y=alt.Y("concurrents", title="Concurrents"),
        tooltip=["section", "concurrents", "pages"],
    ).properties(height=400)
    st.altair_chart(section_chart, use_container_width=True)
    st.dataframe(section_agg, use_container_width=True)

    st.download_button(
        label="Download Section Summary CSV",
        data=to_csv_bytes(section_agg),
        file_name="section_summary.csv",
        mime="text/csv",
    )

# --- Referrer Category Breakdown ---
if "referrer_df" in st.session_state and not st.session_state["referrer_df"].empty:
    ref_df = st.session_state["referrer_df"]
    agg_df = st.session_state["agg_df"]

    st.subheader("Concurrents by Referrer Category")

    all_categories = sorted(ref_df["category"].unique().tolist())
    selected_categories = st.multiselect(
        "Filter by Referrer Category",
        options=all_categories,
        default=all_categories,
    )

    filtered_df = ref_df[ref_df["category"].isin(selected_categories)]
    filtered_agg = agg_df[agg_df["category"].isin(selected_categories)]

    cat_display = filtered_agg[["category", "page_views"]].copy()
    cat_display = cat_display.rename(columns={"page_views": "concurrents"})

    cat_chart = alt.Chart(cat_display).mark_bar().encode(
        x=alt.X("category", sort="-y", title="Category"),
        y=alt.Y("concurrents", title="Concurrents"),
        tooltip=["category", "concurrents"],
    ).properties(height=400)
    st.altair_chart(cat_chart, use_container_width=True)

    st.subheader("Referrer Details")
    detail = filtered_df[["referrer", "category", "page_views"]].copy()
    detail = detail.rename(columns={"page_views": "concurrents"})
    st.dataframe(detail.sort_values("concurrents", ascending=False), use_container_width=True)

    st.download_button(
        label="Download Referrer Summary CSV",
        data=to_csv_bytes(detail),
        file_name="referrer_summary.csv",
        mime="text/csv",
    )

    # --- URL-level drill-down with clickable URLs ---
    st.subheader("URL-Level Drill-Down")
    referrer_list = sorted(filtered_df["referrer"].unique().tolist())
    selected_referrer = st.selectbox("Select a Referrer", options=referrer_list)

    if selected_referrer:
        with st.spinner(f"Fetching URL data for {selected_referrer}..."):
            try:
                client = ChartbeatClient(
                    api_key=st.session_state.get("active_api_key", api_key),
                    host=st.session_state.get("active_domain", property_domain),
                )
                url_data = client.get_urls_for_referrer(selected_referrer)
                if not url_data:
                    st.info("No URL-level data available for this referrer")
                else:
                    url_df = pd.DataFrame(url_data)
                    url_df = add_section_column(url_df)

                    # Section filter
                    all_sections = sorted(url_df["section"].unique().tolist())
                    all_sections = [s for s in all_sections if s]  # remove empty
                    selected_sections = st.multiselect(
                        "Filter by Section",
                        options=all_sections,
                        default=all_sections,
                        key="url_section_filter",
                    )
                    filtered_urls = url_df[url_df["section"].isin(selected_sections)]

                    if filtered_urls.empty:
                        st.info("No URLs match the selected sections")
                    else:
                        url_display = filtered_urls[["url", "page_views", "avg_engaged_sec", "section"]].copy()
                        url_display = url_display.rename(columns={"page_views": "visitors"})

                        # Make URLs clickable
                        url_display["url"] = url_display["url"].apply(make_clickable)
                        st.write(
                            url_display.to_html(escape=False, index=False),
                            unsafe_allow_html=True,
                        )

                        # CSV export uses raw data (not HTML links)
                        csv_df = filtered_urls[["url", "page_views", "avg_engaged_sec", "section"]].copy()
                        csv_df = csv_df.rename(columns={"page_views": "visitors"})
                        st.download_button(
                            label="Download URL Data CSV",
                            data=to_csv_bytes(csv_df),
                            file_name="url_level_data.csv",
                            mime="text/csv",
                        )
            except ChartbeatAPIError as e:
                st.error(e.message)

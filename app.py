"""Streamlit entry point for the Chartbeat Referrer Dashboard.

Uses the Chartbeat Real-Time API to show live referrer data
with section breakdown, referrer categorization, drill-down, and CSV export.
"""

import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

from api_client import ChartbeatClient, ChartbeatAPIError
from categorizer import categorize_dataframe
from transforms import aggregate_by_category, add_section_column
from export import to_csv_bytes

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
    "tv9up.com",
]


STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "with", "by", "from", "as", "it", "its",
    "this", "that", "be", "has", "have", "had", "do", "does", "did", "will",
    "can", "could", "would", "should", "may", "might", "shall", "no", "yes",
    "he", "she", "they", "we", "you", "i", "me", "my", "his", "her", "our",
    "your", "their", "what", "which", "who", "whom", "how", "when", "where",
    "why", "all", "each", "every", "both", "few", "more", "most", "other",
    "some", "such", "than", "too", "very", "just", "about", "above", "after",
    "again", "also", "am", "an", "any", "because", "been", "before", "being",
    "between", "during", "here", "there", "into", "over", "under", "up", "down",
    "out", "off", "then", "once", "only", "own", "same", "so", "if", "while",
    "|", "-", "–", "—", ":", "news", "latest", "live", "updates", "breaking",
}


def extract_keywords(title: str) -> str:
    """Extract meaningful keywords from article title."""
    if not title:
        return ""
    words = title.lower().replace(",", " ").replace(".", " ").split()
    keywords = [w.strip() for w in words if len(w) > 2 and w.lower() not in STOP_WORDS]
    return ", ".join(keywords[:5])


def validate_inputs(api_key: str, property_domain: str) -> tuple[bool, str]:
    if not api_key or not api_key.strip():
        return False, "API Key is required"
    if not property_domain or not property_domain.strip():
        return False, "Property (domain) is required"
    return True, ""


def make_clickable(url: str) -> str:
    if not url.startswith("http"):
        url = f"https://{url}"
    return f'<a href="{url}" target="_blank">{url}</a>'


def fetch_all_data(api_key: str, host: str):
    client = ChartbeatClient(api_key=api_key, host=host)
    raw_referrers = client.get_referrers()
    ref_df, agg_df = pd.DataFrame(), pd.DataFrame()
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


st.set_page_config(page_title="Chartbeat Realtime Dashboard", layout="wide")
st.title("Chartbeat Realtime Dashboard")

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
    property_domain = st.selectbox("Property (domain)", options=DOMAINS, key="property_domain")
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
                    st.session_state["last_updated"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
            except ChartbeatAPIError as e:
                st.error(e.message)

# --- Header: Total Concurrents + Last Updated ---
has_data = "pages_df" in st.session_state and not st.session_state["pages_df"].empty
has_ref = "referrer_df" in st.session_state and not st.session_state["referrer_df"].empty

if has_data:
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        total = int(st.session_state["pages_df"]["page_views"].sum())
        st.metric("Total Concurrents", f"{total:,}")
    with col2:
        domain = st.session_state.get("active_domain", "")
        st.metric("Property", domain)
    with col3:
        ts = st.session_state.get("last_updated", "")
        st.metric("Last Updated", ts)

# --- Tabs ---
if has_data or has_ref:
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Concurrents by Section",
        "🔗 Concurrents by Source",
        "🔥 Trending URLs",
        "🔍 URL Breakdown",
        "👥 New vs Returning",
        "🗺️ Engagement Heatmap",
        "⚡ Traffic Alerts",
    ])

    # ===== TAB 1: Concurrents by Section =====
    with tab1:
        if has_data:
            pages_df = st.session_state["pages_df"]
            section_agg = (
                pages_df[pages_df["section"] != ""]
                .groupby("section", as_index=False)
                .agg(
                    concurrents=("page_views", "sum"),
                    pages=("url", "count"),
                    avg_engaged_sec=("avg_engaged_sec", "mean"),
                    from_search=("search", "sum"),
                    from_social=("social", "sum"),
                    from_internal=("internal", "sum"),
                    from_links=("links", "sum"),
                    new_visitors=("new_visitors", "sum"),
                )
                .sort_values("concurrents", ascending=False)
            )
            section_agg["avg_engaged_sec"] = section_agg["avg_engaged_sec"].round(1)

            chart = alt.Chart(section_agg).mark_bar().encode(
                x=alt.X("section", sort="-y", title="Section"),
                y=alt.Y("concurrents", title="Concurrents"),
                tooltip=["section", "concurrents", "pages"],
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

            st.dataframe(
                section_agg.style.apply(
                    lambda row: ["background-color: #d4edda" if row["avg_engaged_sec"] > 30 else "" for _ in row],
                    axis=1,
                ).format({"avg_engaged_sec": "{:.1f}"}),
                use_container_width=True,
            )
            st.download_button("Download Section Summary CSV", to_csv_bytes(section_agg), "section_summary.csv", "text/csv", key="dl_section")

    # ===== TAB 2: Concurrents by Source =====
    with tab2:
        if has_ref:
            ref_df = st.session_state["referrer_df"]
            agg_df = st.session_state["agg_df"]

            all_categories = sorted(ref_df["category"].unique().tolist())
            selected_categories = st.multiselect("Filter by Referrer Category", options=all_categories, default=all_categories, key="cat_filter")

            filtered_df = ref_df[ref_df["category"].isin(selected_categories)]
            filtered_agg = agg_df[agg_df["category"].isin(selected_categories)]

            cat_display = filtered_agg[["category", "page_views"]].rename(columns={"page_views": "concurrents"})

            chart = alt.Chart(cat_display).mark_bar().encode(
                x=alt.X("category", sort="-y", title="Category"),
                y=alt.Y("concurrents", title="Concurrents"),
                tooltip=["category", "concurrents"],
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

            detail = filtered_df[["referrer", "category", "page_views"]].rename(columns={"page_views": "concurrents"})
            st.dataframe(detail.sort_values("concurrents", ascending=False), use_container_width=True)
            st.download_button("Download Referrer Summary CSV", to_csv_bytes(detail), "referrer_summary.csv", "text/csv", key="dl_ref")

    # ===== TAB 3: Trending URLs =====
    with tab3:
        if has_data:
            pages_df = st.session_state["pages_df"]
            source_sel = st.selectbox(
                "Select Traffic Source",
                options=["Search", "Social", "Discovery (Google Discover/News)", "Direct", "Links"],
                key="trending_source",
            )
            source_col_map = {"Search": "search", "Social": "social", "Discovery (Google Discover/News)": "search", "Direct": "direct", "Links": "links"}
            col = source_col_map[source_sel]

            trending = pages_df[pages_df[col] > 0][["title", "url", "section", col, "page_views", "avg_engaged_sec"]].copy()
            trending = trending.rename(columns={col: "from_source", "page_views": "total_concurrents"})
            trending = trending.sort_values("from_source", ascending=False).head(20)

            if trending.empty:
                st.info(f"No pages with {source_sel} traffic right now")
            else:
                t = trending.copy()
                t["keywords"] = t["title"].apply(extract_keywords)
                t["url"] = t["url"].apply(make_clickable)
                st.write(t.to_html(escape=False, index=False), unsafe_allow_html=True)

    # ===== TAB 4: URL Breakdown =====
    with tab4:
        if has_ref:
            ref_df = st.session_state["referrer_df"]
            filtered_df = ref_df[ref_df["category"].isin(ref_df["category"].unique())]
            referrer_list = sorted(filtered_df["referrer"].unique().tolist())
            selected_referrer = st.selectbox("Select a Referrer", options=referrer_list, key="url_referrer")

            if selected_referrer:
                with st.spinner(f"Fetching URL data for {selected_referrer}..."):
                    try:
                        client = ChartbeatClient(
                            api_key=st.session_state.get("active_api_key", ""),
                            host=st.session_state.get("active_domain", ""),
                        )
                        url_data = client.get_urls_for_referrer(selected_referrer)
                        if not url_data:
                            st.info("No URL-level data available for this referrer")
                        else:
                            url_df = pd.DataFrame(url_data)
                            url_df = add_section_column(url_df)

                            all_sections = sorted([s for s in url_df["section"].unique() if s])
                            selected_sections = st.multiselect("Filter by Section", options=all_sections, default=all_sections, key="url_section_filter")
                            filtered_urls = url_df[url_df["section"].isin(selected_sections)]

                            if filtered_urls.empty:
                                st.info("No URLs match the selected sections")
                            else:
                                url_display = filtered_urls[["url", "page_views", "avg_engaged_sec", "section"]].rename(columns={"page_views": "visitors"})
                                url_display_html = url_display.copy()
                                url_display_html["url"] = url_display_html["url"].apply(make_clickable)
                                st.write(url_display_html.to_html(escape=False, index=False), unsafe_allow_html=True)

                                csv_df = filtered_urls[["url", "page_views", "avg_engaged_sec", "section"]].rename(columns={"page_views": "visitors"})
                                st.download_button("Download URL Data CSV", to_csv_bytes(csv_df), "url_level_data.csv", "text/csv", key="dl_url")
                    except ChartbeatAPIError as e:
                        st.error(e.message)

    # ===== TAB 5: New vs Returning =====
    with tab5:
        if has_data:
            pages_df = st.session_state["pages_df"]
            total_visitors = int(pages_df["page_views"].sum())
            total_new = int(pages_df["new_visitors"].sum())
            total_returning = total_visitors - total_new

            # Overall pie chart
            pie_data = pd.DataFrame({
                "type": ["New Visitors", "Returning Visitors"],
                "count": [total_new, total_returning],
            })
            pie = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color("type:N", scale=alt.Scale(range=["#4CAF50", "#2196F3"])),
                tooltip=["type", "count"],
            ).properties(height=300, title="Overall New vs Returning")
            st.altair_chart(pie, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Visitors", f"{total_visitors:,}")
            c2.metric("New Visitors", f"{total_new:,}", f"{round(total_new/max(total_visitors,1)*100)}%")
            c3.metric("Returning", f"{total_returning:,}", f"{round(total_returning/max(total_visitors,1)*100)}%")

            # Per-section breakdown
            st.subheader("New Visitor Rate by Section")
            section_visitors = (
                pages_df[pages_df["section"] != ""]
                .groupby("section", as_index=False)
                .agg(concurrents=("page_views", "sum"), new_visitors=("new_visitors", "sum"))
            )
            section_visitors["new_pct"] = (section_visitors["new_visitors"] / section_visitors["concurrents"].replace(0, 1) * 100).round(1)
            section_visitors = section_visitors.sort_values("new_pct", ascending=False)

            bar = alt.Chart(section_visitors).mark_bar().encode(
                x=alt.X("section", sort="-y", title="Section"),
                y=alt.Y("new_pct", title="New Visitor %"),
                color=alt.condition(alt.datum.new_pct > 30, alt.value("#4CAF50"), alt.value("#90CAF9")),
                tooltip=["section", "concurrents", "new_visitors", "new_pct"],
            ).properties(height=400)
            st.altair_chart(bar, use_container_width=True)
            st.caption("Green bars = sections with >30% new visitors (strong SEO/discovery content)")
            st.dataframe(section_visitors, use_container_width=True)

    # ===== TAB 6: Engagement Heatmap =====
    with tab6:
        if has_data:
            pages_df = st.session_state["pages_df"]
            sections = pages_df[pages_df["section"] != ""]

            # Build section × source matrix
            sources = ["search", "social", "internal", "links"]
            rows = []
            for section, group in sections.groupby("section"):
                total_conc = group["page_views"].sum()
                if total_conc == 0:
                    continue
                avg_eng = group["avg_engaged_sec"].mean()
                for src in sources:
                    src_conc = group[src].sum()
                    if src_conc > 0:
                        # Weighted avg engaged time for pages with this source
                        src_pages = group[group[src] > 0]
                        src_avg_eng = src_pages["avg_engaged_sec"].mean() if not src_pages.empty else 0
                        rows.append({
                            "section": section,
                            "source": src.capitalize(),
                            "concurrents": int(src_conc),
                            "avg_engaged_sec": round(src_avg_eng, 1),
                        })

            if rows:
                heatmap_df = pd.DataFrame(rows)
                heatmap_df = heatmap_df[heatmap_df["concurrents"] >= 10]
                heat = alt.Chart(heatmap_df).mark_rect().encode(
                    x=alt.X("source:N", title="Traffic Source"),
                    y=alt.Y("section:N", title="Section", sort="-x"),
                    color=alt.Color("avg_engaged_sec:Q", scale=alt.Scale(scheme="yellowgreenblue"), title="Avg Engaged (sec)"),
                    tooltip=["section", "source", "concurrents", "avg_engaged_sec"],
                ).properties(height=max(len(heatmap_df["section"].unique()) * 25, 300), title="Engagement Heatmap: Section × Traffic Source")
                st.altair_chart(heat, use_container_width=True)
                st.caption("Darker = higher engagement. Hover for details.")

                # Top engagement combos
                st.subheader("Top Engagement Combinations")
                top = heatmap_df[heatmap_df["concurrents"] >= 10].sort_values("avg_engaged_sec", ascending=False).head(10)
                st.dataframe(top, use_container_width=True)
            else:
                st.info("Not enough data for heatmap")

    # ===== TAB 7: Traffic Alerts =====
    with tab7:
        if has_data:
            pages_df = st.session_state["pages_df"]
            current_sections = (
                pages_df[pages_df["section"] != ""]
                .groupby("section", as_index=False)
                .agg(concurrents=("page_views", "sum"))
                .sort_values("concurrents", ascending=False)
            )

            # Store history for comparison
            prev_key = "prev_sections"
            if prev_key in st.session_state:
                prev = st.session_state[prev_key]
                merged = current_sections.merge(prev, on="section", how="outer", suffixes=("_now", "_prev")).fillna(0)
                merged["change"] = merged["concurrents_now"] - merged["concurrents_prev"]
                merged["change_pct"] = ((merged["change"] / merged["concurrents_prev"].replace(0, 1)) * 100).round(1)

                # Spikes (>50% increase)
                spikes = merged[merged["change_pct"] > 50].sort_values("change_pct", ascending=False)
                # Drops (>30% decrease)
                drops = merged[merged["change_pct"] < -30].sort_values("change_pct")

                if not spikes.empty:
                    st.subheader("🚀 Traffic Spikes")
                    st.caption("Sections with >50% increase since last fetch")
                    spike_display = spikes[["section", "concurrents_now", "concurrents_prev", "change", "change_pct"]].copy()
                    spike_display.columns = ["Section", "Now", "Previous", "Change", "Change %"]
                    st.dataframe(
                        spike_display.style.map(lambda v: "color: green; font-weight: bold" if isinstance(v, (int, float)) and v > 0 else "", subset=["Change", "Change %"]),
                        use_container_width=True,
                    )

                if not drops.empty:
                    st.subheader("📉 Traffic Drops")
                    st.caption("Sections with >30% decrease since last fetch")
                    drop_display = drops[["section", "concurrents_now", "concurrents_prev", "change", "change_pct"]].copy()
                    drop_display.columns = ["Section", "Now", "Previous", "Change", "Change %"]
                    st.dataframe(
                        drop_display.style.map(lambda v: "color: red; font-weight: bold" if isinstance(v, (int, float)) and v < 0 else "", subset=["Change", "Change %"]),
                        use_container_width=True,
                    )

                if spikes.empty and drops.empty:
                    st.success("No significant traffic changes detected")

                # Full comparison table
                st.subheader("Full Section Comparison")
                full = merged[["section", "concurrents_now", "concurrents_prev", "change", "change_pct"]].copy()
                full.columns = ["Section", "Now", "Previous", "Change", "Change %"]
                st.dataframe(full.sort_values("Now", ascending=False), use_container_width=True)
            else:
                st.info("Fetch data twice to see traffic changes. The first fetch establishes a baseline.")

            # Save current as previous for next comparison
            st.session_state[prev_key] = current_sections.copy()

# Chartbeat Realtime Dashboard

A Streamlit dashboard that connects to the Chartbeat Real-Time API to analyze live referrer performance across multiple properties. Features tabbed views for section breakdown, traffic source analysis, trending content, engagement heatmaps, and traffic alerts.

## Live Demo

Deployed on Streamlit Cloud: [chartbeat.streamlit.app](https://chartbeat.streamlit.app)

## Features

### 📊 Concurrents by Section
- Bar chart and table showing live concurrent visitors per URL section (e.g., /india, /business, /sports)
- Traffic source breakdown per section (search, social, internal, links)
- Rows with >30s avg engagement highlighted in green

### 🔗 Concurrents by Source
- Referrer categorization into Search, Social, Discovery, AMP, AI, Direct/Other
- Per-referrer concurrent visitor counts with category filter

### 🔥 Trending URLs
- Top 20 pages by traffic source with clickable URLs
- Auto-extracted keywords from article titles for quick topic identification

### 🔍 URL Breakdown
- Per-referrer URL drill-down with section filter
- Clickable URLs and engagement time per page

### 👥 New vs Returning
- Donut chart showing overall new vs returning visitor split
- Per-section new visitor rate — highlights sections with >30% new visitors (strong SEO/discovery content)

### 🗺️ Engagement Heatmap
- Section × traffic source heatmap colored by avg engaged time
- Top engagement combinations (filtered to 10+ concurrents)

### ⚡ Traffic Alerts
- Compares current fetch with previous fetch
- Flags sections with >50% traffic spike or >30% drop
- Full section comparison table with change percentages

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## API Key Configuration

Option 1: Enter in the sidebar (shown when no secret is configured)

Option 2: Store in Streamlit secrets (recommended):
- Local: create `.streamlit/secrets.toml`:
  ```toml
  CHARTBEAT_API_KEY = "your-key-here"
  ```
- Streamlit Cloud: Settings → Secrets → add the same line

The secrets file is gitignored.

## Supported Properties

tv9telugu.com, tv9marathi.com, tv9kannada.com, tv9bangla.com, tv9hindi.com, malayalamtv9.com, news9live.com, money9live.com, tv9gujarati.com, tv9tamilnews.com, tv9up.com

## Project Structure

```
├── app.py              # Streamlit entry point (tabbed dashboard)
├── api_client.py       # Chartbeat Real-Time API wrapper
├── categorizer.py      # Referrer categorization engine
├── transforms.py       # Data aggregation and section extraction
├── export.py           # CSV export helpers
├── requirements.txt    # Python dependencies
└── tests/              # 63 tests (unit, property-based, integration)
```

## Tests

```bash
pytest tests/ -v
```

## API Access

Uses the Chartbeat Real-Time API (`/live/referrers/v3/` and `/live/toppages/v3/`). Requires an API key with "all" access.

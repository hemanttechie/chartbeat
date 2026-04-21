# Chartbeat Referrer Dashboard

A Streamlit dashboard that connects to the Chartbeat Real-Time API to analyze live referrer performance for your property (domain). View referrer data categorized by traffic source, drill down into URL-level data, and export results as CSV.

## Features

- **Referrer Categorization** — Automatically groups referrers into Search, Social, Discovery, AMP, AI, and Direct/Other
- **Category Summary** — Aggregated concurrent visitor counts per category with bar charts
- **Referrer Details** — Per-referrer breakdown sortable by concurrent visitors
- **Category Filtering** — Filter data by one or more referrer categories
- **URL-Level Drill-Down** — Select a referrer to see which pages are getting traffic from it
- **CSV Export** — Download referrer summary and URL-level data as CSV files

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Enter your Chartbeat API key (with "all" access) and property domain in the sidebar.

## Project Structure

```
├── app.py              # Streamlit entry point
├── api_client.py       # Chartbeat Real-Time API wrapper
├── categorizer.py      # Referrer categorization engine
├── transforms.py       # Data aggregation and section extraction
├── export.py           # CSV export helpers
├── requirements.txt    # Python dependencies
└── tests/              # Unit, property, and integration tests
```

## Tests

```bash
pytest tests/ -v
```

63 tests including unit tests, property-based tests (Hypothesis), and integration tests.

## Referrer Categories

| Category | Examples |
|---|---|
| Search | Google Search, Bing, DuckDuckGo, Yahoo Search, Brave Search, Ecosia |
| Social | Facebook, Instagram, Twitter, Reddit, YouTube |
| Discovery | Google Discover, Google News, JioNews |
| AMP | *.cdn.ampproject.org |
| AI | ChatGPT, Google Gemini |
| Direct/Other | Everything else |

## API Access

This app uses the Chartbeat Real-Time API (`/live/referrers/v3/` and `/live/toppages/v3/`). You need an API key with "all" access. Create one at your Chartbeat account settings under Manage API Keys.

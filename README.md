# Chartbeat Referrer Dashboard

A Streamlit dashboard that connects to the Chartbeat Historical Analytics API to analyze referrer performance for your property (domain). View aggregated traffic by category, drill down into URL-level data, and export results as CSV.

## Features

- **Referrer Categorization** — Automatically groups referrers into Search, Social, Discovery, AMP, AI, and Direct/Other
- **Aggregated View** — Summary tables and bar charts comparing page views and uniques across categories
- **Category Filtering** — Filter data by one or more referrer categories
- **URL-Level Drill-Down** — Select a referrer to see per-URL performance with section extraction
- **CSV Export** — Download referrer summary and URL-level data as CSV files

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then enter your Chartbeat API key, property domain, and date range in the sidebar.

## Project Structure

```
├── app.py              # Streamlit entry point
├── api_client.py       # Chartbeat API wrapper
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

The test suite includes unit tests, property-based tests (Hypothesis), and integration tests — 63 tests total.

## Referrer Categories

| Category | Examples |
|---|---|
| Search | Google Search, Bing, DuckDuckGo, Yahoo Search, Brave Search, Ecosia |
| Social | Facebook, Instagram, Twitter, Reddit, YouTube |
| Discovery | Google Discover, Google News, JioNews |
| AMP | *.cdn.ampproject.org |
| AI | ChatGPT, Google Gemini |
| Direct/Other | Everything else |

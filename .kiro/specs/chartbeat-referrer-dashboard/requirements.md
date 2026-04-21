# Requirements Document

## Introduction

A Streamlit-based dashboard application that connects to the Chartbeat API to analyze historical referrer performance for a given property (domain). Users configure their API credentials, select a date range, and view aggregated and URL-level referrer data broken down by categories such as Search, Social, Discovery, AMP, AI platforms, and Direct/Other.

## Glossary

- **Dashboard**: The Streamlit web application that displays referrer performance data
- **Chartbeat_API**: The Chartbeat Historical Analytics API used to retrieve referrer and page-level data
- **Property**: A domain/website registered in Chartbeat (e.g., "example.com")
- **Referrer**: The source that directed traffic to the Property (e.g., Google Search, Facebook)
- **Referrer_Category**: A logical grouping of referrers (Search, Social, Discovery, AMP, AI, Direct/Other)
- **Configuration_Panel**: The sidebar UI section where users input API key, Property, and date range
- **Metrics**: The numerical performance indicators: total_stories, total_engaged_min, avg_engaged_min, page_views, quality_page_views, uniques
- **Date_Range**: The start date and end date defining the historical period to query

## Requirements

### Requirement 1: Configuration Panel

**User Story:** As a publisher analyst, I want to configure my Chartbeat API credentials and query parameters, so that I can connect to my account and retrieve data for a specific property and time period.

#### Acceptance Criteria

1. THE Dashboard SHALL display a Configuration_Panel with input fields for Chartbeat API Key, Property (domain), Start Date, and End Date
2. WHEN the user submits the Configuration_Panel, THE Dashboard SHALL validate that all fields are non-empty and that Start Date is before End Date
3. IF the API Key or Property is invalid, THEN THE Dashboard SHALL display a descriptive error message indicating the authentication or property lookup failure
4. THE Dashboard SHALL persist the Configuration_Panel values within the user session so they are not lost on page interaction

### Requirement 2: Referrer Data Retrieval

**User Story:** As a publisher analyst, I want to pull historical referrer performance data from Chartbeat, so that I can analyze traffic sources over a defined period.

#### Acceptance Criteria

1. WHEN the user submits a valid configuration, THE Dashboard SHALL query the Chartbeat_API for referrer performance data within the specified Date_Range
2. THE Dashboard SHALL retrieve the following Metrics for each Referrer: total_stories, total_engaged_min, avg_engaged_min, page_views, quality_page_views, and uniques
3. IF the Chartbeat_API returns an error or empty response, THEN THE Dashboard SHALL display a user-friendly error message with the failure reason
4. WHILE data is being fetched from the Chartbeat_API, THE Dashboard SHALL display a loading indicator to inform the user that processing is in progress

### Requirement 3: Referrer Categorization

**User Story:** As a publisher analyst, I want referrers automatically grouped into categories, so that I can quickly compare performance across traffic source types.

#### Acceptance Criteria

1. THE Dashboard SHALL classify each Referrer into one of the following Referrer_Categories: Search, Social, Discovery, AMP, AI, or Direct/Other
2. THE Dashboard SHALL classify Google Search, Bing, Yahoo Search, DuckDuckGo, Brave Search, Ecosia, and Petal Search as "Search"
3. THE Dashboard SHALL classify Facebook, Instagram, Twitter, Reddit, and YouTube as "Social"
4. THE Dashboard SHALL classify Google Discover, Google News, and JioNews as "Discovery"
5. THE Dashboard SHALL classify referrers matching the pattern "*.cdn.ampproject.org" as "AMP"
6. THE Dashboard SHALL classify ChatGPT and Google Gemini as "AI"
7. WHEN a Referrer does not match any defined category rule, THE Dashboard SHALL classify it as "Direct/Other"

### Requirement 4: Aggregated Performance View

**User Story:** As a publisher analyst, I want to see aggregated referrer performance by category and individual referrer, so that I can identify top-performing traffic sources.

#### Acceptance Criteria

1. WHEN referrer data is loaded, THE Dashboard SHALL display a summary table showing aggregated Metrics per Referrer_Category
2. WHEN referrer data is loaded, THE Dashboard SHALL display a detailed table showing Metrics for each individual Referrer, sortable by any Metric column
3. THE Dashboard SHALL display bar or column charts comparing page_views and uniques across Referrer_Categories
4. THE Dashboard SHALL allow the user to filter the displayed data by one or more Referrer_Categories

### Requirement 5: URL-Level Data

**User Story:** As a publisher analyst, I want to drill down into URL-level performance data per referrer, so that I can identify which specific articles perform well from each traffic source.

#### Acceptance Criteria

1. WHEN the user selects a specific Referrer, THE Dashboard SHALL query the Chartbeat_API for URL-level performance data from that Referrer within the specified Date_Range
2. THE Dashboard SHALL display URL-level results in a table including the URL, page_views, uniques, and engaged minutes
3. THE Dashboard SHALL extract the first path segment after the domain from each URL and display it in a separate "Section" column (e.g., for "malayalamtv9.com/india/article-slug.html" the Section value is "india")
4. THE Dashboard SHALL allow the user to sort URL-level results by any displayed Metric including the Section column
5. IF no URL-level data is available for the selected Referrer, THEN THE Dashboard SHALL display a message indicating no data was found

### Requirement 6: Data Export

**User Story:** As a publisher analyst, I want to export the retrieved data as a CSV file, so that I can perform further analysis in external tools.

#### Acceptance Criteria

1. WHEN referrer data is loaded, THE Dashboard SHALL provide a download button to export the referrer summary data as a CSV file
2. WHEN URL-level data is displayed, THE Dashboard SHALL provide a download button to export the URL-level data as a CSV file
3. THE Dashboard SHALL format exported CSV files with column headers matching the Metrics names (total_stories, referrer, total_engaged_min, avg_engaged_min, page_views, quality_page_views, uniques)

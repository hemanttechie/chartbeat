"""Pure-function module that maps a referrer string to a Referrer_Category."""

import re
from dataclasses import dataclass

import pandas as pd


@dataclass
class CategoryRule:
    """A single categorization rule for matching referrer strings.

    Attributes:
        category: The category label (e.g., "Search", "Social").
        match_type: One of "exact", "contains", or "pattern".
        value: The string literal or regex pattern to match against.
    """

    category: str
    match_type: str
    value: str


# Ordered list — first match wins; Direct/Other is the implicit fallback.
DEFAULT_RULES: list[CategoryRule] = [
    CategoryRule("Search", "contains", "Google Search"),
    CategoryRule("Search", "exact", "Bing"),
    CategoryRule("Search", "contains", "Yahoo Search"),
    CategoryRule("Search", "exact", "DuckDuckGo"),
    CategoryRule("Search", "exact", "Brave Search"),
    CategoryRule("Search", "exact", "Ecosia"),
    CategoryRule("Search", "exact", "Petal Search"),
    CategoryRule("Social", "exact", "Facebook"),
    CategoryRule("Social", "exact", "Instagram"),
    CategoryRule("Social", "exact", "Twitter"),
    CategoryRule("Social", "exact", "Reddit"),
    CategoryRule("Social", "exact", "YouTube"),
    CategoryRule("Discovery", "exact", "Google Discover"),
    CategoryRule("Discovery", "exact", "Google News"),
    CategoryRule("Discovery", "exact", "JioNews"),
    CategoryRule("AMP", "pattern", r".*\.cdn\.ampproject\.org"),
    CategoryRule("AI", "exact", "ChatGPT"),
    CategoryRule("AI", "exact", "Google Gemini"),
]


def categorize_referrer(
    referrer: str, rules: list[CategoryRule] = DEFAULT_RULES
) -> str:
    """Return the Referrer_Category for a given referrer string.

    Pure function. Uses ordered first-match-wins logic against the rules list.
    Falls back to 'Direct/Other' if no rule matches.

    Args:
        referrer: The referrer source string to categorize.
        rules: Ordered list of CategoryRule instances. Defaults to DEFAULT_RULES.

    Returns:
        A category string: one of "Search", "Social", "Discovery", "AMP", "AI",
        or "Direct/Other".
    """
    for rule in rules:
        if rule.match_type == "exact" and referrer == rule.value:
            return rule.category
        elif rule.match_type == "contains" and rule.value in referrer:
            return rule.category
        elif rule.match_type == "pattern" and re.fullmatch(rule.value, referrer):
            return rule.category
    return "Direct/Other"


def categorize_dataframe(
    df: pd.DataFrame, rules: list[CategoryRule] = DEFAULT_RULES
) -> pd.DataFrame:
    """Add a 'category' column to a referrer DataFrame.

    Applies categorize_referrer() to each row's 'referrer' column using the
    provided rules list.

    Args:
        df: DataFrame with a 'referrer' column.
        rules: Ordered list of CategoryRule instances. Defaults to DEFAULT_RULES.

    Returns:
        A copy of the DataFrame with an added 'category' column.
    """
    result = df.copy()
    result["category"] = result["referrer"].apply(
        lambda r: categorize_referrer(r, rules)
    )
    return result

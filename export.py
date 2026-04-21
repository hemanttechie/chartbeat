"""CSV formatting and download helpers."""

import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to UTF-8 CSV bytes for Streamlit download."""
    return df.to_csv(index=False).encode("utf-8")

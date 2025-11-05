#!/usr/bin/env python3
"""
Fetch macroeconomic time series from FRED and export to CSV for ML forecasting.

- Loads FRED_API_KEY from ./api.env (fallback to .env if not found).
- Downloads a curated set of monthly/quarterly series (see SERIES below).
- Upsamples/aligns all series to a MONTHLY, month-end index with forward-fill.
- Writes individual CSVs (one per series) and a combined 'fred_all_series.csv'.
- Optionally computes ML-friendly transformations (pct changes, log diffs, z-scores).

Usage:
  python fetch_fred.py --start 1990-01-01 --end 2025-12-31 --out ./data --with-features

Notes:
- Quarterly series (e.g., GDPC1) are carried forward within their quarter to month-end.
- You can add/remove series by editing the SERIES dict below.
"""

import os
import argparse
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd

try:
    from pandas_datareader import data as pdr
except Exception as e:
    raise SystemExit(
        "pandas-datareader is required. Install it with:\n  pip install pandas-datareader"
    )

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None  # optional, handled below


# -----------------------------
# 1) Configure the series list
# -----------------------------
# Key = human-readable name; value = dict with FRED id and frequency tag
# freq is informational; we align everything to monthly later.
SERIES: Dict[str, Dict[str, str]] = {
    # Core growth / labor
    "Real_GDP":            {"fred_id": "GDPC1",     "freq": "Q"},  # Real GDP (chained 2017 $, SAAR)
    "Unemployment_Rate":   {"fred_id": "UNRATE",    "freq": "M"},  # Civilian unemployment rate (%)
    "Nonfarm_Payrolls":    {"fred_id": "PAYEMS",    "freq": "M"},  # Total nonfarm payrolls (thous)
    # Prices / inflation
    "CPI_All_Items":       {"fred_id": "CPIAUCSL",  "freq": "M"},  # CPI (Index 1982-84=100)
    "PCE_Price_Index":     {"fred_id": "PCEPI",     "freq": "M"},  # PCE price index (Index 2012=100)
    # Activity / spending / production
    "Industrial_Production":{"fred_id": "INDPRO",   "freq": "M"},  # IP index
    "Retail_Sales":        {"fred_id": "RSAFS",     "freq": "M"},  # Retail sales (SA, mil. $)
    # Credit / money / housing
    "Revolving_Consumer_Credit": {"fred_id": "REVOLSL", "freq": "M"},  # Credit cards etc. (Bil $)
    "Housing_Starts":      {"fred_id": "HOUST",     "freq": "M"},  # Housing starts (thous, SAAR)
    # Rates / term structure
    "Fed_Funds_Rate":      {"fred_id": "FEDFUNDS",  "freq": "M"},  # Effective Fed Funds (%)
    "Treasury_10Y_Yield":  {"fred_id": "DGS10",     "freq": "D"},  # 10Y Constant Maturity (%), daily
    # Labor market tightness
    "Job_Openings_JOLTS":  {"fred_id": "JTSJOL",    "freq": "M"},  # Job openings (thous)
}

# Helpful: Some alternate/extra series you might want:
#   "Nominal_GDP": {"fred_id": "GDP", "freq": "Q"}
#   "Core_CPI": {"fred_id": "CPILFESL", "freq": "M"}
#   "ISM_Manufacturing": {"fred_id": "NAPM", "freq": "M"}


# -----------------------------
# 2) Helpers
# -----------------------------
def load_api_key() -> str:
    """Load FRED_API_KEY from api.env (preferred) or .env/environment."""
    # Try api.env first, then .env
    for env_file in ("api.env", ".env"):
        if load_dotenv and os.path.exists(env_file):
            load_dotenv(env_file)

    key = os.getenv("FRED_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "FRED_API_KEY not found. Create 'api.env' with:\n  FRED_API_KEY=your_real_key_here"
        )
    # pandas-datareader reads from env; just ensure it's set
    os.environ["FRED_API_KEY"] = key
    return key


def fetch_series(series_id: str, start: str, end: str) -> pd.Series:
    """Fetch a single series from FRED as a pandas Series with a DatetimeIndex."""
    s = pdr.DataReader(series_id, "fred", start=start, end=end).iloc[:, 0]
    s.name = series_id
    return s


def to_monthly_end(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a DataFrame with mixed daily/monthly/quarterly indexes to
    a common MONTHLY (month-end) index using forward-fill within period.
    """
    # Ensure DateTime index and sort
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    # Build a full month-end index from min..max
    m_start = df.index.min().to_period("M").to_timestamp("M")
    m_end   = df.index.max().to_period("M").to_timestamp("M")
    monthly_index = pd.date_range(m_start, m_end, freq="M")

    # Reindex to daily to preserve intermediate values, then forward-fill
    daily = df.asfreq("D")
    daily = daily.ffill()

    # Take the last observation of each month (month-end)
    out = daily.reindex(monthly_index, method="ffill")
    out.index.name = "Date"
    return out


def add_ml_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add common ML-friendly transformations:
      - pct_change_1m, pct_change_12m
      - log_diff_1m
      - zscore_24m (rolling 24-month z-score)
    """
    out = df.copy()

    # Percent changes
    out[[f"{c}__pct_change_1m" for c in df.columns]] = df.pct_change(1)
    out[[f"{c}__pct_change_12m" for c in df.columns]] = df.pct_change(12)

    # Log diffs (avoid negatives/zeros)
    safe = df.clip(lower=1e-12)
    out[[f"{c}__log_diff_1m" for c in df.columns]] = np.log(safe).diff(1)

    # Rolling z-score (24 months)
    roll = df.rolling(24, min_periods=12)
    z = (df - roll.mean()) / roll.std(ddof=0)
    out[[f"{c}__zscore_24m" for c in df.columns]] = z

    return out


def save_series_csv(s: pd.Series, out_dir: str, label: str) -> None:
    """Save a single Series to CSV as <label>.csv with two columns: Date, Value."""
    df = s.to_frame(name="Value")
    df.index.name = "Date"
    path = os.path.join(out_dir, f"{label}.csv")
    df.to_csv(path)
    print(f"  wrote {path}")


# -----------------------------
# 3) Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Fetch FRED time series to CSV.")
    parser.add_argument("--start", type=str, default="1990-01-01", help="YYYY-MM-DD")
    parser.add_argument("--end",   type=str, default=datetime.today().strftime("%Y-%m-%d"))
    parser.add_argument("--out",   type=str, default="./data", help="Output folder for CSVs")
    parser.add_argument("--with-features", action="store_true",
                        help="Also write a combined CSV with common ML features added")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    load_api_key()

    # Fetch each series to a dict of Series
    raw_series = {}
    print("Downloading from FRED...")
    for label, meta in SERIES.items():
        fred_id = meta["fred_id"]
        try:
            s = fetch_series(fred_id, args.start, args.end)
            raw_series[label] = s
        except Exception as e:
            print(f"  !! Failed {label} ({fred_id}): {e}")

    if not raw_series:
        raise SystemExit("No series fetched. Check your network and FRED_API_KEY.")

    # Save individual raw CSVs (native frequency)
    print("\nWriting individual CSVs (native frequency):")
    for label, s in raw_series.items():
        save_series_csv(s, args.out, label)

    # Combine -> monthly month-end index
    print("\nAligning to monthly (month-end) and writing combined CSV...")
    # First concat on native indexes:
    combined_native = pd.concat(raw_series, axis=1)
    combined_monthly = to_monthly_end(combined_native)

    # Write the baseline monthly combined file
    base_path = os.path.join(args.out, "fred_all_series.csv")
    combined_monthly.to_csv(base_path)
    print(f"  wrote {base_path}")

    if args.with_features:
        print("Computing ML-friendly transformations...")
        enriched = add_ml_features(combined_monthly)
        enriched_path = os.path.join(args.out, "fred_all_series_with_features.csv")
        enriched.to_csv(enriched_path)
        print(f"  wrote {enriched_path}")

    # Also write a lightweight metadata legend for reference
    legend_rows: List[dict] = []
    for label, meta in SERIES.items():
        legend_rows.append({
            "label": label,
            "fred_id": meta["fred_id"],
            "declared_freq": meta["freq"]
        })
    legend = pd.DataFrame(legend_rows)
    legend.to_csv(os.path.join(args.out, "fred_series_legend.csv"), index=False)
    print("\nDone.\n")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import sys

# --- Load environment variables FIRST ---
try:
    from dotenv import load_dotenv
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try api.env first (in script directory)
    api_env_path = os.path.join(script_dir, "api.env")
    env_path = os.path.join(script_dir, ".env")
    
    if os.path.exists(api_env_path):
        load_dotenv(api_env_path)
        print(f"✓ Loaded environment from: {api_env_path}")
    elif os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  No api.env or .env file found in: {script_dir}")
        print(f"   Looking for: {api_env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

# --- Check required environment variables ---
fred_key = os.getenv("FRED_API_KEY")
db_url = os.getenv("DATABASE_URL")

print(f"\nEnvironment check:")
print(f"  FRED_API_KEY: {'✓ Set' if fred_key else '✗ Missing'}")
print(f"  DATABASE_URL: {'✓ Set' if db_url else '✗ Missing'}")

if not db_url:
    print("\n❌ ERROR: DATABASE_URL is required but not set!")
    print("\nPlease ensure api.env file exists with:")
    print("  DATABASE_URL=postgresql://...")
    sys.exit(1)

if not fred_key:
    print("\n⚠️  WARNING: FRED_API_KEY not set. Data fetching may be rate-limited.")
    print("   Get a free key from: https://fred.stlouisfed.org/docs/api/api_key.html")
else:
    os.environ["FRED_API_KEY"] = fred_key

# --- Shim for Python 3.12+ (stdlib removed 'distutils'); pandas-datareader 0.10 still imports it
try:
    import distutils  # noqa: F401
except ModuleNotFoundError:
    import importlib
    import setuptools  # ensure present from requirements.txt
    sys.modules["distutils"] = importlib.import_module("setuptools._distutils")
# ------------------------------------------------------------------------------

from datetime import datetime
import pandas as pd
from pandas_datareader import data as pdr
from sqlalchemy import create_engine, text

# --- Import commodity data ---
try:
    from commodities_data import COMMODITY_SERIES
except ImportError:
    print("⚠️  Warning: commodities_data.py not found, using empty dict")
    COMMODITY_SERIES = {}

# --- Original macroeconomic series ---
MACRO_SERIES = {
    "Real_GDP": "GDPC1",
    "Unemployment_Rate": "UNRATE",
    "Nonfarm_Payrolls": "PAYEMS",
    "CPI_All_Items": "CPIAUCSL",
    "PCE_Price_Index": "PCEPI",
    "Industrial_Production": "INDPRO",
    "Retail_Sales": "RSAFS",
    "Revolving_Consumer_Credit": "REVOLSL",
    "Housing_Starts": "HOUST",
    "Fed_Funds_Rate": "FEDFUNDS",
    "Treasury_10Y_Yield": "DGS10",
    "Job_Openings_JOLTS": "JTSJOL",
}

def fetch_series(series_id: str, start="1990-01-01") -> pd.Series:
    s = pdr.DataReader(series_id, "fred", start=start).iloc[:, 0]
    s.name = series_id
    return s

def to_monthly(df):
    df.index = pd.to_datetime(df.index)
    m_start = df.index.min().to_period("M").to_timestamp("M")
    m_end = df.index.max().to_period("M").to_timestamp("M")
    
    # Try 'ME' first (pandas 2.2+), fallback to 'M' for older versions
    try:
        idx = pd.date_range(m_start, m_end, freq="ME")
    except ValueError:
        idx = pd.date_range(m_start, m_end, freq="M")
    
    return df.asfreq("D").ffill().reindex(idx).ffill()

def main():
    print("\n" + "="*60)
    print("FRED Data Fetcher - Macroeconomic + Commodities")
    print("="*60)
    
    engine = create_engine(db_url, pool_pre_ping=True)

    # ===== Fetch Macro Series =====
    print("\n📊 Fetching Macroeconomic Series...")
    macro_data = {}
    for label, fid in MACRO_SERIES.items():
        try:
            macro_data[label] = fetch_series(fid)
            print(f"  ✓ {label}")
        except Exception as e:
            print(f"  ✗ Error fetching {label}: {e}")

    macro_df = pd.concat(macro_data, axis=1)
    macro_df = to_monthly(macro_df)
    macro_df.reset_index(inplace=True)
    macro_df.rename(columns={"index": "date"}, inplace=True)

    # ===== Fetch Commodity Series =====
    print("\n🔨 Fetching Commodity Series...")
    commodity_data = {}
    for label, info in COMMODITY_SERIES.items():
        fid = info["fred_id"]
        try:
            commodity_data[label] = fetch_series(fid)
            print(f"  ✓ {info['label']} ({label})")
        except Exception as e:
            print(f"  ✗ Error fetching {info['label']}: {e}")

    if commodity_data:
        commodity_df = pd.concat(commodity_data, axis=1)
        commodity_df = to_monthly(commodity_df)
        commodity_df.reset_index(inplace=True)
        commodity_df.rename(columns={"index": "date"}, inplace=True)
    else:
        commodity_df = pd.DataFrame()

    # ===== Write to Database =====
    print("\n💾 Writing to database...")
    with engine.begin() as conn:
        # Create/update macro table
        macro_cols = ", ".join([f'"{c}" DOUBLE PRECISION' for c in MACRO_SERIES.keys()])
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS fred_all_series (
                date DATE PRIMARY KEY,
                {macro_cols}
            );
        """))
        conn.execute(text("TRUNCATE fred_all_series;"))
        macro_df.to_sql("fred_all_series", conn, if_exists="append", index=False)
        print("✅ Macroeconomic data written to fred_all_series")

        # Create/update commodity table
        if not commodity_df.empty:
            commodity_cols = ", ".join([f'"{c}" DOUBLE PRECISION' for c in commodity_data.keys()])
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS fred_commodities (
                    date DATE PRIMARY KEY,
                    {commodity_cols}
                );
            """))
            conn.execute(text("TRUNCATE fred_commodities;"))
            commodity_df.to_sql("fred_commodities", conn, if_exists="append", index=False)
            print("✅ Commodity data written to fred_commodities")
        else:
            print("⚠️  No commodity data to write")
    
    print("\n" + "="*60)
    print("✨ Data fetch complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

    os.environ["FRED_API_KEY"] = fred_key
    engine = create_engine(db_url, pool_pre_ping=True)

    # ===== Fetch Macro Series =====
    print("\n📊 Fetching Macroeconomic Series...")
    macro_data = {}
    for label, fid in MACRO_SERIES.items():
        try:
            macro_data[label] = fetch_series(fid)
            print(f"  ✓ {label}")
        except Exception as e:
            print(f"  ✗ Error fetching {label}: {e}")

    macro_df = pd.concat(macro_data, axis=1)
    macro_df = to_monthly(macro_df)
    macro_df.reset_index(inplace=True)
    macro_df.rename(columns={"index": "date"}, inplace=True)

    # ===== Fetch Commodity Series =====
    print("\n🔨 Fetching Commodity Series...")
    commodity_data = {}
    for label, info in COMMODITY_SERIES.items():
        fid = info["fred_id"]
        try:
            commodity_data[label] = fetch_series(fid)
            print(f"  ✓ {info['label']} ({label})")
        except Exception as e:
            print(f"  ✗ Error fetching {info['label']}: {e}")

    if commodity_data:
        commodity_df = pd.concat(commodity_data, axis=1)
        commodity_df = to_monthly(commodity_df)
        commodity_df.reset_index(inplace=True)
        commodity_df.rename(columns={"index": "date"}, inplace=True)
    else:
        commodity_df = pd.DataFrame()

    # ===== Write to Database =====
    with engine.begin() as conn:
        # Create/update macro table
        macro_cols = ", ".join([f'"{c}" DOUBLE PRECISION' for c in MACRO_SERIES.keys()])
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS fred_all_series (
                date DATE PRIMARY KEY,
                {macro_cols}
            );
        """))
        conn.execute(text("TRUNCATE fred_all_series;"))
        macro_df.to_sql("fred_all_series", conn, if_exists="append", index=False)
        print("\n✅ Macroeconomic data written to fred_all_series")

        # Create/update commodity table
        if not commodity_df.empty:
            commodity_cols = ", ".join([f'"{c}" DOUBLE PRECISION' for c in commodity_data.keys()])
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS fred_commodities (
                    date DATE PRIMARY KEY,
                    {commodity_cols}
                );
            """))
            conn.execute(text("TRUNCATE fred_commodities;"))
            commodity_df.to_sql("fred_commodities", conn, if_exists="append", index=False)
            print("✅ Commodity data written to fred_commodities")
        else:
            print("⚠️  No commodity data to write")

if __name__ == "__main__":
    main()
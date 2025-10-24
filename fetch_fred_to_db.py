#!/usr/bin/env python3
import os
from datetime import datetime
import pandas as pd
from pandas_datareader import data as pdr
from sqlalchemy import create_engine, text

# --- Series you want to track ---
SERIES = {
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
    idx = pd.date_range(m_start, m_end, freq="M")
    return df.asfreq("D").ffill().reindex(idx).ffill()

def main():
    fred_key = os.getenv("FRED_API_KEY")
    db_url = os.getenv("DATABASE_URL")
    if not fred_key or not db_url:
        raise SystemExit("Missing FRED_API_KEY or DATABASE_URL")

    os.environ["FRED_API_KEY"] = fred_key
    engine = create_engine(db_url, pool_pre_ping=True)

    data = {}
    for label, fid in SERIES.items():
        try:
            data[label] = fetch_series(fid)
            print(f"Fetched {label}")
        except Exception as e:
            print(f"Error fetching {label}: {e}")

    df = pd.concat(data, axis=1)
    df = to_monthly(df)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "date"}, inplace=True)

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fred_all_series (
                date DATE PRIMARY KEY,
                "Real_GDP" DOUBLE PRECISION,
                "Unemployment_Rate" DOUBLE PRECISION,
                "Nonfarm_Payrolls" DOUBLE PRECISION,
                "CPI_All_Items" DOUBLE PRECISION,
                "PCE_Price_Index" DOUBLE PRECISION,
                "Industrial_Production" DOUBLE PRECISION,
                "Retail_Sales" DOUBLE PRECISION,
                "Revolving_Consumer_Credit" DOUBLE PRECISION,
                "Housing_Starts" DOUBLE PRECISION,
                "Fed_Funds_Rate" DOUBLE PRECISION,
                "Treasury_10Y_Yield" DOUBLE PRECISION,
                "Job_Openings_JOLTS" DOUBLE PRECISION
            );
        """))
        conn.execute(text("TRUNCATE fred_all_series;"))
        df.to_sql("fred_all_series", conn, if_exists="append", index=False)
        print("✅ FRED data written to Postgres.")

if __name__ == "__main__":
    main()

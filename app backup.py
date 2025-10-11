from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import os, time
from datetime import datetime, timedelta

# ----- FastAPI + templates/static -----
app = FastAPI()
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # This page will render the congress charts (index.html below)
    return env.get_template("index.html").render()

@app.get("/api/ping")
def ping():
    return {"ok": True}

# ----- Congress trades scraping & processing -----
import requests
from bs4 import BeautifulSoup
import pandas as pd

HEADERS = {"User-Agent": "Mozilla/5.0"}
CACHE = {"congress": None, "ts": 0}
CACHE_TTL = 300  # 5 minutes

def _get_table(url: str) -> pd.DataFrame:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table")
    if table is None:
        raise RuntimeError("No table found on page")
    return pd.read_html(str(table))[0]

def _load_congress_trades() -> pd.DataFrame:
    senate = _get_table("https://www.quiverquant.com/sources/senatetrading")
    house  = _get_table("https://www.quiverquant.com/sources/housetrading")
    senate["Chamber"] = "Senate"
    house["Chamber"]  = "House"
    df = pd.concat([senate, house], ignore_index=True)

    # Normalize columns
    df.columns = [c.strip() for c in df.columns]
    if "Unnamed: 6" in df.columns:
        df = df.rename(columns={"Unnamed: 6": "Price Change %"})
    # Transaction pieces
    def trans_type(s):
        return s.split(" ")[0] if isinstance(s, str) else None
    def low_amt(s):
        try:
            a = s.split("$", 1)[-1].split(" - ")[0]
            return int(a.replace(",", ""))
        except Exception:
            return None
    def high_amt(s):
        try:
            a = s.split("$", 1)[-1].split(" - ")[1].replace("$", "")
            return int(a.replace(",", ""))
        except Exception:
            return None

    df["Trans Type"]  = df["Transaction"].apply(trans_type)
    df["Low Range"]   = df["Transaction"].apply(low_amt)
    df["High Range"]  = df["Transaction"].apply(high_amt)
    df["Est. Trade Value"] = df[["Low Range", "High Range"]].mean(axis=1)

    # Dates
    df["Filed"]  = pd.to_datetime(df["Filed"],  errors="coerce")
    df["Traded"] = pd.to_datetime(df["Traded"], errors="coerce")

    # Signed value: Purchase = +, Sale = -
    df["Signed Value"] = df.apply(
        lambda r: r["Est. Trade Value"] if r["Trans Type"] == "Purchase"
        else (-r["Est. Trade Value"] if r["Trans Type"] == "Sale" else 0),
        axis=1
    )
    return df

def _compute_top_bottom(df: pd.DataFrame, n=10):
    df = df.dropna(subset=["Filed", "Signed Value", "Stock"])
    net = df.groupby("Stock")["Signed Value"].sum().sort_values()
    bottom = net.head(n)         # most net SOLD (negative)
    top    = net[::-1].head(n)   # most net BOUGHT (positive)
    start, end = df["Filed"].min(), df["Filed"].max()
    date_range = f"{start:%b %d, %Y} to {end:%b %d, %Y}" if pd.notnull(start) and pd.notnull(end) else "N/A"

    def to_list(series):
        return [{"stock": k, "value": float(v)} for k, v in series.items()]

    return {"date_range": date_range, "top10": to_list(top), "bottom10": to_list(bottom)}

@app.get("/api/congress/top-bottom")
def congress_top_bottom():
    # simple 5-min cache so we don't hammer the source
    now = time.time()
    if CACHE["congress"] and now - CACHE["ts"] < CACHE_TTL:
        return CACHE["congress"]

    df = _load_congress_trades()
    payload = _compute_top_bottom(df, n=10)
    payload["generated_at"] = datetime.utcnow().isoformat() + "Z"
    CACHE["congress"] = payload
    CACHE["ts"] = now
    return payload

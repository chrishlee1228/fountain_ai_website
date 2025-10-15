#   uvicorn app:app --reload
import os, time, asyncio
from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
import feedparser
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

# ----- FastAPI + templates/static -----
app = FastAPI()
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"), auto_reload=True)
templates = Jinja2Templates(directory="templates")

# ===== Background weekly refresh for Congress cache =====
WEEK_SECONDS = 7 * 24 * 60 * 60  # one week

@app.on_event("startup")
async def schedule_weekly_refresh():
    async def loop_refresh():
        try:
            _refresh_congress_cache()  # warm on boot
        except Exception as e:
            print("Initial refresh failed:", repr(e))

        while True:
            await asyncio.sleep(WEEK_SECONDS)
            try:
                _refresh_congress_cache()
                print("Weekly refresh completed")
            except Exception as e:
                print("Weekly refresh failed:", repr(e))
    asyncio.create_task(loop_refresh())

# ==================== Page routes ====================

# NEW: blank/simple landing page at "/"
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("a.home.html", {"request": request})

# Congress dashboard moved to "/congress"
@app.get("/congress", response_class=HTMLResponse)
def congress(request: Request):
    return templates.TemplateResponse("congress.html", {"request": request})

@app.get("/portfolio", response_class=HTMLResponse)
def portfolio(request: Request):
    return templates.TemplateResponse("portfolio.html", {"request": request})

@app.get("/api/ping")
def ping():
    return {"ok": True}

@app.post("/tasks/refresh")
def force_refresh():
    _refresh_congress_cache()
    return {"ok": True, "refreshed_at": datetime.utcnow().isoformat() + "Z"}

# ================== Congress scraping ==================
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

def _refresh_congress_cache():
    """Fetch data, compute top/bottom, and store it in CACHE."""
    df = _load_congress_trades()
    payload = _compute_top_bottom(df, n=10)
    payload["generated_at"] = datetime.utcnow().isoformat() + "Z"
    CACHE["congress"] = payload
    CACHE["ts"] = time.time()

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

# ================= Portfolio APIs =================

@app.get("/api/news")
def portfolio_news(tickers: str = Query(..., description="comma separated tickers")):
    """
    Aggregates headlines from Yahoo Finance RSS (no API key).
    Example feed: https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL&region=US&lang=en-US
    """
    syms = [s.strip().upper() for s in tickers.split(",") if s.strip()]
    if not syms:
        return {"count": 0, "articles": []}

    articles = []
    for s in syms:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={s}&region=US&lang=en-US"
        feed = feedparser.parse(url)
        for e in feed.entries[:30]:
            articles.append({
                "title": e.get("title"),
                "url": e.get("link"),
                "source": "Yahoo Finance",
                "published_at": e.get("published") or e.get("updated") or None,
            })

    # de-dup by URL and trim
    seen, dedup = set(), []
    for a in articles:
        if not a["url"] or a["url"] in seen:
            continue
        seen.add(a["url"])
        dedup.append(a)
    return {"count": len(dedup), "articles": dedup[:100]}

@app.get("/api/forecast/{ticker}")
def forecast_one(ticker: str, horizon: int = 252):
    """
    Minimal working forecast: price history + simple linear trend forward,
    plus an in-sample rolling mean as the 'backtest' line so the chart has data.
    """
    ticker = ticker.upper()
    df = yf.download(ticker, period="5y", interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No price data for {ticker}")

    s = df["Close"].dropna()
    dates = s.index.to_pydatetime().tolist()
    y = s.values.astype(float)

    # backtest = rolling mean
    window = min(60, len(y)//6 or 30)
    backtest = pd.Series(y).rolling(window=window, min_periods=1).mean().values

    # simple linear trend forecast
    x = np.arange(len(y))
    A = np.vstack([x, np.ones_like(x)]).T
    m, b = np.linalg.lstsq(A, y, rcond=None)[0]
    future_x = np.arange(len(y), len(y) + horizon)
    fc = m * future_x + b

    resid = y - (m * x + b)
    sd = np.std(resid) if len(resid) > 1 else 0.0
    fc_upper = fc + sd
    fc_lower = fc - sd

    return {
        "dates": [d.strftime("%Y-%m-%d") for d in dates],
        "price": [float(v) for v in y],
        "forecast": [float(v) for v in fc],
        "forecast_upper": [float(v) for v in fc_upper],
        "forecast_lower": [float(v) for v in fc_lower],
        "dates_pe": [d.strftime("%Y-%m-%d") for d in dates],
        "eps_ttm": [None] * len(dates),
        "pe_ttm": [None] * len(dates),
        "backtest": [float(v) for v in backtest],
        "backtest_mape": float("nan"),
        "backtest_mae": float("nan"),
        "backtest_coverage": float("nan"),
    }

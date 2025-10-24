# uvicorn app:app --reload
import os, time, asyncio, re
from datetime import datetime
from functools import lru_cache

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

from fastapi import FastAPI, Request, Query, HTTPException  # (you already have this line)

from dotenv import load_dotenv
load_dotenv("api.env")



# ----- FastAPI + templates/static -----
app = FastAPI()
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"), auto_reload=True)
templates = Jinja2Templates(directory="templates")

# ==================== Page routes ====================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("a.home.html", {"request": request})

@app.get("/congress", response_class=HTMLResponse)
def congress(request: Request):
    return templates.TemplateResponse("congress.html", {"request": request})

@app.get("/portfolio", response_class=HTMLResponse)
def portfolio(request: Request):
    return templates.TemplateResponse("portfolio.html", {"request": request})

@app.get("/api/ping")
def ping():
    return {"ok": True}


# ---------- Home: Major Headlines (CNBC only) ----------
HOME_NEWS_CACHE = {"ts": 0, "payload": None}
HOME_NEWS_TTL = 300

@app.get("/api/home/major")
def home_major(limit: int = 20):
    now = time.time()
    if HOME_NEWS_CACHE["payload"] and now - HOME_NEWS_CACHE["ts"] < HOME_NEWS_TTL:
        return HOME_NEWS_CACHE["payload"]

    FEED_URL = "https://www.cnbc.com/id/100003114/device/rss/rss.html"
    headers = {"User-Agent": "FountainAI/1.0 (+contact admin@fountain-ai.com)"}
    try:
        r = requests.get(FEED_URL, headers=headers, timeout=10)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
    except Exception as e:
        print("CNBC fetch error:", repr(e))
        payload = {"count": 0, "articles": []}
        HOME_NEWS_CACHE.update(ts=now, payload=payload)
        return payload

    arts = []
    for e in (feed.entries or [])[:limit]:
        t, link = (e.get("title") or "").strip(), (e.get("link") or "").strip()
        if t and link:
            arts.append({"title": t, "url": link, "source": "CNBC",
                         "published_at": e.get("published") or e.get("updated")})
    payload = {"count": len(arts), "articles": arts}
    HOME_NEWS_CACHE.update(ts=now, payload=payload)
    return payload

# ================= Macro (FRED) =================


# ========= SEC (Home feed + per-ticker browse) ======================
SEC_HEADERS = {
    "User-Agent": "FountainAI/1.0 (fountain-ai.com) Contact: admin@fountain-ai.com",
    "Accept": "application/json, text/xml, application/atom+xml;q=0.9,*/*;q=0.8",
}

def _clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

# ---------- Home: recent SEC filings ----------
HOME_SEC_CACHE = {"ts": 0, "payload": None}
HOME_SEC_TTL = 300

@app.get("/api/home/sec-recent")
def sec_recent(forms: str = "10-K,10-Q,8-K", count: int = 50):
    now = time.time()
    if HOME_SEC_CACHE["payload"] and now - HOME_SEC_CACHE["ts"] < HOME_SEC_TTL:
        return HOME_SEC_CACHE["payload"]

    wants = {f.strip().upper() for f in forms.split(",") if f.strip()}
    filings: list[dict] = []

    # 1) Atom feed (current filings)
    try:
        atom_count = min(max(int(count), 1), 200)
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&count={atom_count}&output=atom"
        r = requests.get(url, headers=SEC_HEADERS, timeout=15); r.raise_for_status()
        parsed = feedparser.parse(r.content)
        for ent in parsed.entries or []:
            title = _clean(ent.get("title"))
            link = ent.get("link")
            updated = ent.get("updated") or ent.get("published")
            atom_form = None
            for c in (ent.get("tags") or ent.get("categories") or []):
                term = (c.get("term") or "").upper()
                if term in wants:
                    atom_form = term; break
            if not atom_form:
                m = re.search(r"\b(10-K|10-Q|8-K)\b", title, re.I)
                if m: atom_form = m.group(1).upper()
            if not atom_form or (wants and atom_form not in wants):
                continue
            company = title.split(" - ", 1)[-1].strip() if " - " in title else title
            filings.append({
                "company": company,
                "form": atom_form,
                "filed_at": updated,
                "url": link,
                "source": "SEC EDGAR"
            })
            if len(filings) >= count:
                break
    except Exception as e:
        print("SEC Atom error:", repr(e))

    # 2) Fallback HTML pages (40 rows/page)
    if len(filings) < count:
        try:
            remaining = count - len(filings)
            for start in range(0, min(200, remaining + 40), 40):
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&start={start}&count=40"
                rr = requests.get(url, headers=SEC_HEADERS, timeout=15); rr.raise_for_status()
                soup = BeautifulSoup(rr.text, "html.parser")
                rows = soup.select("table tr")[1:]
                for tr in rows:
                    tds = tr.find_all("td")
                    if len(tds) < 3:
                        continue
                    form = _clean(tds[0].get_text()).upper()
                    if wants and form not in wants:
                        continue
                    comp_a = tds[2].find("a")
                    company = _clean(comp_a.text) if comp_a else _clean(tds[2].get_text())
                    link_a = tds[2].find("a", href=True)
                    link = (f"https://www.sec.gov{link_a['href']}"
                            if link_a and not link_a["href"].startswith("http") else (link_a["href"] if link_a else None))
                    filed_at = _clean(tds[5].get_text()) if len(tds) >= 6 else None
                    filings.append({
                        "company": company,
                        "form": form,
                        "filed_at": filed_at,
                        "url": link,
                        "source": "SEC EDGAR"
                    })
                    if len(filings) >= count:
                        break
                if len(filings) >= count:
                    break
        except Exception as e:
            print("SEC HTML scrape error:", repr(e))

    payload = {"count": len(filings), "filings": filings[:count]}
    HOME_SEC_CACHE.update(ts=now, payload=payload)
    return payload

# --- Enrich filings with per-row descriptions from the company browse page (HTML) ---
DESC_CACHE = {}   # key: cik_int -> {"ts":..., "map": {...}}
DESC_TTL = 300

def _acc_from_link(url: str) -> str | None:
    m = re.search(r"/data/\d+/(\d{10,})/", url or "")
    if m:
        return m.group(1)
    m = re.findall(r"(\d{10,})", url or "")
    return max(m, key=len) if m else None

def _company_browse_descriptions(cik_num: int, count: int = 200) -> dict[str, str]:
    """Scrape the 'getcompany' HTML table; return {accession_no_dashes: description}."""
    now = time.time()
    cached = DESC_CACHE.get(cik_num)
    if cached and now - cached["ts"] < DESC_TTL:
        return cached["map"]

    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "CIK": str(int(cik_num)),
        "owner": "exclude",
        "count": str(min(max(20, count), 400)),
    }
    desc_map: dict[str, str] = {}
    try:
        rr = requests.get(url, headers=SEC_HEADERS, params=params, timeout=15)
        rr.raise_for_status()
        soup = BeautifulSoup(rr.text, "html.parser")
        rows = soup.select("table.tableFile2 tr")[1:] or soup.select("table tr")[1:]
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) < 3:
                continue
            docs_a = tds[1].find("a", href=True) if len(tds) > 1 else None
            desc_txt = _clean(tds[2].get_text())
            if not docs_a:
                continue
            href = docs_a["href"]
            if href and not href.startswith("http"):
                href = f"https://www.sec.gov{href}"
            acc = _acc_from_link(href)
            if acc:
                desc_map[acc] = desc_txt
    except Exception as e:
        print("company browse description scrape error:", repr(e))

    DESC_CACHE[cik_num] = {"ts": now, "map": desc_map}
    return desc_map

# --- Per-ticker Atom feed + join with descriptions (used by /portfolio) ---
@lru_cache(maxsize=1)
def _ticker_map() -> dict[str, int]:
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=SEC_HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return {row["ticker"].upper(): int(row["cik_str"]) for _, row in data.items()}

def _sec_company_atom(cik_num: int, count: int = 200):
    """Company filings Atom feed (same source as SEC company page)."""
    url = "https://www.sec.gov/cgi-bin/browse-edgar"
    params = {
        "action": "getcompany",
        "CIK": str(int(cik_num)),
        "owner": "exclude",
        "count": str(min(max(20, count), 400)),
        "output": "atom",
    }
    r = requests.get(url, headers=SEC_HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return feedparser.parse(r.content)

def _parse_atom_entries(entries, wants: set[str], company_fallback: str):
    out = []
    for ent in (entries or []):
        title = (ent.get("title") or "").strip()
        link  = ent.get("link")
        when  = ent.get("updated") or ent.get("published")
        # Prefer explicit tags; fallback to title
        form = None
        for c in (ent.get("tags") or ent.get("categories") or []):
            term = (c.get("term") or "").upper()
            if term in {"10-K","10-Q","8-K"}:
                form = term; break
        if not form:
            m = re.search(r"\b(10-K|10-Q|8-K)\b", title, re.I)
            if m: form = m.group(1).upper()
        if not form or (wants and form not in wants):
            continue
        company = title.split(" - ", 1)[-1].strip() if " - " in title else company_fallback
        out.append({
            "company": company,
            "form": form,
            "filed_at": when,
            "url": link,
            "source": "SEC EDGAR",
        })
    return out

@app.get("/api/sec/filings-browse-for")
def sec_filings_browse_batch(
    tickers: str = Query(..., description="comma-separated tickers"),
    forms: str = "10-K,10-Q,8-K",
    count_per: int = 200
):
    """
    For each ticker:
      1) Pull company Atom feed -> form/date/url
      2) Scrape company browse HTML once -> accession -> short description
      3) Join by accession extracted from the Atom link (adds 'desc')
    """
    wants = {w.strip().upper() for w in forms.split(",") if w.strip()}
    mp = _ticker_map()
    ticks = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    by_ticker: dict[str, list[dict]] = {}

    for t in ticks:
        cik = mp.get(t)
        if not cik:
            by_ticker[t] = []
            continue

        try:
            feed = _sec_company_atom(cik_num=cik, count=count_per)
            rows = _parse_atom_entries(feed.entries, wants, company_fallback=t)
            desc_map = _company_browse_descriptions(cik, count=count_per)

            for r in rows:
                acc = _acc_from_link(r.get("url") or "")
                if acc and acc in desc_map:
                    r["desc"] = desc_map[acc]
        except Exception as e:
            print(f"[SEC browse] {t} failed:", repr(e))
            rows = []

        def _datekey(x):
            try:
                return pd.to_datetime(x.get("filed_at")).to_pydatetime()
            except Exception:
                return datetime.min
        rows.sort(key=_datekey, reverse=True)
        by_ticker[t] = rows

        time.sleep(0.25)  # tiny politeness pause

    return {"by_ticker": by_ticker}

#====================Sector Stock Prices


# ================== Congress scraping trades==================
WEEK_SECONDS = 7 * 24 * 60 * 60

@app.on_event("startup")
async def schedule_weekly_refresh():
    async def loop_refresh():
        try: _refresh_congress_cache()
        except Exception as e: print("Initial refresh failed:", repr(e))
        while True:
            await asyncio.sleep(WEEK_SECONDS)
            try: _refresh_congress_cache(); print("Weekly refresh completed")
            except Exception as e: print("Weekly refresh failed:", repr(e))
    asyncio.create_task(loop_refresh())

HEADERS = {"User-Agent": "Mozilla/5.0"}
CACHE = {"congress": None, "ts": 0}
CACHE_TTL = 300

def _get_table(url: str) -> pd.DataFrame:
    r = requests.get(url, headers=HEADERS, timeout=20); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser"); table = soup.find("table")
    if table is None: raise RuntimeError("No table found on page")
    return pd.read_html(str(table))[0]

def _load_congress_trades() -> pd.DataFrame:
    senate = _get_table("https://www.quiverquant.com/sources/senatetrading")
    house  = _get_table("https://www.quiverquant.com/sources/housetrading")
    senate["Chamber"] = "Senate"; house["Chamber"]  = "House"
    df = pd.concat([senate, house], ignore_index=True)
    df.columns = [c.strip() for c in df.columns]
    if "Unnamed: 6" in df.columns:
        df = df.rename(columns={"Unnamed: 6": "Price Change %"})
    def trans_type(s): return s.split(" ")[0] if isinstance(s, str) else None
    def low_amt(s):
        try: a = s.split("$",1)[-1].split(" - ")[0]; return int(a.replace(",",""))
        except: return None
    def high_amt(s):
        try: a = s.split("$",1)[-1].split(" - ")[1].replace("$",""); return int(a.replace(",",""))
        except: return None
    df["Trans Type"] = df["Transaction"].apply(trans_type)
    df["Low Range"]  = df["Transaction"].apply(low_amt)
    df["High Range"] = df["Transaction"].apply(high_amt)
    df["Est. Trade Value"] = df[["Low Range","High Range"]].mean(axis=1)
    df["Filed"]  = pd.to_datetime(df["Filed"],  errors="coerce")
    df["Traded"] = pd.to_datetime(df["Traded"], errors="coerce")
    df["Signed Value"] = df.apply(
        lambda r: r["Est. Trade Value"] if r["Trans Type"] == "Purchase"
        else (-r["Est. Trade Value"] if r["Trans Type"] == "Sale" else 0),
        axis=1)
    return df

def _compute_top_bottom(df: pd.DataFrame, n=10):
    df = df.dropna(subset=["Filed","Signed Value","Stock"])
    net = df.groupby("Stock")["Signed Value"].sum().sort_values()
    bottom = net.head(n); top = net[::-1].head(n)
    start, end = df["Filed"].min(), df["Filed"].max()
    date_range = f"{start:%b %d, %Y} to {end:%b %d, %Y}" if pd.notnull(start) and pd.notnull(end) else "N/A"
    to_list = lambda s: [{"stock": k, "value": float(v)} for k,v in s.items()]
    return {"date_range": date_range, "top10": to_list(top), "bottom10": to_list(bottom)}

def _refresh_congress_cache():
    df = _load_congress_trades()
    payload = _compute_top_bottom(df, n=10)
    payload["generated_at"] = datetime.utcnow().isoformat() + "Z"
    CACHE.update(congress=payload, ts=time.time())

@app.get("/api/congress/top-bottom")
def congress_top_bottom():
    now = time.time()
    if CACHE["congress"] and now - CACHE["ts"] < CACHE_TTL:
        return CACHE["congress"]
    df = _load_congress_trades()
    payload = _compute_top_bottom(df, n=10)
    payload["generated_at"] = datetime.utcnow().isoformat() + "Z"
    CACHE.update(congress=payload, ts=now)
    return payload

# ================= Portfolio APIs =================
@app.get("/api/news")
def portfolio_news(tickers: str = Query(..., description="comma separated tickers")):
    syms = [s.strip().upper() for s in tickers.split(",") if s.strip()]
    if not syms: return {"count": 0, "articles": []}
    arts = []
    for s in syms:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={s}&region=US&lang=en-US"
        feed = feedparser.parse(url)
        for e in feed.entries[:30]:
            arts.append({"title": e.get("title"), "url": e.get("link"),
                         "source": "Yahoo Finance",
                         "published_at": e.get("published") or e.get("updated")})
    seen, out = set(), []
    for a in arts:
        if a["url"] and a["url"] not in seen:
            seen.add(a["url"]); out.append(a)
    return {"count": len(out), "articles": out[:100]}


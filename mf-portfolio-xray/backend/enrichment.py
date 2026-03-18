from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx
import pandas as pd
import yfinance as yf
from rapidfuzz import process

from analytics import compute_xirr

MFAPI_BASE = "https://api.mfapi.in/mf"
HTTP_RETRY_ATTEMPTS = 3

_scheme_code_cache: dict[str, str | None] = {}
_fund_details_cache: dict[str, dict[str, Any]] = {}
_current_nav_cache: dict[str, float] = {}
_nifty_download_cache: dict[tuple[str, str], pd.Series] = {}

# Demo fallback holdings for overlap analysis when disclosures are unavailable.
FALLBACK_HOLDINGS: dict[str, set[str]] = {
    "large_cap": {
        "RELIANCE",
        "TCS",
        "HDFCBANK",
        "ICICIBANK",
        "INFY",
        "ITC",
        "LT",
        "SBIN",
        "BHARTIARTL",
        "KOTAKBANK",
    },
    "flexi_cap": {
        "RELIANCE",
        "INFY",
        "HDFCBANK",
        "AXISBANK",
        "BAJFINANCE",
        "LT",
        "ULTRACEMCO",
        "MARUTI",
        "TITAN",
        "ASIANPAINT",
    },
    "mid_cap": {
        "TRENT",
        "MOTHERSON",
        "DIXON",
        "POLYCAB",
        "PIIND",
        "CUMMINSIND",
        "LODHA",
        "MAXHEALTH",
        "AUBANK",
        "BSE",
    },
}


async def get_scheme_code(fund_name: str) -> str | None:
    cache_key = fund_name.strip().lower()
    if cache_key in _scheme_code_cache:
        return _scheme_code_cache[cache_key]

    try:
        payload = await _request_json(f"{MFAPI_BASE}/search", params={"q": fund_name}, timeout=15)
    except Exception:
        _scheme_code_cache[cache_key] = None
        return None

    if not isinstance(payload, list) or not payload:
        _scheme_code_cache[cache_key] = None
        return None

    choices = []
    lookup: dict[str, dict[str, Any]] = {}
    for item in payload:
        name = str(item.get("schemeName", "")).strip()
        if not name:
            continue
        choices.append(name)
        lookup[name] = item

    if not choices:
        _scheme_code_cache[cache_key] = None
        return None

    best = process.extractOne(fund_name, choices)
    if not best:
        _scheme_code_cache[cache_key] = None
        return None

    best_name, score, _ = best
    if score < 70:
        _scheme_code_cache[cache_key] = None
        return None

    chosen = lookup.get(best_name, {})
    code = chosen.get("schemeCode")
    resolved = str(code) if code is not None else None
    _scheme_code_cache[cache_key] = resolved
    return resolved


async def _request_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> Any:
    last_error: Exception | None = None
    for attempt in range(HTTP_RETRY_ATTEMPTS):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: PERF203
            last_error = exc
            if attempt < HTTP_RETRY_ATTEMPTS - 1:
                await asyncio.sleep(0.4 * (2**attempt))
    if last_error:
        raise last_error
    raise RuntimeError("Request failed")


async def get_fund_details(scheme_code: str) -> dict[str, Any]:
    if scheme_code in _fund_details_cache:
        return _fund_details_cache[scheme_code]

    data = await _request_json(f"{MFAPI_BASE}/{scheme_code}", timeout=20)

    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    nav_data = data.get("data", []) if isinstance(data, dict) else []

    details = {
        "name": meta.get("scheme_name", "Unknown"),
        "fund_type": meta.get("scheme_type", "Unknown"),
        "category": meta.get("scheme_category", "Unknown"),
        "ter": float(meta.get("expense_ratio") or 1.5),
        "nav_history": [
            {"date": item.get("date"), "nav": item.get("nav")}
            for item in nav_data
            if isinstance(item, dict)
        ],
    }
    _fund_details_cache[scheme_code] = details
    return details


async def get_current_nav(scheme_code: str) -> float:
    if scheme_code in _current_nav_cache:
        return _current_nav_cache[scheme_code]

    details = await get_fund_details(scheme_code)
    nav_history = details.get("nav_history", [])
    if not nav_history:
        raise ValueError("NAV history unavailable")

    latest_nav = nav_history[0].get("nav")
    nav_value = float(str(latest_nav).replace(",", ""))
    _current_nav_cache[scheme_code] = nav_value
    return nav_value


def _nearest_close_price(series: pd.Series, d: date) -> float | None:
    if series.empty:
        return None
    ts = pd.Timestamp(d)
    if ts in series.index:
        return float(series.loc[ts])

    idx = series.index.searchsorted(ts)
    candidates = []
    if idx < len(series.index):
        candidates.append(series.index[idx])
    if idx > 0:
        candidates.append(series.index[idx - 1])
    if not candidates:
        return None

    best = min(candidates, key=lambda x: abs((x - ts).days))
    return float(series.loc[best])


def get_nifty50_xirr(
    start_date: date,
    end_date: date,
    investment_dates: list[date],
    investment_amounts: list[float],
) -> float | None:
    if not investment_dates or not investment_amounts or len(investment_dates) != len(investment_amounts):
        return None

    cache_key = (start_date.isoformat(), end_date.isoformat())
    closes: pd.Series

    if cache_key in _nifty_download_cache:
        closes = _nifty_download_cache[cache_key]
    else:
        data = yf.download("^NSEI", start=start_date.isoformat(), end=end_date.isoformat(), progress=False)
        if data.empty or "Close" not in data:
            return None
        closes = data["Close"].dropna()
        _nifty_download_cache[cache_key] = closes

    if closes.empty:
        return None

    current_price = float(closes.iloc[-1])
    units = 0.0

    for d, amount in zip(investment_dates, investment_amounts):
        px = _nearest_close_price(closes, d)
        if px and px > 0:
            units += amount / px

    current_value = units * current_price
    cashflows = list(zip(investment_dates, [-abs(x) for x in investment_amounts]))
    cashflows.append((end_date, current_value))
    return compute_xirr(cashflows)


async def get_fund_holdings(scheme_code: str) -> set[str]:
    # AMFI does not provide a stable public JSON holdings API; use fallback theme buckets.
    if not scheme_code:
        return set()
    try:
        bucket = int(scheme_code) % 3
    except ValueError:
        bucket = 0

    if bucket == 0:
        return set(FALLBACK_HOLDINGS["large_cap"])
    if bucket == 1:
        return set(FALLBACK_HOLDINGS["flexi_cap"])
    return set(FALLBACK_HOLDINGS["mid_cap"])

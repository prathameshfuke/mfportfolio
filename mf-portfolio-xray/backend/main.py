from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from advisor import generate_rebalancing_plan
from analytics import compute_expense_drag, compute_health_score, compute_overlap, compute_xirr, mean
from enrichment import get_current_nav, get_fund_details, get_fund_holdings, get_nifty50_xirr, get_scheme_code
from models import AnalysisResponse, FundResult, OverlapPair
from parser import parse_cams_pdf

load_dotenv(dotenv_path=Path(__file__).with_name(".env"))

app = FastAPI(title="MF Portfolio X-Ray", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://mf-portfolio-xray.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SAMPLE_RESPONSE: dict[str, Any] = {
    "health_score": 72,
    "total_invested": 269326.30,
    "current_value": 380005.31,
    "overall_xirr": 0.178,
    "benchmark_xirr": 0.143,
    "funds": [
        {
            "fund_name": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
            "scheme_code": "120503",
            "current_units": 1635.172,
            "current_nav": 76.452,
            "current_value": 124965.18,
            "invested_amount": 97777.80,
            "xirr": 0.142,
            "ter_pct": 1.05,
            "category": "Large Cap",
            "annual_drag_inr": 1312.00,
        },
        {
            "fund_name": "Axis Midcap Fund - Regular Plan - Growth",
            "scheme_code": "120823",
            "current_units": 1770.055,
            "current_nav": 70.124,
            "current_value": 124123.26,
            "invested_amount": 83987.40,
            "xirr": 0.187,
            "ter_pct": 1.85,
            "category": "Mid Cap",
            "annual_drag_inr": 2296.00,
        },
        {
            "fund_name": "SBI Small Cap Fund - Regular Plan - Growth",
            "scheme_code": "125497",
            "current_units": 1005.399,
            "current_nav": 130.241,
            "current_value": 130916.87,
            "invested_amount": 87561.10,
            "xirr": 0.221,
            "ter_pct": 1.92,
            "category": "Small Cap",
            "annual_drag_inr": 2514.00,
        },
    ],
    "overlap_pairs": [
        {
            "fund_a": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
            "fund_b": "Axis Midcap Fund - Regular Plan - Growth",
            "overlap_pct": 38.0,
        },
        {
            "fund_a": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
            "fund_b": "SBI Small Cap Fund - Regular Plan - Growth",
            "overlap_pct": 21.0,
        },
        {
            "fund_a": "Axis Midcap Fund - Regular Plan - Growth",
            "fund_b": "SBI Small Cap Fund - Regular Plan - Growth",
            "overlap_pct": 18.0,
        },
    ],
    "total_ter_drag_inr": 6122.00,
    "total_ter_drag_pct": 1.611,
    "rebalancing_plan": {
        "health_score": 72,
        "summary": "Your portfolio has strong growth potential but overlap and costs can be optimized. A light rebalance can improve risk-adjusted returns.",
        "issues": [
            {
                "type": "overlap",
                "severity": "high",
                "title": "Mirae Axis overlap high",
                "explanation": "Mirae Large Cap and Axis Midcap share a meaningful common stock basket. This reduces diversification benefit and can amplify drawdowns in market stress.",
                "action": "Shift part of fresh SIP allocation from one overlapping fund into a less correlated category such as flexi-cap or value-oriented exposure.",
            },
            {
                "type": "ter_drag",
                "severity": "medium",
                "title": "SBI TER drag elevated",
                "explanation": "The SBI Small Cap holding has a higher annual TER burden versus the rest of the portfolio. Over time this cost drag compounds and reduces net alpha.",
                "action": "Cap small-cap allocation and compare lower-cost category alternatives before adding incremental capital.",
            },
            {
                "type": "benchmark_lag",
                "severity": "low",
                "title": "Mirae near benchmark",
                "explanation": "Mirae is only slightly above benchmark in this period, which is acceptable but not compelling. Monitoring consistency is important before increasing concentration.",
                "action": "Review rolling 3-year performance and keep this fund as core only if risk-adjusted outperformance persists.",
            },
        ],
        "rebalancing_steps": [
            "Freeze new SIP additions in the most overlapping pair for one quarter.",
            "Redirect monthly SIP increments toward underrepresented categories aligned to your risk profile.",
            "Rebalance annually using overlap under 25% and TER under 1.5% as target constraints.",
        ],
        "tax_notes": "If equity units are switched before 1 year, STCG may apply; beyond 1 year, LTCG rules apply. Prefer rebalancing through new SIP flows to reduce taxable redemptions.",
    },
    "issues": [],
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/sample")
def sample() -> dict[str, Any]:
    raise HTTPException(status_code=404, detail="Sample endpoint disabled. Upload a real statement to analyze.")


def _tx_to_cashflow_type(tx_type: str) -> int:
    t = tx_type.lower()
    if "redemption" in t or "switch out" in t or "dividend" in t:
        return 1
    return -1


def _parse_dt(d: str) -> date:
    return datetime.strptime(d, "%d-%b-%Y").date()


def _is_valid_risk_profile(value: str) -> bool:
    return value in {"Conservative", "Moderate", "Aggressive"}


def _normalize_risk_profile(value: str) -> str:
    if not value:
        return "Moderate"
    normalized = value.strip().lower()
    mapping = {
        "conservative": "Conservative",
        "moderate": "Moderate",
        "aggressive": "Aggressive",
    }
    return mapping.get(normalized, "Moderate")


def _push_issue(issues: list[str], issue: str) -> None:
    if issue and issue not in issues:
        issues.append(issue)


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    file: UploadFile = File(...),
    risk_profile: str = Form("Moderate"),
    user_api_key: str | None = Form(None),
    user_api_provider: str | None = Form(None),
) -> AnalysisResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    risk_profile = _normalize_risk_profile(risk_profile)

    raw = await file.read()
    parsed = parse_cams_pdf(raw)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Could not parse this PDF. Please ensure it is a CAMS or KFintech consolidated statement.",
        )

    funds: list[FundResult] = []
    all_portfolio_cashflows: list[tuple[date, float]] = []
    investment_dates: list[date] = []
    investment_amounts: list[float] = []
    issues: list[str] = []

    for pf in parsed:
        fund_name = str(pf.get("fund_name", "")).strip()
        scheme_code = pf.get("scheme_code")
        if not scheme_code:
            try:
                scheme_code = await get_scheme_code(fund_name)
            except Exception:
                scheme_code = None

        details: dict[str, Any] = {}
        current_nav: float | None = None

        if scheme_code:
            try:
                details = await get_fund_details(str(scheme_code))
                current_nav = await get_current_nav(str(scheme_code))
            except Exception:
                current_nav = None

        if current_nav is None:
            closing_nav = pf.get("closing_nav")
            market_value = pf.get("market_value")
            closing_units = pf.get("closing_units")
            current_nav = closing_nav or (market_value / closing_units if market_value and closing_units else None)

        if current_nav is None:
            _push_issue(issues, f"NAV fallback unavailable for {fund_name}")
            current_nav = 0.0

        transactions = pf.get("transactions", [])
        current_units = float(pf.get("closing_units") or 0.0)
        if current_units == 0 and transactions:
            current_units = sum(
                float(tx.get("units", 0.0)) * (_tx_to_cashflow_type(str(tx.get("type", ""))) * -1)
                for tx in transactions
            )

        current_value = (current_units or 0.0) * current_nav
        invested_amount = 0.0

        fund_cashflows: list[tuple[date, float]] = []
        for tx in transactions:
            try:
                d = _parse_dt(str(tx.get("date", "")))
            except (ValueError, TypeError):
                continue

            sign = _tx_to_cashflow_type(str(tx.get("type", "")))
            amount = abs(float(tx.get("amount", 0.0))) * sign
            fund_cashflows.append((d, amount))
            all_portfolio_cashflows.append((d, amount))
            if sign < 0:
                investment_dates.append(d)
                investment_amounts.append(abs(float(tx.get("amount", 0.0))))
                invested_amount += abs(float(tx.get("amount", 0.0)))

        if current_value > 0 and fund_cashflows:
            fund_cashflows.append((date.today(), current_value))

        fxirr = compute_xirr(fund_cashflows)
        if fxirr is None and transactions:
            _push_issue(issues, f"Insufficient transaction history for XIRR calculation in {fund_name}")

        ter_pct = float(details.get("ter", 1.5)) if details else 1.5
        category = str(details.get("category", "Unknown")) if details else "Unknown"

        funds.append(
            FundResult(
                fund_name=fund_name,
                scheme_code=str(scheme_code) if scheme_code else None,
                current_units=round(current_units, 4),
                current_nav=round(current_nav, 4),
                current_value=round(current_value, 2),
                invested_amount=round(invested_amount, 2),
                xirr=fxirr,
                ter_pct=round(ter_pct, 3),
                category=category,
                annual_drag_inr=0.0,
            )
        )

    total_invested = round(sum(f.invested_amount for f in funds), 2)
    current_value = round(sum(f.current_value for f in funds), 2)

    if all_portfolio_cashflows and current_value > 0:
        all_portfolio_cashflows.append((date.today(), current_value))
    overall_xirr = compute_xirr(all_portfolio_cashflows)

    benchmark_xirr = None
    if investment_dates and investment_amounts:
        try:
            benchmark_xirr = get_nifty50_xirr(
                min(investment_dates),
                date.today(),
                investment_dates,
                investment_amounts,
            )
        except Exception:
            benchmark_xirr = None
            _push_issue(issues, "Benchmark data unavailable from yfinance")

    holdings_map: dict[str, set[str]] = {}
    if len(funds) > 1:
        for f in funds:
            if not f.scheme_code:
                continue
            try:
                holdings_map[f.fund_name] = await get_fund_holdings(f.scheme_code)
            except Exception:
                holdings_map[f.fund_name] = set()

    overlap_pairs: list[OverlapPair] = []
    if len(holdings_map) > 1 and any(holdings_map.values()):
        overlap = compute_overlap(holdings_map)
        for (a, b), pct in overlap.items():
            overlap_pairs.append(OverlapPair(fund_a=a, fund_b=b, overlap_pct=round(pct * 100.0, 2)))
    elif len(funds) > 1:
        _push_issue(issues, "Holdings data unavailable for overlap analysis")

    expense = compute_expense_drag(funds)
    avg_overlap = mean([p.overlap_pct / 100.0 for p in overlap_pairs]) if overlap_pairs else 0.0
    health_score = compute_health_score(
        overall_xirr,
        benchmark_xirr,
        avg_overlap,
        expense["total_drag_pct"],
    )

    provider = (user_api_provider or "").strip().lower()
    provider = provider if provider in {"gemini", "anthropic"} else None
    provided_key = (user_api_key or "").strip() or None

    advisor_payload: dict[str, Any] | None = None
    if provided_key or os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        advisor_payload = await generate_rebalancing_plan(
            risk_profile=risk_profile,
            total_invested=total_invested,
            current_value=current_value,
            overall_xirr=overall_xirr,
            benchmark_xirr=benchmark_xirr,
            funds=funds,
            overlap_pairs=[p.model_dump() for p in overlap_pairs],
            total_ter_drag_inr=expense["total_drag_inr"],
            total_ter_drag_pct=expense["total_drag_pct"],
            api_key_override=provided_key,
            api_provider_override=provider,
        )

    if advisor_payload is None:
        if provided_key:
            _push_issue(issues, "AI advisor request failed using provided API key")
        else:
            _push_issue(issues, "Set GEMINI_API_KEY or ANTHROPIC_API_KEY, or provide one in the app")

    return AnalysisResponse(
        health_score=int(advisor_payload.get("health_score", health_score)) if advisor_payload else health_score,
        total_invested=total_invested,
        current_value=current_value,
        overall_xirr=overall_xirr,
        benchmark_xirr=benchmark_xirr,
        funds=funds,
        overlap_pairs=overlap_pairs,
        total_ter_drag_inr=expense["total_drag_inr"],
        total_ter_drag_pct=expense["total_drag_pct"],
        rebalancing_plan=advisor_payload,
        issues=issues,
    )

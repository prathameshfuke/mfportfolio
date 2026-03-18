from __future__ import annotations

from datetime import date
from itertools import combinations
from typing import Iterable

from scipy.optimize import brentq

from models import FundResult


def _npv(rate: float, cashflows: list[tuple[date, float]]) -> float:
    if rate <= -1.0:
        return float("inf")
    t0 = cashflows[0][0]
    return sum(cf / ((1 + rate) ** (((d - t0).days) / 365.0)) for d, cf in cashflows)


def compute_xirr(cashflows: list[tuple[date, float]]) -> float | None:
    if len(cashflows) < 2:
        return None

    dates = [d for d, _ in cashflows]
    if len(set(dates)) == 1:
        return None

    amounts = [a for _, a in cashflows]
    if not any(a < 0 for a in amounts) or not any(a > 0 for a in amounts):
        return None

    cashflows = sorted(cashflows, key=lambda x: x[0])

    try:
        lower = -0.9999
        upper_candidates = [1.0, 2.0, 5.0, 10.0, 25.0, 50.0]

        f_low = _npv(lower, cashflows)
        for upper in upper_candidates:
            f_up = _npv(upper, cashflows)
            if f_low == 0:
                return lower
            if f_up == 0:
                return upper
            if (f_low > 0 and f_up < 0) or (f_low < 0 and f_up > 0):
                return brentq(lambda r: _npv(r, cashflows), lower, upper, maxiter=300)

        return None
    except Exception:
        return None


def compute_overlap(fund_holdings: dict[str, set[str]]) -> dict[tuple[str, str], float]:
    overlap: dict[tuple[str, str], float] = {}
    for a, b in combinations(fund_holdings.keys(), 2):
        set_a = fund_holdings.get(a, set())
        set_b = fund_holdings.get(b, set())
        if not set_a and not set_b:
            overlap[(a, b)] = 0.0
            continue
        union = set_a | set_b
        overlap[(a, b)] = (len(set_a & set_b) / len(union)) if union else 0.0
    return overlap


def compute_expense_drag(funds: list[FundResult]) -> dict:
    per_fund: dict[str, float] = {}
    total_drag = 0.0
    total_value = sum(f.current_value for f in funds)

    for fund in funds:
        drag = fund.current_value * (fund.ter_pct / 100.0)
        fund.annual_drag_inr = round(drag, 2)
        per_fund[fund.fund_name] = fund.annual_drag_inr
        total_drag += drag

    total_drag_pct = (total_drag / total_value * 100.0) if total_value > 0 else 0.0

    return {
        "fund_drag_inr": per_fund,
        "total_drag_inr": round(total_drag, 2),
        "total_drag_pct": round(total_drag_pct, 3),
    }


def _score_linear(value: float, low: float, high: float, invert: bool = False) -> float:
    if high == low:
        return 0.0
    if invert:
        if value <= low:
            return 1.0
        if value >= high:
            return 0.0
        return (high - value) / (high - low)

    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def compute_health_score(
    xirr: float | None,
    benchmark_xirr: float | None,
    avg_overlap: float,
    total_ter_drag_pct: float,
) -> int:
    xirr_score = 20.0
    overlap_score = 15.0
    ter_score = 15.0

    if xirr is not None and benchmark_xirr is not None:
        diff = xirr - benchmark_xirr
        xirr_score = 40.0 * _score_linear(diff, -0.03, 0.02)

    overlap_score = 30.0 * _score_linear(avg_overlap, 0.15, 0.60, invert=True)
    ter_score = 30.0 * _score_linear(total_ter_drag_pct / 100.0, 0.005, 0.025, invert=True)

    score = round(max(0.0, min(100.0, xirr_score + overlap_score + ter_score)))
    return int(score)


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return (sum(values) / len(values)) if values else 0.0

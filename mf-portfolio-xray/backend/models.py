from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    date: str
    type: str
    units: float
    nav: float
    amount: float


class ParsedFund(BaseModel):
    fund_name: str
    scheme_code: str | None = None
    transactions: list[Transaction] = Field(default_factory=list)
    closing_units: float | None = None
    closing_nav: float | None = None
    market_value: float | None = None


class FundResult(BaseModel):
    fund_name: str
    scheme_code: str | None = None
    current_units: float = 0.0
    current_nav: float = 0.0
    current_value: float = 0.0
    invested_amount: float = 0.0
    xirr: float | None = None
    ter_pct: float = 1.5
    category: str = "Unknown"
    annual_drag_inr: float = 0.0


class OverlapPair(BaseModel):
    fund_a: str
    fund_b: str
    overlap_pct: float


class AdvisorIssue(BaseModel):
    type: Literal[
        "overlap",
        "ter_drag",
        "concentration",
        "benchmark_lag",
        "category_imbalance",
    ]
    severity: Literal["high", "medium", "low"]
    title: str
    explanation: str
    action: str


class RebalancingPlan(BaseModel):
    health_score: int = 50
    summary: str = "Portfolio analyzed successfully."
    issues: list[AdvisorIssue] = Field(default_factory=list)
    rebalancing_steps: list[str] = Field(default_factory=list)
    tax_notes: str = "No immediate tax impact"


class AnalysisResponse(BaseModel):
    health_score: int
    total_invested: float
    current_value: float
    overall_xirr: float | None
    benchmark_xirr: float | None
    funds: list[FundResult]
    overlap_pairs: list[OverlapPair]
    total_ter_drag_inr: float
    total_ter_drag_pct: float
    rebalancing_plan: RebalancingPlan | dict[str, Any] | None
    issues: list[str] = Field(default_factory=list)


class AnalyzeRequestContext(BaseModel):
    risk_profile: Literal["Conservative", "Moderate", "Aggressive"] = "Moderate"

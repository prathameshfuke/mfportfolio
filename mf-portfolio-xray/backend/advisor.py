from __future__ import annotations

import json
import os
from typing import Any

import httpx

from models import FundResult

CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """
You are an expert SEBI-registered mutual fund advisor analyzing an Indian retail investor's mutual fund portfolio. Give clear, actionable advice.

Rules:
- Recommend fund categories, not specific fund names
- Flag LTCG/STCG tax implications before recommending switches (equity funds: 1 year LTCG, debt: 3 years)
- Keep language simple for a retail investor
- Be specific about the problem and the action

Return ONLY a valid JSON object (no markdown, no preamble) with this exact structure:
{
  "health_score": <int 0-100>,
  "summary": "<2 sentence overall assessment>",
  "issues": [
    {
      "type": "<overlap|ter_drag|concentration|benchmark_lag|category_imbalance>",
      "severity": "<high|medium|low>",
      "title": "<short title, max 8 words>",
      "explanation": "<plain English, 2-3 sentences>",
      "action": "<specific concrete action>"
    }
  ],
  "rebalancing_steps": ["<Step 1>", "<Step 2>", ...],
  "tax_notes": "<LTCG/STCG notes if any switches recommended, else 'No immediate tax impact'>"
}
""".strip()


def _format_funds_table(funds: list[FundResult], total_value: float) -> str:
    rows = []
    for f in funds:
        weight = (f.current_value / total_value * 100.0) if total_value else 0.0
        rows.append(
            " | ".join(
                [
                    f.fund_name,
                    f.category,
                    f"{f.current_value:.2f}",
                    f"{weight:.2f}%",
                    "N/A" if f.xirr is None else f"{f.xirr * 100:.2f}%",
                    f"{f.ter_pct:.2f}%",
                    f"{f.annual_drag_inr:.2f}",
                ]
            )
        )
    return "\n".join(rows)


def _format_overlap(overlap_pairs: list[dict[str, Any]]) -> str:
    if not overlap_pairs:
        return "Holdings data unavailable for overlap analysis"

    lines = []
    for p in overlap_pairs:
        lines.append(f"{p['fund_a']} <-> {p['fund_b']}: {p['overlap_pct']:.2f}%")
    return "\n".join(lines)


def build_user_prompt(data: dict[str, Any]) -> str:
    return f"""
Here is the user's mutual fund portfolio:

PORTFOLIO SUMMARY:
- Total invested: INR {data['total_invested']:.2f}
- Current value: INR {data['current_value']:.2f}
- Overall XIRR: {'N/A' if data['overall_xirr'] is None else f"{data['overall_xirr']*100:.2f}%"}
- Benchmark XIRR (Nifty 50, same period): {'N/A' if data['benchmark_xirr'] is None else f"{data['benchmark_xirr']*100:.2f}%"}
- Risk profile selected by user: {data['risk_profile']}

FUNDS HELD:
{data['funds_table']}
(columns: Fund Name | Category | Value | Weight% | XIRR% | TER% | Annual Drag INR)

OVERLAP MATRIX:
{data['overlap_table']}
(Jaccard overlap % between each fund pair)

EXPENSE RATIO DRAG:
- Total annual TER cost: INR {data['total_ter_drag_inr']:.2f}
- As % of portfolio: {data['total_ter_drag_pct']:.2f}%

Analyze this portfolio and provide your assessment and rebalancing plan in the JSON format specified.
""".strip()


async def generate_rebalancing_plan(
    *,
    risk_profile: str,
    total_invested: float,
    current_value: float,
    overall_xirr: float | None,
    benchmark_xirr: float | None,
    funds: list[FundResult],
    overlap_pairs: list[dict[str, Any]],
    total_ter_drag_inr: float,
    total_ter_drag_pct: float,
    api_key_override: str | None = None,
    api_provider_override: str | None = None,
) -> dict[str, Any] | None:
    payload_context = {
        "risk_profile": risk_profile,
        "total_invested": total_invested,
        "current_value": current_value,
        "overall_xirr": overall_xirr,
        "benchmark_xirr": benchmark_xirr,
        "funds_table": _format_funds_table(funds, current_value),
        "overlap_table": _format_overlap(overlap_pairs),
        "total_ter_drag_inr": total_ter_drag_inr,
        "total_ter_drag_pct": total_ter_drag_pct,
    }

    user_prompt = build_user_prompt(payload_context)

    provider = (api_provider_override or "").strip().lower()
    override_key = (api_key_override or "").strip() or None

    gemini_key = override_key if provider == "gemini" else os.getenv("GEMINI_API_KEY")
    anthropic_key = override_key if provider == "anthropic" else os.getenv("ANTHROPIC_API_KEY")

    if provider and override_key is None:
        return None

    if gemini_key:
        gemini_payload = await _generate_with_gemini(gemini_key, user_prompt)
        if gemini_payload is not None:
            return gemini_payload

    if anthropic_key:
        anthropic_payload = await _generate_with_anthropic(anthropic_key, user_prompt)
        if anthropic_payload is not None:
            return anthropic_payload

    return None


def _extract_json_blob(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        return json.loads(raw)
    except Exception:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        candidate = raw[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return None


async def _generate_with_gemini(api_key: str, user_prompt: str) -> dict[str, Any] | None:
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(
                GEMINI_URL_TEMPLATE.format(model=GEMINI_MODEL),
                params={"key": api_key},
                json=body,
            )
            resp.raise_for_status()
            payload = resp.json()

        candidates = payload.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        text = parts[0].get("text", "")
        return _extract_json_blob(text)
    except Exception:
        return None


async def _generate_with_anthropic(api_key: str, user_prompt: str) -> dict[str, Any] | None:

    body = {
        "model": CLAUDE_MODEL,
        "system": SYSTEM_PROMPT,
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=40) as client:
            resp = await client.post(CLAUDE_URL, headers=headers, json=body)
            resp.raise_for_status()
            payload = resp.json()

        content_blocks = payload.get("content", [])
        if not content_blocks:
            return None
        text = content_blocks[0].get("text", "").strip()
        return _extract_json_blob(text)
    except Exception:
        return None

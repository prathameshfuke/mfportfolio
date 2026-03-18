from __future__ import annotations

import re

import pdfplumber

FUND_HEADER = re.compile(
    r"^(?P<name>[A-Za-z0-9&().,'\-/\s]+(?:Fund|FoF|ETF|Plan\s*-\s*Growth))\s*$",
    re.IGNORECASE,
)
TRANSACTION = re.compile(
    r"^(?P<date>\d{2}-[A-Za-z]{3}-\d{4})\s+"
    r"(?P<type>.+?)\s+"
    r"(?P<units>[\d,]+\.\d{1,4})\s+"
    r"(?P<nav>[\d,]+\.\d{1,4})\s+"
    r"(?P<amount>[\d,]+\.\d{1,2})\s+"
    r"(?P<balance>[\d,]+\.\d{1,4})\s*$",
    re.IGNORECASE,
)
CLOSING_LINE = re.compile(
    r"Closing\s+Unit\s+Balance\s*:\s*(?P<units>[\d,]+\.\d{1,4}).*?Market\s+Value\s*:\s*Rs\.?\s*(?P<market>[\d,]+\.\d{1,2})",
    re.IGNORECASE,
)
NAV_IN_CLOSING = re.compile(r"NAV\s*\(As\s+on.*?\)\s*:\s*Rs\.?\s*([\d,]+\.\d{1,4})", re.IGNORECASE)
SCHEME_CODE = re.compile(r"(?:Scheme\s*Code|Code)\s*:?\s*(\d{4,8})", re.IGNORECASE)
PORTFOLIO_SUMMARY = re.compile(r"^\s*PORTFOLIO\s+SUMMARY\s*$", re.IGNORECASE)

HEADER_BLOCKLIST = {
    "CONSOLIDATED ACCOUNT STATEMENT",
    "CAS - CAMS + KFINTECH | DETAILED STATEMENT",
    "PORTFOLIO SUMMARY",
}


def _normalize_tx_type(raw_type: str) -> str:
    tx = re.sub(r"\s+", " ", raw_type.strip())
    tx_low = tx.lower()
    if tx_low.startswith("purchase"):
        if "sip" in tx_low:
            return "SIP"
        return "Purchase"
    if "redemption" in tx_low:
        return "Redemption"
    if "switch in" in tx_low:
        return "Switch In"
    if "switch out" in tx_low:
        return "Switch Out"
    if "dividend" in tx_low:
        return "Dividend"
    return tx


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", "").strip())
    except ValueError:
        return None


def _extract_text_pages(pdf_bytes: bytes) -> list[str]:
    pages: list[str] = []
    with pdfplumber.open(io_bytes := __import__("io").BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    io_bytes.close()
    return pages


def _is_probable_fund_name(line: str) -> bool:
    cleaned = re.sub(r"\s+", " ", line).strip()
    if not cleaned:
        return False
    if cleaned.upper() in HEADER_BLOCKLIST:
        return False
    if cleaned.startswith("Folio No:") or cleaned.startswith("Date "):
        return False
    if cleaned.startswith("Fund Name Invested"):
        return False
    if re.search(r"\d{2}-[A-Za-z]{3}-\d{4}", cleaned):
        return False
    return bool(FUND_HEADER.match(cleaned))


def _new_fund(name: str) -> dict:
    return {
        "fund_name": re.sub(r"\s+", " ", name).strip(),
        "scheme_code": None,
        "transactions": [],
        "closing_units": None,
        "closing_nav": None,
        "market_value": None,
    }


def _parse_with_regex(text: str) -> list[dict]:
    text = text.replace("Market Val\nue", "Market Value")
    text = text.replace("Market Va\nlue", "Market Value")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    funds: list[dict] = []
    current: dict | None = None

    for line in lines:
        if PORTFOLIO_SUMMARY.match(line):
            break

        if _is_probable_fund_name(line):
            if current:
                funds.append(current)
            current = _new_fund(line)
            continue

        if current is None:
            continue

        code_match = SCHEME_CODE.search(line)
        if code_match and not current["scheme_code"]:
            current["scheme_code"] = code_match.group(1)

        tx_match = TRANSACTION.match(line)
        if tx_match:
            units = _to_float(tx_match.group("units"))
            nav = _to_float(tx_match.group("nav"))
            amt = _to_float(tx_match.group("amount"))
            if units is not None and nav is not None and amt is not None:
                current["transactions"].append(
                    {
                        "date": tx_match.group("date"),
                        "type": _normalize_tx_type(tx_match.group("type")),
                        "units": units,
                        "nav": nav,
                        "amount": amt,
                    }
                )

        closing_match = CLOSING_LINE.search(line)
        if closing_match:
            current["closing_units"] = _to_float(closing_match.group("units"))
            current["market_value"] = _to_float(closing_match.group("market"))
            nav_match = NAV_IN_CLOSING.search(line)
            if nav_match:
                current["closing_nav"] = _to_float(nav_match.group(1))
            continue

    if current:
        funds.append(current)

    return [f for f in funds if f["transactions"] or f["closing_units"] or f["market_value"]]


def _fallback_line_parse(text: str) -> list[dict]:
    text = text.replace("Market Val\nue", "Market Value")
    text = text.replace("Market Va\nlue", "Market Value")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    funds: list[dict] = []
    current: dict | None = None

    date_prefix = re.compile(r"^\d{2}-[A-Za-z]{3}-\d{4}")

    for line in lines:
        if PORTFOLIO_SUMMARY.match(line):
            break

        if _is_probable_fund_name(line):
            if current:
                funds.append(current)
            current = _new_fund(line)
            continue

        if current is None:
            continue

        if date_prefix.match(line):
            parts = re.split(r"\s+", line)
            if len(parts) >= 6:
                date = parts[0]
                amount = _to_float(parts[-2])
                nav = _to_float(parts[-3])
                units = _to_float(parts[-4])
                tx_type = " ".join(parts[1:-4]) if len(parts) > 5 else "Transaction"
                if amount is not None and nav is not None and units is not None:
                    current["transactions"].append(
                        {
                            "date": date,
                            "type": _normalize_tx_type(tx_type),
                            "units": units,
                            "nav": nav,
                            "amount": amount,
                        }
                    )

        closing_match = CLOSING_LINE.search(line)
        if closing_match:
            current["closing_units"] = _to_float(closing_match.group("units"))
            current["market_value"] = _to_float(closing_match.group("market"))
            nav_match = NAV_IN_CLOSING.search(line)
            if nav_match:
                current["closing_nav"] = _to_float(nav_match.group(1))

    if current:
        funds.append(current)

    return [f for f in funds if f["transactions"] or f["closing_units"] or f["market_value"]]


def parse_cams_pdf(pdf_bytes: bytes) -> list[dict]:
    pages = _extract_text_pages(pdf_bytes)
    full_text = "\n".join(pages)

    funds = _parse_with_regex(full_text)
    if funds:
        return funds

    return _fallback_line_parse(full_text)

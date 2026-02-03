"""LLM-based financial data extraction from SEC EDGAR filings."""

import json
import os
from dataclasses import dataclass, field, asdict
from anthropic import Anthropic

from src.fetchers.sec_edgar import (
    SECFinancialData,
    lookup_cik,
    fetch_company_facts,
    get_available_concepts,
    extract_facts,
    get_annual_facts,
)
from src.calculators.metrics import FinancialMetrics
from src.calculators.ratios import FinancialRatios


@dataclass
class ExtractionResult:
    """Result of LLM-based financial data extraction."""
    metrics: FinancialMetrics
    ratios: FinancialRatios
    fiscal_year_end: str  # e.g., "2024-12-31"
    fiscal_year_end_prior: str  # e.g., "2023-12-31"
    company_name: str
    ticker: str
    notes: list[str] = field(default_factory=list)  # LLM's notes about the extraction
    warnings: list[str] = field(default_factory=list)  # Any data quality concerns


# Keywords that indicate relevant financial concepts
RELEVANT_KEYWORDS = {
    # Income statement
    "revenue", "sales", "income", "profit", "loss", "expense", "cost",
    "margin", "ebitda", "earnings", "interest", "depreciation", "amortization",
    "gross", "operating", "tax", "dividend",
    # Balance sheet
    "asset", "liability", "equity", "debt", "cash", "receivable", "payable",
    "inventory", "current", "goodwill", "intangible", "capital", "stock",
    "retained", "treasury", "working",
    # Cash flow
    "cashflow", "flow",
    # Ratios/returns
    "return", "ratio",
}


def _is_relevant_concept(concept_name: str, label: str | None) -> bool:
    """Check if a concept is relevant for financial analysis."""
    text = (concept_name + " " + (label or "")).lower()
    return any(kw in text for kw in RELEVANT_KEYWORDS)


def _build_concept_summary(raw_data: dict, taxonomy: str = "us-gaap", min_year: int = 2022) -> str:
    """
    Build a summary of available XBRL concepts with their recent values.
    This is what we send to the LLM for interpretation.
    Filters to only financially relevant concepts with recent data to reduce token usage.
    """
    lines = []
    taxonomy_data = raw_data.get("facts", {}).get(taxonomy, {})
    included_count = 0

    for concept_name, concept_data in taxonomy_data.items():
        label = concept_data.get("label", concept_name)

        # Filter to relevant concepts only
        if not _is_relevant_concept(concept_name, label):
            continue

        # Get recent annual values (USD only for monetary, others for ratios)
        for unit_type, entries in concept_data.get("units", {}).items():
            # Filter for 10-K filings
            annual_entries = [
                e for e in entries
                if e.get("form") == "10-K"
            ]
            if not annual_entries:
                continue

            # Sort by end date descending
            annual_entries.sort(key=lambda x: x.get("end", ""), reverse=True)

            # Get most recent 2 values only, but skip if data is too old
            recent = []
            seen_ends = set()
            for e in annual_entries:
                end = e.get("end", "")
                if not end:
                    continue

                # Skip if data is older than min_year
                try:
                    year = int(end[:4])
                    if year < min_year:
                        continue
                except (ValueError, IndexError):
                    continue

                if end not in seen_ends:
                    seen_ends.add(end)
                    val = e.get("val", 0)
                    start = e.get("start", "")
                    period = f"{start} to {end}" if start else f"as of {end}"
                    if isinstance(val, (int, float)):
                        recent.append(f"{period}: {val:,.0f}")
                    else:
                        recent.append(f"{period}: {val}")
                    if len(recent) >= 2:
                        break

            if recent:
                lines.append(f"\n## {concept_name}")
                lines.append(f"Label: {label}")
                lines.append(f"Unit: {unit_type}")
                lines.append("Values:")
                for r in recent:
                    lines.append(f"  - {r}")
                included_count += 1

    lines.insert(0, f"# Available Financial Concepts ({included_count} relevant concepts)\n")
    return "\n".join(lines)


def _get_extraction_prompt(company_name: str, ticker: str, concept_summary: str) -> str:
    """Build the prompt for the LLM to extract financial data."""
    return f"""You are a financial analyst extracting data from SEC EDGAR XBRL filings for {company_name} ({ticker}).

Below is a list of available XBRL concepts with their recent annual values. Your task is to:

1. Identify the correct concepts for each required metric
2. Extract values for the two most recent fiscal years
3. Calculate derived metrics (gross profit, EBITDA, margins, ratios)
4. Validate that the numbers make sense (e.g., Assets ≈ Liabilities + Equity)
5. Note any concerns or data quality issues

## Available XBRL Concepts:
{concept_summary}

## Required Output

Return a JSON object with this exact structure:

```json
{{
  "fiscal_year_end": "YYYY-MM-DD",
  "fiscal_year_end_prior": "YYYY-MM-DD",

  "metrics": {{
    "tangible_net_worth": <number in USD>,
    "tangible_net_worth_prior": <number>,
    "cash_balance": <number>,
    "cash_balance_prior": <number>,
    "top_line_revenue": <number>,
    "top_line_revenue_prior": <number>,
    "gross_profit": <number>,
    "gross_profit_prior": <number>,
    "gross_profit_margin": <decimal 0-1>,
    "gross_profit_margin_prior": <decimal>,
    "operating_income": <number>,
    "operating_income_prior": <number>,
    "operating_income_margin": <decimal>,
    "operating_income_margin_prior": <decimal>,
    "ebitda": <number>,
    "ebitda_prior": <number>,
    "ebitda_margin": <decimal>,
    "ebitda_margin_prior": <decimal>,
    "adjusted_ebitda": <number or null if not calculable>,
    "adjusted_ebitda_prior": <number or null>,
    "adjusted_ebitda_margin": <decimal or null>,
    "adjusted_ebitda_margin_prior": <decimal or null>,
    "net_income": <number>,
    "net_income_prior": <number>,
    "net_income_margin": <decimal>,
    "net_income_margin_prior": <decimal>
  }},

  "ratios": {{
    "current_ratio": <decimal>,
    "current_ratio_prior": <decimal>,
    "cash_ratio": <decimal>,
    "cash_ratio_prior": <decimal>,
    "debt_to_equity": <decimal>,
    "debt_to_equity_prior": <decimal>,
    "ebitda_interest_coverage": <decimal or null>,
    "ebitda_interest_coverage_prior": <decimal or null>,
    "net_debt_to_ebitda": <decimal>,
    "net_debt_to_ebitda_prior": <decimal>,
    "net_debt_to_adj_ebitda": <decimal or null>,
    "net_debt_to_adj_ebitda_prior": <decimal or null>,
    "days_sales_outstanding": <decimal>,
    "days_sales_outstanding_prior": <decimal>,
    "working_capital": <number>,
    "working_capital_prior": <number>,
    "return_on_assets": <decimal>,
    "return_on_assets_prior": <decimal>,
    "return_on_equity": <decimal>,
    "return_on_equity_prior": <decimal>
  }},

  "extraction_notes": [
    "Note about which concepts were used for each metric",
    "Note about any calculations performed"
  ],

  "warnings": [
    "Any data quality concerns",
    "Missing data that had to be estimated or omitted"
  ]
}}
```

## Calculation Guidelines:

- **Tangible Net Worth** = Stockholders Equity - Intangible Assets - Goodwill
- **Gross Profit** = Revenue - Cost of Revenue (if not directly reported)
- **EBITDA** = Operating Income + Depreciation & Amortization
- **Adjusted EBITDA** = EBITDA + Stock Compensation + Other non-cash items (if available)
- **Margins** = Metric / Revenue
- **Current Ratio** = Current Assets / Current Liabilities
- **Cash Ratio** = Cash / Current Liabilities
- **Debt-to-Equity** = Total Debt / Stockholders Equity
- **EBITDA Interest Coverage** = EBITDA / Interest Expense
- **Net Debt** = Total Debt - Cash
- **Days Sales Outstanding** = (Accounts Receivable / Revenue) × 365
- **Working Capital** = Current Assets - Current Liabilities
- **Return on Assets** = Net Income / Total Assets
- **Return on Equity** = Net Income / Stockholders Equity

## Important:
- Use the MOST RECENT fiscal year as "current" and the one before as "prior"
- All monetary values should be in USD (not millions or billions - actual values)
- If a metric cannot be calculated due to missing data, use null and add a warning
- Double-check that balance sheet items balance (Assets ≈ Liabilities + Equity within 1%)

Return ONLY the JSON object, no additional text."""


def extract_financial_data(ticker: str) -> ExtractionResult | None:
    """
    Extract financial data from SEC EDGAR using LLM interpretation.

    Args:
        ticker: Stock ticker symbol

    Returns:
        ExtractionResult with metrics, ratios, and notes, or None if extraction fails
    """
    # Step 1: Look up company and fetch raw data
    company = lookup_cik(ticker)
    if not company:
        return None

    raw_data = fetch_company_facts(company.cik)

    # Step 2: Build concept summary for LLM
    concept_summary = _build_concept_summary(raw_data)

    # Step 3: Call LLM for extraction
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = _get_extraction_prompt(company.name, ticker, concept_summary)

    message = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Step 4: Parse JSON response
    # Handle potential markdown code blocks
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    try:
        data = json.loads(response_text.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}")
        print(f"Response was: {response_text[:500]}...")
        return None

    # Step 5: Convert to dataclasses
    metrics_data = data.get("metrics", {})
    ratios_data = data.get("ratios", {})

    # Handle null values by converting to 0.0
    def safe_float(val):
        return float(val) if val is not None else 0.0

    metrics = FinancialMetrics(
        tangible_net_worth=safe_float(metrics_data.get("tangible_net_worth")),
        tangible_net_worth_prior=safe_float(metrics_data.get("tangible_net_worth_prior")),
        cash_balance=safe_float(metrics_data.get("cash_balance")),
        cash_balance_prior=safe_float(metrics_data.get("cash_balance_prior")),
        top_line_revenue=safe_float(metrics_data.get("top_line_revenue")),
        top_line_revenue_prior=safe_float(metrics_data.get("top_line_revenue_prior")),
        gross_profit=safe_float(metrics_data.get("gross_profit")),
        gross_profit_prior=safe_float(metrics_data.get("gross_profit_prior")),
        gross_profit_margin=safe_float(metrics_data.get("gross_profit_margin")),
        gross_profit_margin_prior=safe_float(metrics_data.get("gross_profit_margin_prior")),
        operating_income=safe_float(metrics_data.get("operating_income")),
        operating_income_prior=safe_float(metrics_data.get("operating_income_prior")),
        operating_income_margin=safe_float(metrics_data.get("operating_income_margin")),
        operating_income_margin_prior=safe_float(metrics_data.get("operating_income_margin_prior")),
        ebitda=safe_float(metrics_data.get("ebitda")),
        ebitda_prior=safe_float(metrics_data.get("ebitda_prior")),
        ebitda_margin=safe_float(metrics_data.get("ebitda_margin")),
        ebitda_margin_prior=safe_float(metrics_data.get("ebitda_margin_prior")),
        adjusted_ebitda=safe_float(metrics_data.get("adjusted_ebitda")),
        adjusted_ebitda_prior=safe_float(metrics_data.get("adjusted_ebitda_prior")),
        adjusted_ebitda_margin=safe_float(metrics_data.get("adjusted_ebitda_margin")),
        adjusted_ebitda_margin_prior=safe_float(metrics_data.get("adjusted_ebitda_margin_prior")),
        net_income=safe_float(metrics_data.get("net_income")),
        net_income_prior=safe_float(metrics_data.get("net_income_prior")),
        net_income_margin=safe_float(metrics_data.get("net_income_margin")),
        net_income_margin_prior=safe_float(metrics_data.get("net_income_margin_prior")),
    )

    ratios = FinancialRatios(
        current_ratio=safe_float(ratios_data.get("current_ratio")),
        current_ratio_prior=safe_float(ratios_data.get("current_ratio_prior")),
        cash_ratio=safe_float(ratios_data.get("cash_ratio")),
        cash_ratio_prior=safe_float(ratios_data.get("cash_ratio_prior")),
        debt_to_equity=safe_float(ratios_data.get("debt_to_equity")),
        debt_to_equity_prior=safe_float(ratios_data.get("debt_to_equity_prior")),
        ebitda_interest_coverage=safe_float(ratios_data.get("ebitda_interest_coverage")),
        ebitda_interest_coverage_prior=safe_float(ratios_data.get("ebitda_interest_coverage_prior")),
        net_debt_to_ebitda=safe_float(ratios_data.get("net_debt_to_ebitda")),
        net_debt_to_ebitda_prior=safe_float(ratios_data.get("net_debt_to_ebitda_prior")),
        net_debt_to_adj_ebitda=safe_float(ratios_data.get("net_debt_to_adj_ebitda")),
        net_debt_to_adj_ebitda_prior=safe_float(ratios_data.get("net_debt_to_adj_ebitda_prior")),
        days_sales_outstanding=safe_float(ratios_data.get("days_sales_outstanding")),
        days_sales_outstanding_prior=safe_float(ratios_data.get("days_sales_outstanding_prior")),
        working_capital=safe_float(ratios_data.get("working_capital")),
        working_capital_prior=safe_float(ratios_data.get("working_capital_prior")),
        return_on_assets=safe_float(ratios_data.get("return_on_assets")),
        return_on_assets_prior=safe_float(ratios_data.get("return_on_assets_prior")),
        return_on_equity=safe_float(ratios_data.get("return_on_equity")),
        return_on_equity_prior=safe_float(ratios_data.get("return_on_equity_prior")),
    )

    return ExtractionResult(
        metrics=metrics,
        ratios=ratios,
        fiscal_year_end=data.get("fiscal_year_end", ""),
        fiscal_year_end_prior=data.get("fiscal_year_end_prior", ""),
        company_name=company.name,
        ticker=ticker,
        notes=data.get("extraction_notes", []),
        warnings=data.get("warnings", []),
    )


def print_extraction_result(result: ExtractionResult) -> None:
    """Print a formatted summary of the extraction result."""
    print(f"\n{'='*70}")
    print(f"Financial Data Extraction: {result.company_name} ({result.ticker})")
    print(f"Fiscal Years: {result.fiscal_year_end} vs {result.fiscal_year_end_prior}")
    print(f"{'='*70}\n")

    # Metrics
    m = result.metrics
    print("FINANCIAL METRICS")
    print("-" * 50)
    print(f"{'Metric':<30} {'Current':>15} {'Prior':>15}")
    print("-" * 50)
    print(f"{'Revenue':<30} ${m.top_line_revenue/1e9:>13.1f}B ${m.top_line_revenue_prior/1e9:>13.1f}B")
    print(f"{'Gross Profit':<30} ${m.gross_profit/1e9:>13.1f}B ${m.gross_profit_prior/1e9:>13.1f}B")
    print(f"{'Gross Margin':<30} {m.gross_profit_margin:>14.1%} {m.gross_profit_margin_prior:>14.1%}")
    print(f"{'Operating Income':<30} ${m.operating_income/1e9:>13.1f}B ${m.operating_income_prior/1e9:>13.1f}B")
    print(f"{'Operating Margin':<30} {m.operating_income_margin:>14.1%} {m.operating_income_margin_prior:>14.1%}")
    print(f"{'EBITDA':<30} ${m.ebitda/1e9:>13.1f}B ${m.ebitda_prior/1e9:>13.1f}B")
    print(f"{'EBITDA Margin':<30} {m.ebitda_margin:>14.1%} {m.ebitda_margin_prior:>14.1%}")
    print(f"{'Net Income':<30} ${m.net_income/1e9:>13.1f}B ${m.net_income_prior/1e9:>13.1f}B")
    print(f"{'Net Margin':<30} {m.net_income_margin:>14.1%} {m.net_income_margin_prior:>14.1%}")
    print(f"{'Cash Balance':<30} ${m.cash_balance/1e9:>13.1f}B ${m.cash_balance_prior/1e9:>13.1f}B")
    print(f"{'Tangible Net Worth':<30} ${m.tangible_net_worth/1e9:>13.1f}B ${m.tangible_net_worth_prior/1e9:>13.1f}B")

    # Ratios
    r = result.ratios
    print(f"\nFINANCIAL RATIOS")
    print("-" * 50)
    print(f"{'Ratio':<30} {'Current':>15} {'Prior':>15}")
    print("-" * 50)
    print(f"{'Current Ratio':<30} {r.current_ratio:>15.2f}x {r.current_ratio_prior:>14.2f}x")
    print(f"{'Cash Ratio':<30} {r.cash_ratio:>15.2f}x {r.cash_ratio_prior:>14.2f}x")
    print(f"{'Debt-to-Equity':<30} {r.debt_to_equity:>15.2f}x {r.debt_to_equity_prior:>14.2f}x")
    print(f"{'EBITDA Interest Coverage':<30} {r.ebitda_interest_coverage:>15.2f}x {r.ebitda_interest_coverage_prior:>14.2f}x")
    print(f"{'Net Debt / EBITDA':<30} {r.net_debt_to_ebitda:>15.2f}x {r.net_debt_to_ebitda_prior:>14.2f}x")
    print(f"{'Days Sales Outstanding':<30} {r.days_sales_outstanding:>15.1f} {r.days_sales_outstanding_prior:>14.1f}")
    print(f"{'Working Capital':<30} ${r.working_capital/1e9:>13.1f}B ${r.working_capital_prior/1e9:>13.1f}B")
    print(f"{'Return on Assets':<30} {r.return_on_assets:>14.1%} {r.return_on_assets_prior:>14.1%}")
    print(f"{'Return on Equity':<30} {r.return_on_equity:>14.1%} {r.return_on_equity_prior:>14.1%}")

    # Notes and warnings
    if result.notes:
        print(f"\nEXTRACTION NOTES")
        print("-" * 50)
        for note in result.notes:
            print(f"  • {note}")

    if result.warnings:
        print(f"\nWARNINGS")
        print("-" * 50)
        for warning in result.warnings:
            print(f"  ⚠ {warning}")

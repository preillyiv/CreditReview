"""
LLM-based concept mapper for XBRL data.

This module uses an LLM to identify which XBRL concepts correspond to required
financial metrics. It performs NO calculations - only concept mapping.

The flow is:
1. Fetch raw XBRL data from SEC EDGAR
2. LLM identifies which concepts map to which metrics
3. Python code extracts the actual values (see value_extractor.py)
4. Python code performs all calculations (see calculators/)
"""

import json
import os
from dataclasses import dataclass
from anthropic import Anthropic

from src.fetchers.sec_edgar import (
    lookup_cik,
    fetch_company_facts,
)
from src.models.extraction import (
    REQUIRED_BASE_METRICS,
    METRIC_DISPLAY_NAMES,
    ConceptMapping,
)


@dataclass
class ConceptMappingResult:
    """Result of LLM concept mapping."""
    # Mapped metrics: metric_key -> ConceptMapping
    mapped: dict[str, ConceptMapping]

    # Unmapped but notable: list of (concept, label, current_value, prior_value, note)
    unmapped_but_notable: list[dict]

    # Not found metrics: metric_key -> note
    not_found: dict[str, str]

    # Fiscal year info determined by LLM
    fiscal_year_end: str
    fiscal_year_end_prior: str

    # LLM metadata
    llm_notes: list[str]
    llm_warnings: list[str]


def _build_concept_summary_for_mapping(raw_data: dict, taxonomy: str = "us-gaap", min_year: int = 2022) -> str:
    """
    Build a summary of available XBRL concepts with their recent values.
    This is what we send to the LLM for concept mapping.
    Filters to only financially relevant concepts with recent 10-K data.
    """
    lines = []
    taxonomy_data = raw_data.get("facts", {}).get(taxonomy, {})
    included_count = 0

    for concept_name, concept_data in taxonomy_data.items():
        label = concept_data.get("label", concept_name)

        # Get recent annual values
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


def _get_concept_mapping_prompt(company_name: str, ticker: str, concept_summary: str) -> str:
    """Build the prompt for the LLM to map XBRL concepts to required metrics."""

    required_metrics_list = "\n".join([
        f"- {key}: {METRIC_DISPLAY_NAMES.get(key, key)}"
        for key in REQUIRED_BASE_METRICS
    ])

    return f"""You are a financial analyst mapping XBRL concepts from SEC EDGAR filings for {company_name} ({ticker}).

Your task is to identify which XBRL concept BEST represents each required metric.

**IMPORTANT: DO NOT perform any calculations. Just map concepts to metrics.**

## Available XBRL Concepts:
{concept_summary}

## Required Metrics to Map:
{required_metrics_list}

## Your Task:

For each required metric, identify:
1. The XBRL concept that best represents it
2. Your confidence in the mapping (0.0 to 1.0)
3. Brief reasoning for your choice
4. Where to find it in the SEC filing - be SPECIFIC. Examples:
   - "Consolidated Statements of Operations" (not just "Income Statement")
   - "Consolidated Balance Sheets"
   - "Notes to Financial Statements > Note 12: Restructuring and Other"
   - "Notes to Financial Statements > Stock-Based Compensation"
   Use the actual section/tab names from SEC filings, not generic terms.

Also identify:
- XBRL concepts that weren't mapped but might be relevant (e.g., unusual items, one-time charges) - include the specific location
- Required metrics that have no corresponding XBRL concept

## Return JSON in this exact format:

```json
{{
  "fiscal_year_end": "YYYY-MM-DD",
  "fiscal_year_end_prior": "YYYY-MM-DD",

  "mapped": {{
    "revenue": {{
      "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
      "confidence": 0.95,
      "reasoning": "This is the ASC 606 compliant revenue tag used by this company",
      "statement": "Consolidated Statements of Operations"
    }},
    "cost_of_revenue": {{
      "concept": "CostOfRevenue",
      "confidence": 0.90,
      "reasoning": "Direct cost of revenue concept",
      "statement": "Consolidated Statements of Operations"
    }},
    "stock_compensation": {{
      "concept": "AllocatedShareBasedCompensationExpense",
      "confidence": 0.85,
      "reasoning": "Total stock-based compensation expense",
      "statement": "Notes to Financial Statements > Stock-Based Compensation"
    }}
  }},

  "unmapped_but_notable": [
    {{
      "concept": "RestructuringCharges",
      "label": "Restructuring Charges",
      "value_current": 150000000,
      "value_prior": 50000000,
      "note": "Significant restructuring charges that may affect EBITDA adjustments",
      "statement": "Notes to Financial Statements > Restructuring and Other"
    }}
  ],

  "not_found": {{
    "stock_compensation": "No StockBasedCompensation or ShareBasedCompensation concept found in filings"
  }},

  "notes": [
    "Company uses ASC 606 revenue recognition tags",
    "Two different debt concepts found - used the more comprehensive one"
  ],

  "warnings": [
    "No adjusted EBITDA data available - will need manual input",
    "Intangible assets concept includes goodwill at this company"
  ]
}}
```

## Guidelines:

1. **Be specific**: Use the exact XBRL concept name (e.g., "RevenueFromContractWithCustomerExcludingAssessedTax", not just "Revenue")

2. **Prefer precision**: If multiple concepts could work, choose the one that most precisely matches the metric definition

3. **Note alternatives**: If you're torn between concepts, mention the alternative in your reasoning

4. **Fiscal years**: Determine the two most recent fiscal year ends from the data (use "as of" dates for balance sheet items, period end dates for income statement items)

5. **Common mappings**:
   - revenue → RevenueFromContractWithCustomerExcludingAssessedTax, Revenues, SalesRevenueNet
   - net_income → NetIncomeLoss, ProfitLoss
   - total_assets → Assets
   - total_liabilities → Liabilities
   - stockholders_equity → StockholdersEquity
   - cash → CashAndCashEquivalentsAtCarryingValue
   - total_debt → LongTermDebtAndCapitalLeaseObligations, DebtLongtermAndShorttermCombinedAmount
   - depreciation_amortization → DepreciationDepletionAndAmortization
   - stock_compensation → AllocatedShareBasedCompensationExpense, ShareBasedCompensation

6. **Notable unmapped**: Include concepts that might be relevant for:
   - Adjusted EBITDA calculations (restructuring, impairments, one-time items)
   - Risk assessment (litigation, contingencies)
   - Unusual items that could affect analysis

Return ONLY the JSON object, no additional text."""


def map_concepts(ticker: str) -> ConceptMappingResult | None:
    """
    Use LLM to map XBRL concepts to required financial metrics.

    This function ONLY performs concept mapping - no value extraction or calculations.

    Args:
        ticker: Stock ticker symbol

    Returns:
        ConceptMappingResult with mappings, or None if mapping fails
    """
    # Step 1: Look up company and fetch raw data
    company = lookup_cik(ticker)
    if not company:
        return None

    raw_data = fetch_company_facts(company.cik)

    # Step 2: Build concept summary for LLM
    concept_summary = _build_concept_summary_for_mapping(raw_data)

    # Step 3: Call LLM for concept mapping
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = _get_concept_mapping_prompt(company.name, ticker, concept_summary)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",  # Use Sonnet for faster, cheaper mapping
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Step 4: Parse JSON response
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

    # Step 5: Convert to result object
    mapped = {}
    for metric_key, mapping_data in data.get("mapped", {}).items():
        mapped[metric_key] = ConceptMapping(
            xbrl_concept=mapping_data.get("concept", ""),
            confidence=mapping_data.get("confidence", 0.0),
            reasoning=mapping_data.get("reasoning", ""),
            statement=mapping_data.get("statement", ""),
        )

    return ConceptMappingResult(
        mapped=mapped,
        unmapped_but_notable=data.get("unmapped_but_notable", []),
        not_found=data.get("not_found", {}),
        fiscal_year_end=data.get("fiscal_year_end", ""),
        fiscal_year_end_prior=data.get("fiscal_year_end_prior", ""),
        llm_notes=data.get("notes", []),
        llm_warnings=data.get("warnings", []),
    )


def map_concepts_with_raw_data(
    company_name: str,
    ticker: str,
    cik: str,
    raw_data: dict,
    model: str = "claude-opus-4-5-20251101"
) -> ConceptMappingResult | None:
    """
    Use LLM to map XBRL concepts to required financial metrics.
    This version accepts pre-fetched raw data.

    Args:
        company_name: Company name
        ticker: Stock ticker symbol
        cik: SEC CIK number
        raw_data: Pre-fetched raw SEC data

    Returns:
        ConceptMappingResult with mappings, or None if mapping fails
    """
    # Build concept summary for LLM
    concept_summary = _build_concept_summary_for_mapping(raw_data)

    # Call LLM for concept mapping
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = _get_concept_mapping_prompt(company_name, ticker, concept_summary)

    message = client.messages.create(
        model=model,
        max_tokens=8000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = message.content[0].text

    # Parse JSON response
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

    # Convert to result object
    mapped = {}
    for metric_key, mapping_data in data.get("mapped", {}).items():
        mapped[metric_key] = ConceptMapping(
            xbrl_concept=mapping_data.get("concept", ""),
            confidence=mapping_data.get("confidence", 0.0),
            reasoning=mapping_data.get("reasoning", ""),
            statement=mapping_data.get("statement", ""),
        )

    return ConceptMappingResult(
        mapped=mapped,
        unmapped_but_notable=data.get("unmapped_but_notable", []),
        not_found=data.get("not_found", {}),
        fiscal_year_end=data.get("fiscal_year_end", ""),
        fiscal_year_end_prior=data.get("fiscal_year_end_prior", ""),
        llm_notes=data.get("notes", []),
        llm_warnings=data.get("warnings", []),
    )


def print_mapping_result(result: ConceptMappingResult) -> None:
    """Print a formatted summary of the concept mapping result."""
    print(f"\n{'='*70}")
    print("CONCEPT MAPPING RESULT")
    print(f"Fiscal Years: {result.fiscal_year_end} vs {result.fiscal_year_end_prior}")
    print(f"{'='*70}\n")

    print("MAPPED METRICS")
    print("-" * 70)
    for metric_key, mapping in result.mapped.items():
        display_name = METRIC_DISPLAY_NAMES.get(metric_key, metric_key)
        print(f"\n{display_name} ({metric_key}):")
        print(f"  Concept: {mapping.xbrl_concept}")
        print(f"  Confidence: {mapping.confidence:.0%}")
        print(f"  Reasoning: {mapping.reasoning}")

    if result.not_found:
        print(f"\n{'='*70}")
        print("NOT FOUND METRICS")
        print("-" * 70)
        for metric_key, note in result.not_found.items():
            display_name = METRIC_DISPLAY_NAMES.get(metric_key, metric_key)
            print(f"\n{display_name} ({metric_key}):")
            print(f"  {note}")

    if result.unmapped_but_notable:
        print(f"\n{'='*70}")
        print("UNMAPPED BUT NOTABLE")
        print("-" * 70)
        for item in result.unmapped_but_notable:
            print(f"\n{item.get('concept', 'Unknown')}:")
            print(f"  Label: {item.get('label', '')}")
            print(f"  Current: {item.get('value_current', 0):,.0f}")
            print(f"  Prior: {item.get('value_prior', 0):,.0f}")
            print(f"  Note: {item.get('note', '')}")

    if result.llm_notes:
        print(f"\n{'='*70}")
        print("NOTES")
        print("-" * 70)
        for note in result.llm_notes:
            print(f"  • {note}")

    if result.llm_warnings:
        print(f"\n{'='*70}")
        print("WARNINGS")
        print("-" * 70)
        for warning in result.llm_warnings:
            print(f"  ⚠ {warning}")

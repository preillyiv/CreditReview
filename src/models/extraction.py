"""Data models for extraction sessions with source citations."""

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class SourceCitation:
    """
    Source citation for an extracted financial value.
    Links back to the original SEC filing for audit trail.
    """
    xbrl_concept: str        # e.g., "us-gaap:Revenues"
    xbrl_label: str          # Human-readable label from XBRL taxonomy
    filing_url: str          # Direct link to SEC filing
    accession_number: str    # SEC accession number (e.g., "0001018724-24-000015")
    filing_date: str         # Date filing was submitted (YYYY-MM-DD)
    form_type: str           # "10-K", "10-Q", etc.
    period_end: str          # End date of the reporting period (YYYY-MM-DD)
    raw_value: float         # The actual value from the filing
    statement: str = ""      # Which financial statement (e.g., "Income Statement", "Balance Sheet")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "xbrl_concept": self.xbrl_concept,
            "xbrl_label": self.xbrl_label,
            "filing_url": self.filing_url,
            "accession_number": self.accession_number,
            "filing_date": self.filing_date,
            "form_type": self.form_type,
            "period_end": self.period_end,
            "raw_value": self.raw_value,
            "statement": self.statement,
        }


@dataclass
class ConceptMapping:
    """
    LLM's mapping of an XBRL concept to a required metric.
    """
    xbrl_concept: str        # The XBRL concept name (e.g., "RevenueFromContractWithCustomerExcludingAssessedTax")
    confidence: float        # LLM's confidence in the mapping (0.0 - 1.0)
    reasoning: str           # Why the LLM chose this concept
    statement: str = ""      # Which financial statement (e.g., "Income Statement", "Balance Sheet")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "xbrl_concept": self.xbrl_concept,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "statement": self.statement,
        }


@dataclass
class ExtractedValue:
    """
    A single extracted financial value with its source citation.
    """
    metric_key: str          # Internal key (e.g., "revenue", "net_income")
    display_name: str        # Human-readable name (e.g., "Top Line Revenue")
    value: float             # The extracted value (current year)
    value_prior: float       # The extracted value (prior year)
    citation: SourceCitation | None  # Source citation (None if manually entered)
    citation_prior: SourceCitation | None  # Source citation for prior year
    llm_reasoning: str       # LLM's explanation of concept selection
    is_editable: bool = True  # Whether user can edit this value

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_key": self.metric_key,
            "display_name": self.display_name,
            "value": self.value,
            "value_prior": self.value_prior,
            "citation": self.citation.to_dict() if self.citation else None,
            "citation_prior": self.citation_prior.to_dict() if self.citation_prior else None,
            "llm_reasoning": self.llm_reasoning,
            "is_editable": self.is_editable,
        }


@dataclass
class UnmappedValue:
    """
    An XBRL concept that wasn't mapped to a required metric but may be notable.
    The LLM identified this as potentially relevant for the user to review.
    """
    xbrl_concept: str        # The XBRL concept name
    xbrl_label: str          # Human-readable label
    value_current: float     # Current year value
    value_prior: float       # Prior year value
    llm_note: str            # LLM's note about why this might be relevant
    citation: SourceCitation | None = None  # Source citation for current value
    citation_prior: SourceCitation | None = None  # Source citation for prior value

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "xbrl_concept": self.xbrl_concept,
            "xbrl_label": self.xbrl_label,
            "value_current": self.value_current,
            "value_prior": self.value_prior,
            "llm_note": self.llm_note,
            "citation": self.citation.to_dict() if self.citation else None,
            "citation_prior": self.citation_prior.to_dict() if self.citation_prior else None,
        }


@dataclass
class NotFoundMetric:
    """
    A required metric that couldn't be found in the XBRL data.
    """
    metric_key: str          # Internal key (e.g., "adjusted_ebitda")
    display_name: str        # Human-readable name
    llm_note: str            # Why it wasn't found / suggestions

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric_key": self.metric_key,
            "display_name": self.display_name,
            "llm_note": self.llm_note,
        }


@dataclass
class CalculationStep:
    """
    A single step in a calculation, for audit trail purposes.
    """
    metric: str              # The metric being calculated
    formula: str             # Human-readable formula (e.g., "EBITDA = Operating Income + D&A")
    formula_excel: str       # Excel formula reference (e.g., "=B5+B6")
    inputs: dict[str, float]  # Input values used in the calculation
    result: float            # The calculated result

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric": self.metric,
            "formula": self.formula,
            "formula_excel": self.formula_excel,
            "inputs": self.inputs,
            "result": self.result,
        }


@dataclass
class ExtractionSession:
    """
    Represents a complete extraction session.
    This is the main object passed between extraction, review, and calculation phases.
    """
    session_id: str
    ticker: str
    company_name: str
    cik: str                 # SEC CIK number
    fiscal_year_end: str     # e.g., "2024-12-31"
    fiscal_year_end_prior: str  # e.g., "2023-12-31"

    # Raw extracted values (before calculations)
    raw_values: dict[str, ExtractedValue] = field(default_factory=dict)

    # Values that weren't mapped but might be interesting
    unmapped_values: list[UnmappedValue] = field(default_factory=list)

    # Required metrics that couldn't be found
    not_found: list[NotFoundMetric] = field(default_factory=list)

    # Calculation audit trail (populated after approval)
    calculation_steps: list[CalculationStep] = field(default_factory=list)

    # Session state
    is_approved: bool = False
    approved_at: str | None = None  # ISO timestamp when approved

    # LLM metadata
    llm_model: str = ""
    llm_notes: list[str] = field(default_factory=list)
    llm_warnings: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, ticker: str, company_name: str, cik: str) -> "ExtractionSession":
        """Create a new extraction session with a generated ID."""
        return cls(
            session_id=str(uuid.uuid4()),
            ticker=ticker,
            company_name=company_name,
            cik=cik,
            fiscal_year_end="",
            fiscal_year_end_prior="",
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "cik": self.cik,
            "fiscal_year_end": self.fiscal_year_end,
            "fiscal_year_end_prior": self.fiscal_year_end_prior,
            "raw_values": {k: v.to_dict() for k, v in self.raw_values.items()},
            "unmapped_values": [v.to_dict() for v in self.unmapped_values],
            "not_found": [v.to_dict() for v in self.not_found],
            "calculation_steps": [s.to_dict() for s in self.calculation_steps],
            "is_approved": self.is_approved,
            "approved_at": self.approved_at,
            "llm_model": self.llm_model,
            "llm_notes": self.llm_notes,
            "llm_warnings": self.llm_warnings,
        }

    def get_raw_value(self, metric_key: str, prior: bool = False) -> float | None:
        """Get a raw value by metric key."""
        if metric_key not in self.raw_values:
            return None
        ev = self.raw_values[metric_key]
        return ev.value_prior if prior else ev.value

    def set_raw_value(self, metric_key: str, value: float, prior: bool = False) -> None:
        """Update a raw value (used for user edits)."""
        if metric_key in self.raw_values:
            ev = self.raw_values[metric_key]
            if prior:
                # Create new ExtractedValue with updated prior value
                self.raw_values[metric_key] = ExtractedValue(
                    metric_key=ev.metric_key,
                    display_name=ev.display_name,
                    value=ev.value,
                    value_prior=value,
                    citation=ev.citation,
                    citation_prior=ev.citation_prior,
                    llm_reasoning=ev.llm_reasoning,
                    is_editable=ev.is_editable,
                )
            else:
                self.raw_values[metric_key] = ExtractedValue(
                    metric_key=ev.metric_key,
                    display_name=ev.display_name,
                    value=value,
                    value_prior=ev.value_prior,
                    citation=ev.citation,
                    citation_prior=ev.citation_prior,
                    llm_reasoning=ev.llm_reasoning,
                    is_editable=ev.is_editable,
                )


# Display name mapping for metrics
METRIC_DISPLAY_NAMES = {
    # Base values (extracted from XBRL)
    "revenue": "Top Line Revenue",
    "cost_of_revenue": "Cost of Revenue",
    "gross_profit": "Gross Profit",
    "operating_income": "Operating Income",
    "depreciation_amortization": "Depreciation & Amortization",
    "interest_expense": "Interest Expense",
    "net_income": "Net Income",
    "total_assets": "Total Assets",
    "total_liabilities": "Total Liabilities",
    "stockholders_equity": "Stockholders' Equity",
    "current_assets": "Current Assets",
    "current_liabilities": "Current Liabilities",
    "cash": "Cash & Cash Equivalents",
    "total_debt": "Total Debt",
    "accounts_receivable": "Accounts Receivable",
    "intangible_assets": "Intangible Assets",
    "goodwill": "Goodwill",
    "stock_compensation": "Stock-Based Compensation",

    # Calculated metrics
    "tangible_net_worth": "Tangible Net Worth",
    "ebitda": "EBITDA",
    "adjusted_ebitda": "Adjusted EBITDA",
    "gross_margin": "Gross Profit Margin",
    "operating_margin": "Operating Income Margin",
    "ebitda_margin": "EBITDA Margin",
    "adjusted_ebitda_margin": "Adjusted EBITDA Margin",
    "net_margin": "Net Income Margin",

    # Ratios
    "current_ratio": "Current Ratio",
    "cash_ratio": "Cash Ratio",
    "debt_to_equity": "Debt-to-Equity Ratio",
    "ebitda_interest_coverage": "EBITDA Interest Coverage",
    "net_debt": "Net Debt",
    "net_debt_to_ebitda": "Net Debt / EBITDA",
    "net_debt_to_adj_ebitda": "Net Debt / Adj. EBITDA",
    "days_sales_outstanding": "Days Sales Outstanding",
    "working_capital": "Working Capital",
    "return_on_assets": "Return on Assets",
    "return_on_equity": "Return on Equity",
}


# Required base metrics that LLM should map from XBRL
REQUIRED_BASE_METRICS = [
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "operating_income",
    "depreciation_amortization",
    "interest_expense",
    "net_income",
    "total_assets",
    "total_liabilities",
    "stockholders_equity",
    "current_assets",
    "current_liabilities",
    "cash",
    "total_debt",
    "accounts_receivable",
    "intangible_assets",
    "goodwill",
    "stock_compensation",
]

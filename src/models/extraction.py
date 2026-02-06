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
    unit: str = "dollars"    # Unit of financial metrics (e.g., "millions", "thousands", "dollars")

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
    # === Income Statement ===
    "revenue": "Top Line Revenue",
    "cost_of_revenue": "Cost of Revenue",
    "gross_profit": "Gross Profit",
    "sga_expense": "Selling, General & Administrative",
    "rd_expense": "Research & Development",
    "depreciation_amortization": "Depreciation & Amortization",
    "other_operating_expense": "Other Operating Expenses",
    "total_operating_expenses": "Total Operating Expenses",
    "operating_income": "Operating Income",
    "interest_expense": "Interest Expense",
    "other_income_expense": "Other Income/Expense, Net",
    "income_before_tax": "Income Before Income Tax",
    "income_tax_expense": "Income Tax Expense",
    "net_income": "Net Income",
    "stock_compensation": "Stock-Based Compensation",

    # === Balance Sheet - Assets ===
    "cash": "Cash & Cash Equivalents",
    "short_term_investments": "Short-term Investments",
    "accounts_receivable": "Accounts Receivable",
    "inventories": "Inventories",
    "other_current_assets": "Other Current Assets",
    "current_assets": "Total Current Assets",
    "ppe_net": "Property, Plant & Equipment, Net",
    "goodwill": "Goodwill",
    "intangible_assets": "Intangible Assets",
    "other_noncurrent_assets": "Other Non-Current Assets",
    "total_assets": "Total Assets",

    # === Balance Sheet - Liabilities & Equity ===
    "accounts_payable": "Accounts Payable",
    "short_term_debt": "Short-term Debt",
    "accrued_liabilities": "Accrued Liabilities",
    "other_current_liabilities": "Other Current Liabilities",
    "current_liabilities": "Total Current Liabilities",
    "long_term_debt": "Long-term Debt",
    "other_noncurrent_liabilities": "Other Non-Current Liabilities",
    "total_liabilities": "Total Liabilities",
    "stockholders_equity": "Stockholders' Equity",
    "total_debt": "Total Debt",

    # === Cash Flow Statement ===
    "cf_net_income": "Net Income",
    "cf_depreciation_amortization": "Depreciation & Amortization",
    "cf_stock_compensation": "Stock-Based Compensation",
    "cf_working_capital_changes": "Changes in Working Capital",
    "cf_other_operating": "Other Operating Activities",
    "cash_from_operations": "Cash from Operations",
    "capital_expenditures": "Capital Expenditures",
    "acquisitions": "Acquisitions",
    "cf_other_investing": "Other Investing Activities",
    "cash_from_investing": "Cash from Investing",
    "debt_issuance_repayment": "Debt Issuance/Repayment, Net",
    "stock_repurchases": "Stock Repurchases",
    "dividends_paid": "Dividends Paid",
    "cf_other_financing": "Other Financing Activities",
    "cash_from_financing": "Cash from Financing",
    "net_change_in_cash": "Net Change in Cash",

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
    # Income Statement
    "revenue",
    "cost_of_revenue",
    "gross_profit",
    "sga_expense",
    "rd_expense",
    "depreciation_amortization",
    "other_operating_expense",
    "total_operating_expenses",
    "operating_income",
    "interest_expense",
    "other_income_expense",
    "income_before_tax",
    "income_tax_expense",
    "net_income",
    "stock_compensation",
    # Balance Sheet - Assets
    "cash",
    "short_term_investments",
    "accounts_receivable",
    "inventories",
    "other_current_assets",
    "current_assets",
    "ppe_net",
    "goodwill",
    "intangible_assets",
    "other_noncurrent_assets",
    "total_assets",
    # Balance Sheet - Liabilities & Equity
    "accounts_payable",
    "short_term_debt",
    "accrued_liabilities",
    "other_current_liabilities",
    "current_liabilities",
    "long_term_debt",
    "other_noncurrent_liabilities",
    "total_liabilities",
    "stockholders_equity",
    "total_debt",
    # Cash Flow Statement
    "cf_net_income",
    "cf_depreciation_amortization",
    "cf_stock_compensation",
    "cf_working_capital_changes",
    "cf_other_operating",
    "cash_from_operations",
    "capital_expenditures",
    "acquisitions",
    "cf_other_investing",
    "cash_from_investing",
    "debt_issuance_repayment",
    "stock_repurchases",
    "dividends_paid",
    "cf_other_financing",
    "cash_from_financing",
    "net_change_in_cash",
]


@dataclass
class StatementLineItem:
    """Metadata for rendering a single line item in a financial statement."""
    metric_key: str
    display_name: str
    statement: str        # "income_statement", "balance_sheet", "cash_flow"
    section: str          # e.g., "Current Assets", "Operating Activities", ""
    indent_level: int     # 0 = bold top-level, 1 = indented sub-item
    is_subtotal: bool
    is_bold: bool
    sort_order: int


# === Financial Statement Line Item Registries ===

INCOME_STATEMENT_ITEMS = [
    StatementLineItem("revenue", "Top Line Revenue", "income_statement", "", 0, False, True, 0),
    StatementLineItem("cost_of_revenue", "Cost of Revenue", "income_statement", "", 1, False, False, 1),
    StatementLineItem("gross_profit", "Gross Profit", "income_statement", "", 0, True, True, 2),
    StatementLineItem("sga_expense", "Selling, General & Administrative", "income_statement", "", 1, False, False, 3),
    StatementLineItem("rd_expense", "Research & Development", "income_statement", "", 1, False, False, 4),
    StatementLineItem("depreciation_amortization", "Depreciation & Amortization", "income_statement", "", 1, False, False, 5),
    StatementLineItem("other_operating_expense", "Other Operating Expenses", "income_statement", "", 1, False, False, 6),
    StatementLineItem("total_operating_expenses", "Total Operating Expenses", "income_statement", "", 0, True, True, 7),
    StatementLineItem("operating_income", "Operating Income", "income_statement", "", 0, True, True, 8),
    StatementLineItem("interest_expense", "Interest Expense", "income_statement", "", 1, False, False, 9),
    StatementLineItem("other_income_expense", "Other Income/Expense, Net", "income_statement", "", 1, False, False, 10),
    StatementLineItem("income_before_tax", "Income Before Income Tax", "income_statement", "", 0, True, True, 11),
    StatementLineItem("income_tax_expense", "Income Tax Expense", "income_statement", "", 1, False, False, 12),
    StatementLineItem("net_income", "Net Income", "income_statement", "", 0, True, True, 13),
    StatementLineItem("stock_compensation", "Stock-Based Compensation", "income_statement", "", 1, False, False, 14),
]

BALANCE_SHEET_ITEMS = [
    # Current Assets
    StatementLineItem("cash", "Cash & Cash Equivalents", "balance_sheet", "Current Assets", 1, False, False, 0),
    StatementLineItem("short_term_investments", "Short-term Investments", "balance_sheet", "Current Assets", 1, False, False, 1),
    StatementLineItem("accounts_receivable", "Accounts Receivable", "balance_sheet", "Current Assets", 1, False, False, 2),
    StatementLineItem("inventories", "Inventories", "balance_sheet", "Current Assets", 1, False, False, 3),
    StatementLineItem("other_current_assets", "Other Current Assets", "balance_sheet", "Current Assets", 1, False, False, 4),
    StatementLineItem("current_assets", "Total Current Assets", "balance_sheet", "Current Assets", 0, True, True, 5),
    # Non-Current Assets
    StatementLineItem("ppe_net", "Property, Plant & Equipment, Net", "balance_sheet", "Non-Current Assets", 1, False, False, 6),
    StatementLineItem("goodwill", "Goodwill", "balance_sheet", "Non-Current Assets", 1, False, False, 7),
    StatementLineItem("intangible_assets", "Intangible Assets", "balance_sheet", "Non-Current Assets", 1, False, False, 8),
    StatementLineItem("other_noncurrent_assets", "Other Non-Current Assets", "balance_sheet", "Non-Current Assets", 1, False, False, 9),
    StatementLineItem("total_assets", "Total Assets", "balance_sheet", "", 0, True, True, 10),
    # Current Liabilities
    StatementLineItem("accounts_payable", "Accounts Payable", "balance_sheet", "Current Liabilities", 1, False, False, 11),
    StatementLineItem("short_term_debt", "Short-term Debt", "balance_sheet", "Current Liabilities", 1, False, False, 12),
    StatementLineItem("accrued_liabilities", "Accrued Liabilities", "balance_sheet", "Current Liabilities", 1, False, False, 13),
    StatementLineItem("other_current_liabilities", "Other Current Liabilities", "balance_sheet", "Current Liabilities", 1, False, False, 14),
    StatementLineItem("current_liabilities", "Total Current Liabilities", "balance_sheet", "Current Liabilities", 0, True, True, 15),
    # Non-Current Liabilities
    StatementLineItem("long_term_debt", "Long-term Debt", "balance_sheet", "Non-Current Liabilities", 1, False, False, 16),
    StatementLineItem("other_noncurrent_liabilities", "Other Non-Current Liabilities", "balance_sheet", "Non-Current Liabilities", 1, False, False, 17),
    StatementLineItem("total_liabilities", "Total Liabilities", "balance_sheet", "", 0, True, True, 18),
    # Equity
    StatementLineItem("stockholders_equity", "Stockholders' Equity", "balance_sheet", "Equity", 0, True, True, 19),
]

CASH_FLOW_ITEMS = [
    # Operating Activities
    StatementLineItem("cf_net_income", "Net Income", "cash_flow", "Operating Activities", 1, False, False, 0),
    StatementLineItem("cf_depreciation_amortization", "Depreciation & Amortization", "cash_flow", "Operating Activities", 1, False, False, 1),
    StatementLineItem("cf_stock_compensation", "Stock-Based Compensation", "cash_flow", "Operating Activities", 1, False, False, 2),
    StatementLineItem("cf_working_capital_changes", "Changes in Working Capital", "cash_flow", "Operating Activities", 1, False, False, 3),
    StatementLineItem("cf_other_operating", "Other Operating Activities", "cash_flow", "Operating Activities", 1, False, False, 4),
    StatementLineItem("cash_from_operations", "Cash from Operations", "cash_flow", "Operating Activities", 0, True, True, 5),
    # Investing Activities
    StatementLineItem("capital_expenditures", "Capital Expenditures", "cash_flow", "Investing Activities", 1, False, False, 6),
    StatementLineItem("acquisitions", "Acquisitions", "cash_flow", "Investing Activities", 1, False, False, 7),
    StatementLineItem("cf_other_investing", "Other Investing Activities", "cash_flow", "Investing Activities", 1, False, False, 8),
    StatementLineItem("cash_from_investing", "Cash from Investing", "cash_flow", "Investing Activities", 0, True, True, 9),
    # Financing Activities
    StatementLineItem("debt_issuance_repayment", "Debt Issuance/Repayment, Net", "cash_flow", "Financing Activities", 1, False, False, 10),
    StatementLineItem("stock_repurchases", "Stock Repurchases", "cash_flow", "Financing Activities", 1, False, False, 11),
    StatementLineItem("dividends_paid", "Dividends Paid", "cash_flow", "Financing Activities", 1, False, False, 12),
    StatementLineItem("cf_other_financing", "Other Financing Activities", "cash_flow", "Financing Activities", 1, False, False, 13),
    StatementLineItem("cash_from_financing", "Cash from Financing", "cash_flow", "Financing Activities", 0, True, True, 14),
    # Net Change
    StatementLineItem("net_change_in_cash", "Net Change in Cash", "cash_flow", "", 0, True, True, 15),
]

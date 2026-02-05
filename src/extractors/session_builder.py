"""
Shared session builder for both ticker and PDF extraction paths.

This module contains the anti-duplication layer that both extraction paths converge on.
Both ticker-based and PDF-based extraction normalize their results into NormalizedExtractionData,
which is then used to build an ExtractionSession via this shared builder.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List

from src.models.extraction import (
    ExtractionSession,
    ExtractedValue,
    SourceCitation,
    NotFoundMetric,
    METRIC_DISPLAY_NAMES,
)


@dataclass
class NormalizedMetric:
    """A single extracted metric, normalized from either XBRL or PDF."""
    metric_key: str              # e.g., "revenue"
    value: float                 # Current year
    value_prior: float           # Prior year
    source_description: str      # e.g., "us-gaap:Revenues" or "Page 66 of PDF"
    source_url: str              # SEC filing URL or empty for PDF
    reasoning: str               # LLM reasoning
    form_type: str               # "10-K"
    period_end: str              # "2024-12-31"
    period_end_prior: str        # "2023-12-31"
    unit: str = "dollars"        # Unit of the value (e.g., "millions", "thousands", "dollars")
    statement: str = ""          # Which financial statement (e.g., "Income Statement", "Balance Sheet")


@dataclass
class NormalizedExtractionData:
    """Normalized extraction result from either ticker or PDF path."""
    company_name: str
    ticker: str                  # May be empty for PDF uploads
    cik: str                     # May be empty for PDF uploads
    fiscal_year_end: str
    fiscal_year_end_prior: str
    metrics: Dict[str, NormalizedMetric]  # Keyed by metric_key
    unmapped_notes: List[str] = field(default_factory=list)  # Notable items not mapped
    not_found: List[str] = field(default_factory=list)  # Required metrics not found
    unit: str = "dollars"        # Unit of all financial metrics (e.g., "millions", "thousands", "dollars")
    llm_model: str = ""
    llm_notes: List[str] = field(default_factory=list)
    llm_warnings: List[str] = field(default_factory=list)


def build_extraction_session(data: NormalizedExtractionData) -> ExtractionSession:
    """
    Build an ExtractionSession from normalized data.
    Used by BOTH ticker and PDF extraction paths.

    This is the single point of convergence - ensures both paths create sessions identically.
    """
    session = ExtractionSession(
        session_id=str(uuid.uuid4()),
        ticker=data.ticker,
        company_name=data.company_name,
        cik=data.cik,
        fiscal_year_end=data.fiscal_year_end,
        fiscal_year_end_prior=data.fiscal_year_end_prior,
        unit=data.unit,  # Store the unit from normalized data
        llm_model=data.llm_model,
        llm_notes=data.llm_notes,
        llm_warnings=data.llm_warnings,
    )

    # Convert normalized metrics to ExtractedValue with citations
    for metric_key, norm_metric in data.metrics.items():
        # Use the statement field from NormalizedMetric (populated by each extraction path)
        # For SEC: contains "Income Statement", "Balance Sheet", etc.
        # For PDF: contains "Page X of PDF", etc.
        statement_field = norm_metric.statement

        citation = SourceCitation(
            xbrl_concept=norm_metric.source_description,
            xbrl_label=norm_metric.source_description,
            filing_url=norm_metric.source_url,
            accession_number="",
            filing_date="",
            form_type=norm_metric.form_type,
            period_end=norm_metric.period_end,
            raw_value=norm_metric.value,
            statement=statement_field,
        )

        citation_prior = SourceCitation(
            xbrl_concept=norm_metric.source_description,
            xbrl_label=norm_metric.source_description,
            filing_url=norm_metric.source_url,
            accession_number="",
            filing_date="",
            form_type=norm_metric.form_type,
            period_end=norm_metric.period_end_prior,
            raw_value=norm_metric.value_prior,
            statement=statement_field,
        )

        session.raw_values[metric_key] = ExtractedValue(
            metric_key=metric_key,
            display_name=METRIC_DISPLAY_NAMES.get(metric_key, metric_key),
            value=norm_metric.value,
            value_prior=norm_metric.value_prior,
            citation=citation,
            citation_prior=citation_prior,
            llm_reasoning=norm_metric.reasoning,
            is_editable=True,
        )

    # Handle not found metrics
    for metric_key in data.not_found:
        session.not_found.append(NotFoundMetric(
            metric_key=metric_key,
            display_name=METRIC_DISPLAY_NAMES.get(metric_key, metric_key),
            llm_note=f"Not found in source data",
        ))

    return session

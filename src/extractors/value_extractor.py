"""
Value extractor for XBRL data with source citations.

This module takes LLM concept mappings and raw XBRL data, then extracts
the actual values with full source citations. It performs NO calculations
and makes NO LLM calls - it's pure Python data extraction.

The flow is:
1. Concept mapper identifies which XBRL concepts map to which metrics
2. This module extracts the actual values from raw data
3. It builds source citations for audit trail
4. Python calculators perform all derived calculations
"""

from src.fetchers.sec_edgar import (
    extract_facts,
    get_annual_facts,
    build_sec_viewer_url,
    build_sec_document_url,
)
from src.extractors.concept_mapper import ConceptMappingResult
from src.models.extraction import (
    ExtractionSession,
    ExtractedValue,
    SourceCitation,
    UnmappedValue,
    NotFoundMetric,
    METRIC_DISPLAY_NAMES,
)


def extract_values_with_citations(
    session: ExtractionSession,
    raw_data: dict,
    mapping_result: ConceptMappingResult,
) -> ExtractionSession:
    """
    Extract financial values from raw XBRL data using LLM concept mappings.

    This function:
    1. Takes concept mappings from the LLM
    2. Extracts actual values from raw XBRL data
    3. Builds source citations for each value
    4. Populates the ExtractionSession with ExtractedValue objects

    Args:
        session: The extraction session to populate
        raw_data: Raw SEC EDGAR data
        mapping_result: LLM concept mapping result

    Returns:
        Updated ExtractionSession with raw_values populated
    """
    # Set fiscal year info from mapping result
    session.fiscal_year_end = mapping_result.fiscal_year_end
    session.fiscal_year_end_prior = mapping_result.fiscal_year_end_prior
    session.llm_notes = mapping_result.llm_notes
    session.llm_warnings = mapping_result.llm_warnings

    # Extract values for each mapped metric
    for metric_key, concept_mapping in mapping_result.mapped.items():
        extracted = _extract_metric_value(
            session=session,
            raw_data=raw_data,
            metric_key=metric_key,
            concept_name=concept_mapping.xbrl_concept,
            reasoning=concept_mapping.reasoning,
            statement=concept_mapping.statement,
        )
        if extracted:
            session.raw_values[metric_key] = extracted

    # Add not found metrics
    for metric_key, note in mapping_result.not_found.items():
        session.not_found.append(NotFoundMetric(
            metric_key=metric_key,
            display_name=METRIC_DISPLAY_NAMES.get(metric_key, metric_key),
            llm_note=note,
        ))

    # Add unmapped but notable values with citations
    for item in mapping_result.unmapped_but_notable:
        concept_name = item.get("concept", "")
        statement = item.get("statement", "")
        citation = None
        citation_prior = None

        # Try to get citation info for unmapped values
        if concept_name:
            facts = extract_facts(raw_data, concept_name, taxonomy="us-gaap")
            annual_facts = get_annual_facts(facts, years=2)
            if annual_facts:
                current_fact = annual_facts[0]
                citation = _build_citation(
                    session.cik,
                    concept_name,
                    current_fact.label,
                    current_fact.accession_number,
                    current_fact.filed,
                    current_fact.form,
                    current_fact.end_date,
                    current_fact.value,
                    statement,
                )
                if len(annual_facts) >= 2:
                    prior_fact = annual_facts[1]
                    citation_prior = _build_citation(
                        session.cik,
                        concept_name,
                        prior_fact.label,
                        prior_fact.accession_number,
                        prior_fact.filed,
                        prior_fact.form,
                        prior_fact.end_date,
                        prior_fact.value,
                        statement,
                    )

        session.unmapped_values.append(UnmappedValue(
            xbrl_concept=concept_name,
            xbrl_label=item.get("label", ""),
            value_current=item.get("value_current", 0),
            value_prior=item.get("value_prior", 0),
            llm_note=item.get("note", ""),
            citation=citation,
            citation_prior=citation_prior,
        ))

    return session


def _extract_metric_value(
    session: ExtractionSession,
    raw_data: dict,
    metric_key: str,
    concept_name: str,
    reasoning: str,
    statement: str = "",
) -> ExtractedValue | None:
    """
    Extract a single metric value from raw XBRL data.

    Args:
        session: The extraction session (for CIK)
        raw_data: Raw SEC EDGAR data
        metric_key: The metric key (e.g., "revenue")
        concept_name: The XBRL concept name
        reasoning: LLM's reasoning for this mapping
        statement: Which financial statement (from LLM)

    Returns:
        ExtractedValue with citations, or None if extraction fails
    """
    # Extract facts for this concept
    facts = extract_facts(raw_data, concept_name, taxonomy="us-gaap")
    if not facts:
        # Try dei taxonomy as fallback
        facts = extract_facts(raw_data, concept_name, taxonomy="dei")
    if not facts:
        return None

    # Get the two most recent annual values
    annual_facts = get_annual_facts(facts, years=2)
    if not annual_facts:
        return None

    # Current year fact (most recent)
    current_fact = annual_facts[0]
    current_value = current_fact.value
    current_citation = _build_citation(
        session.cik,
        concept_name,
        current_fact.label,
        current_fact.accession_number,
        current_fact.filed,
        current_fact.form,
        current_fact.end_date,
        current_value,
        statement,
    )

    # Prior year fact (second most recent, if available)
    prior_value = 0.0
    prior_citation = None
    if len(annual_facts) >= 2:
        prior_fact = annual_facts[1]
        prior_value = prior_fact.value
        prior_citation = _build_citation(
            session.cik,
            concept_name,
            prior_fact.label,
            prior_fact.accession_number,
            prior_fact.filed,
            prior_fact.form,
            prior_fact.end_date,
            prior_value,
            statement,
        )

    return ExtractedValue(
        metric_key=metric_key,
        display_name=METRIC_DISPLAY_NAMES.get(metric_key, metric_key),
        value=current_value,
        value_prior=prior_value,
        citation=current_citation,
        citation_prior=prior_citation,
        llm_reasoning=reasoning,
        is_editable=True,
    )


def _build_citation(
    cik: str,
    concept_name: str,
    label: str,
    accession_number: str,
    filed: str,
    form: str,
    period_end: str,
    value: float,
    statement: str = "",
) -> SourceCitation:
    """
    Build a source citation for a financial fact.

    Args:
        cik: Company CIK
        concept_name: XBRL concept name
        label: Human-readable label
        accession_number: SEC accession number
        filed: Filing date
        form: Form type (10-K, 10-Q)
        period_end: Period end date
        value: The actual value
        statement: Which financial statement (e.g., "Income Statement", "Balance Sheet")

    Returns:
        SourceCitation object
    """
    # Build the SEC filing URL
    if accession_number:
        filing_url = build_sec_document_url(cik, accession_number)
    else:
        filing_url = ""

    return SourceCitation(
        xbrl_concept=f"us-gaap:{concept_name}",
        xbrl_label=label,
        filing_url=filing_url,
        accession_number=accession_number,
        filing_date=filed,
        form_type=form,
        period_end=period_end,
        raw_value=value,
        statement=statement,
    )


def extract_all_available_values(
    session: ExtractionSession,
    raw_data: dict,
) -> dict[str, list[dict]]:
    """
    Extract all available XBRL values for exploration/debugging.

    This function extracts ALL concepts from the raw data, not just
    mapped ones. Useful for understanding what data is available.

    Args:
        session: The extraction session (for CIK)
        raw_data: Raw SEC EDGAR data

    Returns:
        Dict mapping concept names to list of values with metadata
    """
    result = {}
    taxonomy_data = raw_data.get("facts", {}).get("us-gaap", {})

    for concept_name, concept_data in taxonomy_data.items():
        label = concept_data.get("label", concept_name)
        facts = extract_facts(raw_data, concept_name, taxonomy="us-gaap")
        annual_facts = get_annual_facts(facts, years=2)

        if annual_facts:
            result[concept_name] = [
                {
                    "label": label,
                    "value": f.value,
                    "period_end": f.end_date,
                    "form": f.form,
                    "filed": f.filed,
                    "accession": f.accession_number,
                }
                for f in annual_facts
            ]

    return result


def print_extraction_summary(session: ExtractionSession) -> None:
    """Print a summary of extracted values."""
    print(f"\n{'='*70}")
    print(f"EXTRACTION SUMMARY: {session.company_name} ({session.ticker})")
    print(f"CIK: {session.cik}")
    print(f"Fiscal Years: {session.fiscal_year_end} vs {session.fiscal_year_end_prior}")
    print(f"{'='*70}\n")

    print("EXTRACTED VALUES")
    print("-" * 70)
    print(f"{'Metric':<30} {'Current':>15} {'Prior':>15}")
    print("-" * 70)

    for metric_key, ev in session.raw_values.items():
        # Format large numbers
        if abs(ev.value) >= 1e9:
            current = f"${ev.value/1e9:,.1f}B"
            prior = f"${ev.value_prior/1e9:,.1f}B"
        elif abs(ev.value) >= 1e6:
            current = f"${ev.value/1e6:,.1f}M"
            prior = f"${ev.value_prior/1e6:,.1f}M"
        else:
            current = f"${ev.value:,.0f}"
            prior = f"${ev.value_prior:,.0f}"

        print(f"{ev.display_name:<30} {current:>15} {prior:>15}")

    if session.not_found:
        print(f"\n{'='*70}")
        print("NOT FOUND")
        print("-" * 70)
        for nf in session.not_found:
            print(f"  • {nf.display_name}: {nf.llm_note}")

    if session.unmapped_values:
        print(f"\n{'='*70}")
        print("UNMAPPED BUT NOTABLE")
        print("-" * 70)
        for uv in session.unmapped_values:
            current = f"${uv.value_current/1e9:,.1f}B" if abs(uv.value_current) >= 1e9 else f"${uv.value_current/1e6:,.1f}M"
            print(f"  • {uv.xbrl_label} ({uv.xbrl_concept}): {current}")
            print(f"    {uv.llm_note}")

    if session.llm_notes:
        print(f"\n{'='*70}")
        print("LLM NOTES")
        print("-" * 70)
        for note in session.llm_notes:
            print(f"  • {note}")

    if session.llm_warnings:
        print(f"\n{'='*70}")
        print("WARNINGS")
        print("-" * 70)
        for warning in session.llm_warnings:
            print(f"  ⚠ {warning}")

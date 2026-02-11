"""
Extraction API routes.

Handles:
- POST /api/extract - Extract financial data from SEC EDGAR
- POST /api/approve - Approve extraction with optional edits and run calculations
- GET /api/session/{session_id} - Get session status
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from src.fetchers.sec_edgar import lookup_cik, lookup_by_cik, fetch_company_facts
from src.extractors.concept_mapper import map_concepts_with_raw_data
from src.extractors.value_extractor import extract_values_with_citations
from src.extractors.session_builder import (
    NormalizedExtractionData,
    NormalizedMetric,
    build_extraction_session,
)
from src.extractors.pdf_extractor import normalize_unit
from src.calculators.metrics import calculate_metrics_from_raw, FinancialMetrics
from src.calculators.ratios import calculate_ratios_from_raw, FinancialRatios
from src.calculators.verification import run_verification, VerificationResult
from src.models.extraction import ExtractionSession, CalculationStep

router = APIRouter()

# In-memory session storage (for demo - use Redis/DB in production)
_sessions: dict[str, ExtractionSession] = {}
_raw_data_cache: dict[str, dict] = {}  # Cache raw SEC data by session_id


# ============== Request/Response Models ==============

class ExtractRequest(BaseModel):
    """Request to extract financial data for a ticker."""
    ticker: str
    model: str | None = None  # LLM model to use (e.g., "claude-opus-4-6")


class EditedValue(BaseModel):
    """A single edited value from the user."""
    metric_key: str
    value: float | None = None
    value_prior: float | None = None


class ApproveRequest(BaseModel):
    """Request to approve extraction with optional edits."""
    session_id: str
    edited_values: list[EditedValue] = []


class SourceCitationResponse(BaseModel):
    """Source citation in API response."""
    xbrl_concept: str
    xbrl_label: str | None = None
    filing_url: str | None = None
    accession_number: str | None = None
    filing_date: str | None = None
    form_type: str | None = None
    period_end: str | None = None
    raw_value: float
    statement: str | None = None  # Which financial statement (e.g., "Income Statement")


class ExtractedValueResponse(BaseModel):
    """Extracted value in API response."""
    metric_key: str
    display_name: str
    value: float
    value_prior: float
    citation: SourceCitationResponse | None = None
    citation_prior: SourceCitationResponse | None = None
    llm_reasoning: str
    is_editable: bool


class UnmappedValueResponse(BaseModel):
    """Unmapped but notable value in API response."""
    xbrl_concept: str
    xbrl_label: str
    value_current: float = 0.0
    value_prior: float = 0.0
    llm_note: str
    citation: SourceCitationResponse | None = None
    citation_prior: SourceCitationResponse | None = None


class NotFoundMetricResponse(BaseModel):
    """Not found metric in API response."""
    metric_key: str
    display_name: str
    llm_note: str


class VerificationCheckResponse(BaseModel):
    """A single verification check result."""
    check_id: str
    description: str
    formula: str
    lhs_value: float
    rhs_value: float
    difference: float
    tolerance: float
    passed: bool
    severity: str
    year: str
    skipped: bool = False


class VerificationResultResponse(BaseModel):
    """Verification results summary."""
    checks: list[VerificationCheckResponse]
    pass_count: int
    fail_count: int
    warning_count: int
    error_count: int
    skip_count: int


class ExtractResponse(BaseModel):
    """Response from extraction endpoint."""
    session_id: str
    ticker: str
    company_name: str
    cik: str
    fiscal_year_end: str
    fiscal_year_end_prior: str
    unit: str  # Unit of financial metrics (e.g., "millions", "thousands", "dollars")
    raw_values: dict[str, ExtractedValueResponse]
    unmapped_values: list[UnmappedValueResponse]
    not_found: list[NotFoundMetricResponse]
    llm_notes: list[str]
    llm_warnings: list[str]
    verification: VerificationResultResponse | None = None


class CalculatedMetricsResponse(BaseModel):
    """Calculated metrics in API response."""
    tangible_net_worth: float
    tangible_net_worth_prior: float
    cash_balance: float
    cash_balance_prior: float
    top_line_revenue: float
    top_line_revenue_prior: float
    gross_profit: float
    gross_profit_prior: float
    gross_profit_margin: float
    gross_profit_margin_prior: float
    operating_income: float
    operating_income_prior: float
    operating_income_margin: float
    operating_income_margin_prior: float
    ebitda: float
    ebitda_prior: float
    ebitda_margin: float
    ebitda_margin_prior: float
    adjusted_ebitda: float
    adjusted_ebitda_prior: float
    adjusted_ebitda_margin: float
    adjusted_ebitda_margin_prior: float
    net_income: float
    net_income_prior: float
    net_income_margin: float
    net_income_margin_prior: float


class CalculatedRatiosResponse(BaseModel):
    """Calculated ratios in API response."""
    current_ratio: float
    current_ratio_prior: float
    cash_ratio: float
    cash_ratio_prior: float
    debt_to_equity: float
    debt_to_equity_prior: float
    ebitda_interest_coverage: float
    ebitda_interest_coverage_prior: float
    net_debt_to_ebitda: float
    net_debt_to_ebitda_prior: float
    net_debt_to_adj_ebitda: float
    net_debt_to_adj_ebitda_prior: float
    days_sales_outstanding: float
    days_sales_outstanding_prior: float
    working_capital: float
    working_capital_prior: float
    return_on_assets: float
    return_on_assets_prior: float
    return_on_equity: float
    return_on_equity_prior: float


class CalculationStepResponse(BaseModel):
    """Calculation step in API response."""
    metric: str
    formula: str
    formula_excel: str
    inputs: dict[str, float]
    result: float


class ApproveResponse(BaseModel):
    """Response from approve endpoint."""
    session_id: str
    approved_at: str
    metrics: CalculatedMetricsResponse
    ratios: CalculatedRatiosResponse
    calculation_steps: list[CalculationStepResponse]


# ============== Helper Functions ==============

def _normalize_session_to_dollars(session: ExtractionSession) -> None:
    """
    Normalize all financial values in session to actual dollars based on unit.

    This converts values like "5.2" (in millions) to "5200000" (in dollars),
    so downstream calculations and displays use consistent units.

    Modifies the session in place.
    """
    # First, normalize the unit string to a standard format
    normalized_unit = normalize_unit(session.unit)

    # Determine multiplier based on standardized unit
    multiplier_map = {
        "billions": 1_000_000_000,
        "millions": 1_000_000,
        "thousands": 1_000,
        "dollars": 1,
    }

    multiplier = multiplier_map.get(normalized_unit, 1)

    # If already in dollars (multiplier is 1), no conversion needed
    if multiplier == 1:
        session.unit = "dollars"
        return

    # Normalize all raw values
    for metric_key in session.raw_values:
        metric = session.raw_values[metric_key]
        metric.value *= multiplier
        metric.value_prior *= multiplier

    # Update unit to dollars
    session.unit = "dollars"


def _verification_to_response(vr: VerificationResult) -> VerificationResultResponse:
    """Convert VerificationResult to API response."""
    return VerificationResultResponse(
        checks=[
            VerificationCheckResponse(
                check_id=c.check_id,
                description=c.description,
                formula=c.formula,
                lhs_value=c.lhs_value,
                rhs_value=c.rhs_value,
                difference=c.difference,
                tolerance=c.tolerance,
                passed=c.passed,
                severity=c.severity,
                year=c.year,
                skipped=c.skipped,
            )
            for c in vr.checks
        ],
        pass_count=vr.pass_count,
        fail_count=vr.fail_count,
        warning_count=vr.warning_count,
        error_count=vr.error_count,
        skip_count=vr.skip_count,
    )


def _session_to_extract_response(session: ExtractionSession, verification: VerificationResult | None = None) -> ExtractResponse:
    """Convert ExtractionSession to API response."""
    raw_values = {}
    for key, ev in session.raw_values.items():
        citation = None
        if ev.citation:
            citation = SourceCitationResponse(
                xbrl_concept=ev.citation.xbrl_concept,
                xbrl_label=ev.citation.xbrl_label,
                filing_url=ev.citation.filing_url,
                accession_number=ev.citation.accession_number,
                filing_date=ev.citation.filing_date,
                form_type=ev.citation.form_type,
                period_end=ev.citation.period_end,
                raw_value=ev.citation.raw_value,
                statement=ev.citation.statement,
            )
        citation_prior = None
        if ev.citation_prior:
            citation_prior = SourceCitationResponse(
                xbrl_concept=ev.citation_prior.xbrl_concept,
                xbrl_label=ev.citation_prior.xbrl_label,
                filing_url=ev.citation_prior.filing_url,
                accession_number=ev.citation_prior.accession_number,
                filing_date=ev.citation_prior.filing_date,
                form_type=ev.citation_prior.form_type,
                period_end=ev.citation_prior.period_end,
                raw_value=ev.citation_prior.raw_value,
                statement=ev.citation_prior.statement,
            )
        raw_values[key] = ExtractedValueResponse(
            metric_key=ev.metric_key,
            display_name=ev.display_name,
            value=ev.value,
            value_prior=ev.value_prior,
            citation=citation,
            citation_prior=citation_prior,
            llm_reasoning=ev.llm_reasoning,
            is_editable=ev.is_editable,
        )

    unmapped = []
    for uv in session.unmapped_values:
        uv_citation = None
        if uv.citation:
            uv_citation = SourceCitationResponse(
                xbrl_concept=uv.citation.xbrl_concept,
                xbrl_label=uv.citation.xbrl_label,
                filing_url=uv.citation.filing_url,
                accession_number=uv.citation.accession_number,
                filing_date=uv.citation.filing_date,
                form_type=uv.citation.form_type,
                period_end=uv.citation.period_end,
                raw_value=uv.citation.raw_value,
                statement=uv.citation.statement,
            )
        uv_citation_prior = None
        if uv.citation_prior:
            uv_citation_prior = SourceCitationResponse(
                xbrl_concept=uv.citation_prior.xbrl_concept,
                xbrl_label=uv.citation_prior.xbrl_label,
                filing_url=uv.citation_prior.filing_url,
                accession_number=uv.citation_prior.accession_number,
                filing_date=uv.citation_prior.filing_date,
                form_type=uv.citation_prior.form_type,
                period_end=uv.citation_prior.period_end,
                raw_value=uv.citation_prior.raw_value,
                statement=uv.citation_prior.statement,
            )
        unmapped.append(UnmappedValueResponse(
            xbrl_concept=uv.xbrl_concept or "",
            xbrl_label=uv.xbrl_label or "",
            value_current=uv.value_current if uv.value_current is not None else 0.0,
            value_prior=uv.value_prior if uv.value_prior is not None else 0.0,
            llm_note=uv.llm_note or "",
            citation=uv_citation,
            citation_prior=uv_citation_prior,
        ))

    not_found = [
        NotFoundMetricResponse(
            metric_key=nf.metric_key,
            display_name=nf.display_name,
            llm_note=nf.llm_note,
        )
        for nf in session.not_found
    ]

    return ExtractResponse(
        session_id=session.session_id,
        ticker=session.ticker,
        company_name=session.company_name,
        cik=session.cik,
        fiscal_year_end=session.fiscal_year_end,
        fiscal_year_end_prior=session.fiscal_year_end_prior,
        unit=session.unit,
        raw_values=raw_values,
        unmapped_values=unmapped,
        not_found=not_found,
        llm_notes=session.llm_notes,
        llm_warnings=session.llm_warnings,
        verification=_verification_to_response(verification) if verification else None,
    )


def _metrics_to_response(metrics: FinancialMetrics) -> CalculatedMetricsResponse:
    """Convert FinancialMetrics to API response."""
    return CalculatedMetricsResponse(
        tangible_net_worth=metrics.tangible_net_worth,
        tangible_net_worth_prior=metrics.tangible_net_worth_prior,
        cash_balance=metrics.cash_balance,
        cash_balance_prior=metrics.cash_balance_prior,
        top_line_revenue=metrics.top_line_revenue,
        top_line_revenue_prior=metrics.top_line_revenue_prior,
        gross_profit=metrics.gross_profit,
        gross_profit_prior=metrics.gross_profit_prior,
        gross_profit_margin=metrics.gross_profit_margin,
        gross_profit_margin_prior=metrics.gross_profit_margin_prior,
        operating_income=metrics.operating_income,
        operating_income_prior=metrics.operating_income_prior,
        operating_income_margin=metrics.operating_income_margin,
        operating_income_margin_prior=metrics.operating_income_margin_prior,
        ebitda=metrics.ebitda,
        ebitda_prior=metrics.ebitda_prior,
        ebitda_margin=metrics.ebitda_margin,
        ebitda_margin_prior=metrics.ebitda_margin_prior,
        adjusted_ebitda=metrics.adjusted_ebitda,
        adjusted_ebitda_prior=metrics.adjusted_ebitda_prior,
        adjusted_ebitda_margin=metrics.adjusted_ebitda_margin,
        adjusted_ebitda_margin_prior=metrics.adjusted_ebitda_margin_prior,
        net_income=metrics.net_income,
        net_income_prior=metrics.net_income_prior,
        net_income_margin=metrics.net_income_margin,
        net_income_margin_prior=metrics.net_income_margin_prior,
    )


def _ratios_to_response(ratios: FinancialRatios) -> CalculatedRatiosResponse:
    """Convert FinancialRatios to API response."""
    return CalculatedRatiosResponse(
        current_ratio=ratios.current_ratio,
        current_ratio_prior=ratios.current_ratio_prior,
        cash_ratio=ratios.cash_ratio,
        cash_ratio_prior=ratios.cash_ratio_prior,
        debt_to_equity=ratios.debt_to_equity,
        debt_to_equity_prior=ratios.debt_to_equity_prior,
        ebitda_interest_coverage=ratios.ebitda_interest_coverage,
        ebitda_interest_coverage_prior=ratios.ebitda_interest_coverage_prior,
        net_debt_to_ebitda=ratios.net_debt_to_ebitda,
        net_debt_to_ebitda_prior=ratios.net_debt_to_ebitda_prior,
        net_debt_to_adj_ebitda=ratios.net_debt_to_adj_ebitda,
        net_debt_to_adj_ebitda_prior=ratios.net_debt_to_adj_ebitda_prior,
        days_sales_outstanding=ratios.days_sales_outstanding,
        days_sales_outstanding_prior=ratios.days_sales_outstanding_prior,
        working_capital=ratios.working_capital,
        working_capital_prior=ratios.working_capital_prior,
        return_on_assets=ratios.return_on_assets,
        return_on_assets_prior=ratios.return_on_assets_prior,
        return_on_equity=ratios.return_on_equity,
        return_on_equity_prior=ratios.return_on_equity_prior,
    )


def _xbrl_to_normalized(
    ticker: str,
    company_name: str,
    cik: str,
    fiscal_year_end: str,
    fiscal_year_end_prior: str,
    raw_values: dict,
    not_found: list,
    llm_model: str,
    llm_notes: list,
    llm_warnings: list,
    unit: str = "dollars",
) -> NormalizedExtractionData:
    """
    Convert XBRL extraction result to normalized format.
    Used by ticker path before sending to shared builder.

    This adapter ensures ticker path produces same structure as PDF path.
    """
    metrics = {}

    # Convert ExtractedValue objects to NormalizedMetric
    for metric_key, extracted_value in raw_values.items():
        source_desc = extracted_value.citation.xbrl_concept if extracted_value.citation else "Unknown"
        source_url = extracted_value.citation.filing_url if extracted_value.citation else ""
        # Preserve the statement field from SEC extraction (e.g., "Income Statement", "Balance Sheet")
        statement = extracted_value.citation.statement if extracted_value.citation else ""

        metrics[metric_key] = NormalizedMetric(
            metric_key=metric_key,
            value=extracted_value.value,
            value_prior=extracted_value.value_prior,
            source_description=source_desc,
            source_url=source_url,
            reasoning=extracted_value.llm_reasoning,
            form_type="10-K",
            period_end=fiscal_year_end,
            period_end_prior=fiscal_year_end_prior,
            statement=statement,
        )

    # Extract not_found metric keys
    not_found_keys = [nf.metric_key for nf in not_found]

    return NormalizedExtractionData(
        company_name=company_name,
        ticker=ticker,
        cik=cik,
        fiscal_year_end=fiscal_year_end,
        fiscal_year_end_prior=fiscal_year_end_prior,
        metrics=metrics,
        unmapped_notes=[],  # Not tracked by XBRL path
        not_found=not_found_keys,
        unit=unit,  # Pass through the unit from XBRL extraction
        llm_model=llm_model,
        llm_notes=llm_notes,
        llm_warnings=llm_warnings,
    )


# ============== API Endpoints ==============

@router.post("/extract", response_model=ExtractResponse)
async def extract(request: ExtractRequest) -> ExtractResponse:
    """
    Extract financial data from SEC EDGAR for a given ticker or CIK.

    This endpoint:
    1. Fetches raw XBRL data from SEC EDGAR
    2. Uses LLM to map XBRL concepts to required metrics
    3. Extracts values with full source citations
    4. Returns data for human review

    The user should review the extracted values, make any corrections,
    then call POST /api/approve to run calculations.

    Accepts either:
    - Stock ticker (e.g., "AAPL", "TSLA")
    - SEC CIK number (e.g., "0001398987" or "1398987")
    """
    input_value = request.ticker.strip()

    # Detect if input is a CIK (numeric) or ticker (alphanumeric)
    is_cik = input_value.replace("0", "").isdigit() and len(input_value) >= 6

    if is_cik:
        # Look up by CIK directly
        company = lookup_by_cik(input_value)
        if not company:
            raise HTTPException(
                status_code=404,
                detail=f"No company found for CIK: {input_value}. Please verify the CIK is correct."
            )
        ticker = company.ticker or f"CIK{input_value}"
    else:
        # Look up by ticker
        ticker = input_value.upper()
        company = lookup_cik(ticker)
        if not company:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Ticker '{ticker}' not found in SEC database. "
                    f"This can happen with smaller companies or recent ticker changes. "
                    f"Use the SEC CIK Lookup at https://www.sec.gov/search-filings/cik-lookup "
                    f"to find the CIK by company name, then enter it here (e.g., '0001398987')."
                )
            )

    # Step 2: Fetch raw SEC data
    raw_data = fetch_company_facts(company.cik)

    # Step 3: Map concepts using LLM
    llm_model = request.model or "claude-opus-4-6"
    mapping_result = map_concepts_with_raw_data(
        company_name=company.name,
        ticker=ticker,
        cik=company.cik,
        raw_data=raw_data,
        model=llm_model,
    )
    if not mapping_result:
        raise HTTPException(status_code=500, detail="Failed to map XBRL concepts")

    # Step 4: Extract values with citations (old path - returns populated session)
    temp_session = ExtractionSession.create(
        ticker=ticker,
        company_name=company.name,
        cik=company.cik,
    )
    temp_session = extract_values_with_citations(temp_session, raw_data, mapping_result)
    temp_session.llm_model = llm_model

    # Step 5: Normalize to common format
    normalized = _xbrl_to_normalized(
        ticker=ticker,
        company_name=company.name,
        cik=company.cik,
        fiscal_year_end=temp_session.fiscal_year_end,
        fiscal_year_end_prior=temp_session.fiscal_year_end_prior,
        raw_values=temp_session.raw_values,
        not_found=temp_session.not_found,
        llm_model=llm_model,
        llm_notes=temp_session.llm_notes,
        llm_warnings=temp_session.llm_warnings,
        unit=temp_session.unit,  # Pass the unit detected by LLM extraction
    )

    # Step 6: Use shared builder to create session (same as PDF path)
    session = build_extraction_session(normalized)

    # Step 7: Normalize all values to actual dollars immediately (no intermediate unit)
    _normalize_session_to_dollars(session)

    # Run verification checks
    verification = run_verification(session)

    # Store session and raw data for later
    _sessions[session.session_id] = session
    _raw_data_cache[session.session_id] = raw_data

    return _session_to_extract_response(session, verification=verification)


@router.post("/extract-pdf", response_model=ExtractResponse)
async def extract_pdf(
    file: UploadFile = File(...),
    model: str = Form("claude-opus-4-6")
) -> ExtractResponse:
    """
    Extract financial data from uploaded 10-K PDF.

    This endpoint:
    1. Extracts text from the PDF
    2. Uses LLM to extract financial metrics from PDF text
    3. Normalizes results for review
    4. Returns data for human review (same as ticker-based extraction)

    The user should review the extracted values, make any corrections,
    then call POST /api/approve to run calculations.

    Accepts:
    - PDF file (10-K filing format)
    """
    # Validate file is PDF
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    # Read file bytes
    pdf_bytes = await file.read()

    # Check file size (max 50MB)
    if len(pdf_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Send PDF directly to Claude's API (no local parsing — avoids memory issues)
    from src.extractors.pdf_extractor import (
        extract_from_pdf_bytes,
        pdf_to_normalized,
    )

    try:
        pdf_result = extract_from_pdf_bytes(pdf_bytes, model=model)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        del pdf_bytes

    # Normalize to common format
    normalized = pdf_to_normalized(pdf_result)
    normalized.llm_model = model

    # Use shared builder (same as ticker path!)
    session = build_extraction_session(normalized)

    print(f"\n[DEBUG] API /extract-pdf - Before _normalize_session_to_dollars:")
    print(f"  session.unit: {session.unit}")
    if session.raw_values:
        first_key = list(session.raw_values.keys())[0]
        first_val = session.raw_values[first_key]
        print(f"  Sample raw value ({first_key}): {first_val.value}")

    # Normalize all values to actual dollars immediately (no intermediate unit)
    _normalize_session_to_dollars(session)

    print(f"[DEBUG] API /extract-pdf - After _normalize_session_to_dollars:")
    print(f"  session.unit: {session.unit}")
    if session.raw_values:
        first_key = list(session.raw_values.keys())[0]
        first_val = session.raw_values[first_key]
        print(f"  Sample raw value ({first_key}): {first_val.value}")
    print()

    # Run verification checks
    verification = run_verification(session)

    # Store session
    _sessions[session.session_id] = session

    return _session_to_extract_response(session, verification=verification)


@router.post("/approve", response_model=ApproveResponse)
async def approve(request: ApproveRequest) -> ApproveResponse:
    """
    Approve extraction with optional edits and run deterministic calculations.

    This endpoint:
    1. Applies any user edits to the raw values
    2. Runs deterministic Python calculations for all metrics and ratios
    3. Returns calculated values with full audit trail

    After approval, the user can export to Excel or PDF.
    """
    session_id = request.session_id

    # Get session
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]

    # Apply user edits
    for edit in request.edited_values:
        if edit.value is not None:
            session.set_raw_value(edit.metric_key, edit.value, prior=False)
        if edit.value_prior is not None:
            session.set_raw_value(edit.metric_key, edit.value_prior, prior=True)

    # Normalize all values to actual dollars so calculations are consistent
    _normalize_session_to_dollars(session)

    # Mark as approved
    session.is_approved = True
    session.approved_at = datetime.utcnow().isoformat()

    # Run calculations
    metrics, metric_steps = calculate_metrics_from_raw(session)
    ratios, ratio_steps = calculate_ratios_from_raw(
        session,
        ebitda=metrics.ebitda,
        ebitda_prior=metrics.ebitda_prior,
        adjusted_ebitda=metrics.adjusted_ebitda,
        adjusted_ebitda_prior=metrics.adjusted_ebitda_prior,
    )

    # Store calculation steps in session
    session.calculation_steps = metric_steps + ratio_steps

    # Update stored session
    _sessions[session_id] = session

    # Build response
    calc_steps = [
        CalculationStepResponse(
            metric=step.metric,
            formula=step.formula,
            formula_excel=step.formula_excel,
            inputs=step.inputs,
            result=step.result,
        )
        for step in session.calculation_steps
    ]

    return ApproveResponse(
        session_id=session_id,
        approved_at=session.approved_at,
        metrics=_metrics_to_response(metrics),
        ratios=_ratios_to_response(ratios),
        calculation_steps=calc_steps,
    )


class VerifyRequest(BaseModel):
    """Request to re-run verification checks."""
    session_id: str
    edited_values: list[EditedValue] = []


@router.post("/verify", response_model=VerificationResultResponse)
async def verify(request: VerifyRequest) -> VerificationResultResponse:
    """
    Re-run verification checks with optionally edited values.

    This allows users to check if their edits fix verification issues
    without approving the session.
    """
    session_id = request.session_id

    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]

    # Apply edits temporarily for verification
    for edit in request.edited_values:
        if edit.value is not None:
            session.set_raw_value(edit.metric_key, edit.value, prior=False)
        if edit.value_prior is not None:
            session.set_raw_value(edit.metric_key, edit.value_prior, prior=True)

    verification = run_verification(session)
    return _verification_to_response(verification)


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> ExtractResponse:
    """Get the current state of an extraction session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]
    verification = run_verification(session)
    return _session_to_extract_response(session, verification=verification)

"""
Export API routes.

Handles:
- POST /api/export/excel - Export to Excel with formulas
- POST /api/export/report - Export to Word report
- POST /api/export/pdf - Export to PDF report
"""

import io
import subprocess
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.api.routes.extraction import _sessions, _raw_data_cache
from src.calculators.metrics import calculate_metrics_from_raw
from src.calculators.ratios import calculate_ratios_from_raw
from src.generators.excel_export import generate_excel_report
from src.generators.word_report import generate_word_report
from src.generators.narrative import generate_company_narrative
from src.fetchers.yahoo import fetch_company_info, fetch_corporate_actions, CompanyInfo
from src.fetchers.logo import download_logo

router = APIRouter()


class ExportExcelRequest(BaseModel):
    """Request to export to Excel."""
    session_id: str


class ManualInputs(BaseModel):
    """Manual inputs for the report (S&P/Moody's, etc.)."""
    sp_rating: str = "[EDIT]"
    sp_outlook: str = "[EDIT]"
    moodys_rating: str = "[EDIT]"
    moodys_outlook: str = "[EDIT]"
    hq_city: str = ""
    hq_state: str = ""
    num_locations: str = ""
    additional_notes: str = ""


class ExportReportRequest(BaseModel):
    """Request to export to Word/PDF report."""
    session_id: str
    manual_inputs: ManualInputs = ManualInputs()
    include_narrative: bool = True


@router.post("/export/excel")
async def export_excel(request: ExportExcelRequest):
    """
    Export extraction data to Excel with formulas.

    The Excel file includes:
    - Sheet 1: Raw Values with source citations
    - Sheet 2: Calculated Metrics with Excel formulas
    - Sheet 3: Ratios with Excel formulas
    - Sheet 4: Audit Log with calculation steps
    """
    session_id = request.session_id

    # Get session
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]

    if not session.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Session must be approved before export. Call POST /api/approve first."
        )

    # Calculate metrics and ratios
    metrics, metric_steps = calculate_metrics_from_raw(session)
    ratios, ratio_steps = calculate_ratios_from_raw(
        session,
        ebitda=metrics.ebitda,
        ebitda_prior=metrics.ebitda_prior,
        adjusted_ebitda=metrics.adjusted_ebitda,
        adjusted_ebitda_prior=metrics.adjusted_ebitda_prior,
    )
    all_steps = metric_steps + ratio_steps

    # Generate Excel file
    excel_buffer = generate_excel_report(
        session=session,
        metrics=metrics,
        ratios=ratios,
        calculation_steps=all_steps,
    )

    # Return as streaming response
    filename = f"{session.ticker}_Financial_Analysis.xlsx"
    return StreamingResponse(
        excel_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/export/report")
async def export_report(request: ExportReportRequest):
    """
    Export to Word report.

    The report includes:
    - Company overview with logo
    - LLM-generated narrative (optional)
    - Financial metrics table with YoY deltas
    - Ratios table
    - Corporate actions from Yahoo Finance
    - S&P/Moody's outlook section (with manual inputs)
    """
    session_id = request.session_id

    # Get session
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]

    if not session.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Session must be approved before export. Call POST /api/approve first."
        )

    # Calculate metrics and ratios
    metrics, _ = calculate_metrics_from_raw(session)
    ratios, _ = calculate_ratios_from_raw(
        session,
        ebitda=metrics.ebitda,
        ebitda_prior=metrics.ebitda_prior,
        adjusted_ebitda=metrics.adjusted_ebitda,
        adjusted_ebitda_prior=metrics.adjusted_ebitda_prior,
    )

    # Fetch additional data from Yahoo Finance (with error handling)
    try:
        company_info = fetch_company_info(session.ticker)
    except Exception:
        # Create a minimal CompanyInfo if Yahoo fails
        company_info = CompanyInfo(
            name=session.company_name,
            ticker=session.ticker,
        )

    try:
        corporate_actions = fetch_corporate_actions(session.ticker)
    except Exception:
        corporate_actions = []

    # Download logo (with error handling)
    logo_path = None
    try:
        if company_info and company_info.website:
            logo_dir = Path(tempfile.gettempdir()) / "financial_reports"
            logo_dir.mkdir(exist_ok=True)
            logo_path = download_logo(company_info.website, logo_dir)
    except Exception:
        pass  # Logo is optional

    # Generate narrative if requested (with error handling)
    narrative = None
    if request.include_narrative and company_info:
        try:
            narrative = generate_company_narrative(
                company_info=company_info,
                metrics=metrics,
                ratios=ratios,
                corporate_actions=corporate_actions,
            )
        except Exception as e:
            narrative = f"[Narrative generation failed: {str(e)}]"

    # Generate Word document
    doc_buffer = io.BytesIO()
    generate_word_report(
        output_path=doc_buffer,
        company_info=company_info,
        metrics=metrics,
        ratios=ratios,
        corporate_actions=corporate_actions,
        narrative=narrative,
        logo_path=logo_path,
        fiscal_year_end=session.fiscal_year_end,
        fiscal_year_end_prior=session.fiscal_year_end_prior,
        unit=session.unit,
        sp_rating=request.manual_inputs.sp_rating,
        sp_outlook=request.manual_inputs.sp_outlook,
        moodys_rating=request.manual_inputs.moodys_rating,
        moodys_outlook=request.manual_inputs.moodys_outlook,
        session=session,
    )
    doc_buffer.seek(0)

    # Return as streaming response
    filename = f"{session.ticker}_Financial_Report.docx"
    return StreamingResponse(
        doc_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/export/pdf")
async def export_pdf(request: ExportReportRequest):
    """
    Export to PDF report.

    This generates a Word document first, then converts it to PDF.
    Requires LibreOffice to be installed for conversion.
    """
    session_id = request.session_id

    # Get session
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    session = _sessions[session_id]

    if not session.is_approved:
        raise HTTPException(
            status_code=400,
            detail="Session must be approved before export. Call POST /api/approve first."
        )

    # Calculate metrics and ratios
    metrics, _ = calculate_metrics_from_raw(session)
    ratios, _ = calculate_ratios_from_raw(
        session,
        ebitda=metrics.ebitda,
        ebitda_prior=metrics.ebitda_prior,
        adjusted_ebitda=metrics.adjusted_ebitda,
        adjusted_ebitda_prior=metrics.adjusted_ebitda_prior,
    )

    # Fetch additional data from Yahoo Finance (with error handling)
    try:
        company_info = fetch_company_info(session.ticker)
    except Exception:
        company_info = CompanyInfo(
            name=session.company_name,
            ticker=session.ticker,
        )

    try:
        corporate_actions = fetch_corporate_actions(session.ticker)
    except Exception:
        corporate_actions = []

    # Download logo
    logo_path = None
    try:
        if company_info and company_info.website:
            logo_dir = Path(tempfile.gettempdir()) / "financial_reports"
            logo_dir.mkdir(exist_ok=True)
            logo_path = download_logo(company_info.website, logo_dir)
    except Exception:
        pass

    # Generate narrative if requested
    narrative = None
    if request.include_narrative and company_info:
        try:
            narrative = generate_company_narrative(
                company_info=company_info,
                metrics=metrics,
                ratios=ratios,
                corporate_actions=corporate_actions,
            )
        except Exception as e:
            narrative = f"[Narrative generation failed: {str(e)}]"

    # Generate Word document to temp file
    with tempfile.TemporaryDirectory() as tmpdir:
        docx_path = Path(tmpdir) / f"{session.ticker}_report.docx"
        pdf_path = Path(tmpdir) / f"{session.ticker}_report.pdf"

        generate_word_report(
            output_path=docx_path,
            company_info=company_info,
            metrics=metrics,
            ratios=ratios,
            corporate_actions=corporate_actions,
            narrative=narrative,
            logo_path=logo_path,
            fiscal_year_end=session.fiscal_year_end,
            fiscal_year_end_prior=session.fiscal_year_end_prior,
            unit=session.unit,
            sp_rating=request.manual_inputs.sp_rating,
            sp_outlook=request.manual_inputs.sp_outlook,
            moodys_rating=request.manual_inputs.moodys_rating,
            moodys_outlook=request.manual_inputs.moodys_outlook,
            session=session,
        )

        # Convert to PDF using LibreOffice
        try:
            result = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(tmpdir),
                    str(docx_path),
                ],
                capture_output=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"PDF conversion failed. Make sure LibreOffice is installed. Error: {result.stderr.decode()}"
                )
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail="LibreOffice not found. Please install LibreOffice to enable PDF export, or use Word export instead."
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=500, detail="PDF conversion timed out")

        # Read PDF into buffer
        if not pdf_path.exists():
            raise HTTPException(status_code=500, detail="PDF file was not created")

        pdf_buffer = io.BytesIO(pdf_path.read_bytes())

    # Return as streaming response
    filename = f"{session.ticker}_Financial_Report.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

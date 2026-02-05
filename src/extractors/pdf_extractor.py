"""
PDF-based financial data extraction.

This module handles:
1. Extracting text from PDF files (pdfplumber)
2. Using LLM to extract financial metrics from PDF text
3. Normalizing PDF extraction results for use by shared session builder
"""

import json
from dataclasses import dataclass
from io import BytesIO
import pdfplumber
from anthropic import Anthropic

from src.models.extraction import REQUIRED_BASE_METRICS, METRIC_DISPLAY_NAMES
from src.extractors.session_builder import (
    NormalizedExtractionData,
    NormalizedMetric,
)


@dataclass
class PDFExtractionResult:
    """Raw result from LLM extraction of PDF."""
    company_name: str
    ticker: str
    fiscal_year_end: str
    fiscal_year_end_prior: str
    metrics: dict  # metric_key -> {value, value_prior, page_number, source_text}
    company_info: dict  # sector, industry, employees, website, hq, etc.
    credit_ratings: dict  # sp_rating, sp_outlook, moodys_rating, moodys_outlook
    unmapped_notes: list
    not_found: list
    llm_notes: list
    llm_warnings: list


def extract_text_from_pdf(pdf_bytes: bytes) -> dict[int, str]:
    """
    Extract text from PDF file.

    Args:
        pdf_bytes: Raw PDF file bytes

    Returns:
        Dict mapping page number (0-indexed) to text content

    Raises:
        ValueError: If PDF is corrupted or cannot be parsed
    """
    try:
        pdf_text = {}
        # Wrap bytes in BytesIO to create a file-like object
        pdf_file = BytesIO(pdf_bytes)
        with pdfplumber.open(pdf_file) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    pdf_text[page_num] = text
        return pdf_text
    except Exception as e:
        raise ValueError(
            f"Unable to extract text from PDF. Ensure it contains searchable text, not scanned images. Error: {str(e)}"
        )


def extract_from_pdf(
    pdf_text: dict[int, str],
    model: str = "claude-opus-4-5-20251101"
) -> PDFExtractionResult:
    """
    Extract financial data from PDF text using LLM.

    Args:
        pdf_text: Dict of page_number -> text from extract_text_from_pdf()
        model: Claude model to use

    Returns:
        PDFExtractionResult with extracted metrics and company info
    """
    client = Anthropic()

    # Build prompt with PDF text
    pdf_content = "\n\n".join(
        [f"--- Page {page_num + 1} ---\n{text}" for page_num, text in sorted(pdf_text.items())]
    )

    # Required metrics list for prompt
    metrics_list = "\n".join(
        [f"{i+1}. {METRIC_DISPLAY_NAMES.get(m, m)} ({m})" for i, m in enumerate(REQUIRED_BASE_METRICS)]
    )

    prompt = f"""You are a financial data extraction specialist. Extract financial data from this 10-K filing PDF.

REQUIRED FINANCIAL METRICS (extract for 2 most recent fiscal years):
{metrics_list}

COMPANY INFORMATION:
- Company name
- Ticker symbol (look on cover page, headers, or body of filing)
- Fiscal year end dates (current and prior year in YYYY-MM-DD format)
- Headquarters city and state
- Sector and industry (from Item 1 Business section)
- Employee count
- Website
- Brief business description (1-2 sentences from Item 1)

CREDIT RATINGS (if mentioned anywhere in the document):
- S&P rating and outlook
- Moody's rating and outlook

EXTRACTION RULES:
- All dollar amounts should be converted to their base unit (millions if stated in millions, etc.)
- For each metric, provide BOTH current year and prior year values
- Include the page number where each value was found
- If a metric appears in multiple places, use the most recent/authoritative source
- Only mark metrics as "not found" if they genuinely don't appear in the document

Return ONLY valid JSON (no markdown, no extra text):
{{
  "company_name": "string",
  "ticker": "string (or empty if not found)",
  "fiscal_year_end": "YYYY-MM-DD",
  "fiscal_year_end_prior": "YYYY-MM-DD",
  "metrics": {{
    "metric_key": {{
      "value": number (current year),
      "value_prior": number (prior year),
      "page_number": number (0-indexed page where found),
      "source_text": "brief quote or location description"
    }},
    ...
  }},
  "company_info": {{
    "sector": "string or null",
    "industry": "string or null",
    "employees": number or null,
    "website": "string or null",
    "hq_city": "string or null",
    "hq_state": "string or null",
    "business_description": "string or null"
  }},
  "credit_ratings": {{
    "sp_rating": "string or null",
    "sp_outlook": "string or null",
    "moodys_rating": "string or null",
    "moodys_outlook": "string or null"
  }},
  "unmapped_notes": ["notable items found that don't fit standard metrics"],
  "not_found": ["metric_keys that couldn't be found"],
  "llm_notes": ["processing notes"],
  "llm_warnings": ["warnings about data quality or confidence"]
}}

PDF CONTENT:
{pdf_content}"""

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.content[0].text

        # Handle markdown-wrapped JSON (```json ... ```)
        if result_text.strip().startswith('```'):
            # Extract JSON from markdown code block
            lines = result_text.strip().split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith('```json'):
                    in_json = True
                    continue
                elif line.strip() == '```':
                    in_json = False
                    break
                elif in_json:
                    json_lines.append(line)
            result_text = '\n'.join(json_lines)

        result_json = json.loads(result_text)

        # Validate we got expected structure
        if not isinstance(result_json, dict):
            raise ValueError(f"Expected JSON object, got {type(result_json).__name__}")

        # Parse result into PDFExtractionResult with defaults
        return PDFExtractionResult(
            company_name=result_json.get("company_name") or "Unknown",
            ticker=result_json.get("ticker") or "",
            fiscal_year_end=result_json.get("fiscal_year_end") or "",
            fiscal_year_end_prior=result_json.get("fiscal_year_end_prior") or "",
            metrics=result_json.get("metrics") or {},
            company_info=result_json.get("company_info") or {},
            credit_ratings=result_json.get("credit_ratings") or {},
            unmapped_notes=result_json.get("unmapped_notes") or [],
            not_found=result_json.get("not_found") or [],
            llm_notes=result_json.get("llm_notes") or [],
            llm_warnings=result_json.get("llm_warnings") or [],
        )
    except json.JSONDecodeError as e:
        # Show first 200 chars of response for debugging
        preview = result_text[:200] if 'result_text' in locals() else "No response"
        raise ValueError(f"LLM response was not valid JSON: {str(e)}. Response preview: {preview}")
    except Exception as e:
        raise ValueError(f"LLM extraction failed: {str(e)}")


def pdf_to_normalized(pdf_result: PDFExtractionResult) -> NormalizedExtractionData:
    """
    Convert PDF extraction result to normalized format for shared builder.

    This is where the PDF path converges with the shared builder.
    """
    metrics = {}

    # Convert each metric to normalized format
    for metric_key, metric_data in pdf_result.metrics.items():
        if metric_key not in REQUIRED_BASE_METRICS:
            continue  # Skip unknown metrics

        try:
            value = float(metric_data.get("value", 0)) if metric_data.get("value") else 0.0
            value_prior = float(metric_data.get("value_prior", 0)) if metric_data.get("value_prior") else 0.0
            page_num = metric_data.get("page_number", 0)
            source_text = metric_data.get("source_text", "")

            # Build source description with page number
            source_desc = f"Page {page_num + 1} of PDF"
            if source_text:
                source_desc += f": {source_text}"

            metrics[metric_key] = NormalizedMetric(
                metric_key=metric_key,
                value=value,
                value_prior=value_prior,
                source_description=source_desc,
                source_url="",  # No URL for PDF uploads
                reasoning=source_text,
                form_type="10-K",
                period_end=pdf_result.fiscal_year_end,
                period_end_prior=pdf_result.fiscal_year_end_prior,
            )
        except (ValueError, TypeError):
            # Skip metrics with invalid values
            continue

    return NormalizedExtractionData(
        company_name=pdf_result.company_name,
        ticker=pdf_result.ticker,
        cik="",  # No CIK for PDF uploads
        fiscal_year_end=pdf_result.fiscal_year_end,
        fiscal_year_end_prior=pdf_result.fiscal_year_end_prior,
        metrics=metrics,
        unmapped_notes=pdf_result.unmapped_notes,
        not_found=pdf_result.not_found,
        llm_model="claude-opus-4-5-20251101",  # Will be set by caller
        llm_notes=pdf_result.llm_notes,
        llm_warnings=pdf_result.llm_warnings,
    )

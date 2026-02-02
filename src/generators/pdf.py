"""PDF report generation using Jinja2 and WeasyPrint."""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.fetchers.yahoo import CompanyInfo
from src.calculators.metrics import FinancialMetrics
from src.calculators.ratios import FinancialRatios


# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def generate_pdf_report(
    output_path: Path,
    company_info: CompanyInfo,
    metrics: FinancialMetrics,
    ratios: FinancialRatios,
    narrative: str,
    logo_path: Path | None = None,
    sp_rating: str | None = None,
    sp_outlook: str | None = None,
    moodys_rating: str | None = None,
    moodys_outlook: str | None = None,
    hq: str | None = None,
    locations: str | None = None,
    ttm_revenue: str | None = None,
) -> Path:
    """
    Generate a PDF financial report.

    Args:
        output_path: Directory to save the PDF
        company_info: Company information
        metrics: Calculated financial metrics
        ratios: Calculated financial ratios
        narrative: LLM-generated company narrative
        logo_path: Path to company logo image
        sp_rating: S&P credit rating
        sp_outlook: S&P outlook
        moodys_rating: Moody's rating
        moodys_outlook: Moody's outlook
        hq: Headquarters location (override)
        locations: Number of locations
        ttm_revenue: Trailing twelve month revenue

    Returns:
        Path to generated PDF
    """
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report.html")

    # Prepare template context
    context = {
        "company": company_info,
        "metrics": metrics,
        "metrics_deltas": metrics.calculate_deltas(),
        "ratios": ratios,
        "ratios_deltas": ratios.calculate_deltas(),
        "narrative": narrative,
        "logo_path": str(logo_path) if logo_path else None,
        "ratings": {
            "sp_rating": sp_rating,
            "sp_outlook": sp_outlook,
            "moodys_rating": moodys_rating,
            "moodys_outlook": moodys_outlook,
        },
        "company_details": {
            "hq": hq or f"{company_info.hq_city}, {company_info.hq_state}",
            "public_private": "Public",
            "locations": locations,
            "ttm_revenue": ttm_revenue,
        },
    }

    # Render HTML
    html_content = template.render(**context)

    # Generate PDF
    pdf_path = output_path / f"{company_info.ticker}_report.pdf"
    HTML(string=html_content, base_url=str(TEMPLATE_DIR)).write_pdf(pdf_path)

    return pdf_path


def format_currency(value: float, suffix: str = "M") -> str:
    """Format a value as currency with suffix."""
    if value >= 1000:
        return f"${value / 1000:.1f}B"
    return f"${value:.1f}{suffix}"


def format_percentage(value: float) -> str:
    """Format a value as percentage."""
    return f"{value:.2%}"


def format_ratio(value: float) -> str:
    """Format a value as ratio."""
    return f"{value:.2f}x"


def get_delta_color(delta: float) -> str:
    """Get CSS color class for delta value."""
    if delta > 0:
        return "positive"
    elif delta < 0:
        return "negative"
    return "neutral"

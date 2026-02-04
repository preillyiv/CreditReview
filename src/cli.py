"""
CLI entry point for financial report generation.

NOTE: This is for DEVELOPMENT/TESTING only.
The production interface is a web app (FastAPI backend + React frontend).
This CLI exists to test the pipeline without spinning up the full web stack.
"""

import click
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Financial Reporting Tool - Generate PDF reports from SEC EDGAR data."""
    pass


@cli.command()
@click.argument("ticker")
@click.option("--output", "-o", type=click.Path(), default="./output",
              help="Output directory for generated report")
def generate(ticker, output):
    """Generate a full Word document financial report for TICKER.

    Example: uv run python -m src.cli generate AMZN
    """
    from src.extractors.llm_extractor import extract_financial_data
    from src.fetchers.yahoo import fetch_company_info, fetch_corporate_actions
    from src.fetchers.logo import get_logo_url, download_logo, get_domain_from_website
    from src.generators.narrative import generate_company_narrative
    from src.generators.word_report import generate_word_report

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    click.echo(f"Generating financial report for {ticker}...")
    click.echo("-" * 50)

    # Step 1: Extract financial data from SEC EDGAR
    click.echo("1. Extracting financial data from SEC EDGAR (via Claude)...")
    extraction = extract_financial_data(ticker)
    if not extraction:
        click.echo("   ERROR: Failed to extract financial data. Check ticker and API key.")
        return
    click.echo(f"   Fiscal year: {extraction.fiscal_year_end}")
    if extraction.warnings:
        for w in extraction.warnings[:3]:
            click.echo(f"   Warning: {w}")

    # Step 2: Fetch company info from Yahoo Finance
    click.echo("2. Fetching company info from Yahoo Finance...")
    company_info = fetch_company_info(ticker)
    click.echo(f"   Company: {company_info.name}")

    # Step 3: Fetch corporate actions
    click.echo("3. Fetching corporate actions...")
    corporate_actions = fetch_corporate_actions(ticker, limit=10)
    click.echo(f"   Found {len(corporate_actions)} actions")

    # Step 4: Fetch company logo
    click.echo("4. Fetching company logo...")
    logo_path = None
    if company_info.website:
        domain = get_domain_from_website(company_info.website)
        if domain:
            logo_path = download_logo(domain, output_path)
            if logo_path:
                click.echo(f"   Saved to {logo_path}")
            else:
                click.echo("   Could not download logo")
    else:
        click.echo("   No website found, skipping logo")

    # Step 5: Generate narrative
    click.echo("5. Generating company narrative (via Claude)...")
    narrative = generate_company_narrative(
        company_info=company_info,
        metrics=extraction.metrics,
        ratios=extraction.ratios,
        corporate_actions=corporate_actions[:5],
    )
    click.echo(f"   Generated {len(narrative)} characters")

    # Step 6: Generate Word document
    click.echo("6. Generating Word document...")
    doc_path = output_path / f"{ticker}_Financial_Report.docx"
    generate_word_report(
        output_path=doc_path,
        company_info=company_info,
        metrics=extraction.metrics,
        ratios=extraction.ratios,
        fiscal_year_end=extraction.fiscal_year_end,
        fiscal_year_end_prior=extraction.fiscal_year_end_prior,
        narrative=narrative,
        corporate_actions=corporate_actions,
        logo_path=logo_path,
    )
    click.echo(f"   Saved to {doc_path}")

    # Step 7: Generate extraction log
    click.echo("7. Generating extraction log...")
    log_path = output_path / f"{ticker}_Extraction_Log.docx"
    from src.generators.extraction_log import generate_extraction_log
    generate_extraction_log(
        output_path=log_path,
        ticker=ticker,
        company_name=extraction.company_name,
        fiscal_year_end=extraction.fiscal_year_end,
        fiscal_year_end_prior=extraction.fiscal_year_end_prior,
        metrics=extraction.metrics,
        ratios=extraction.ratios,
        notes=extraction.notes,
        warnings=extraction.warnings,
    )
    click.echo(f"   Saved to {log_path}")

    click.echo("-" * 50)
    click.echo(f"Report generated: {doc_path}")
    click.echo(f"Extraction log: {log_path}")


@cli.command()
@click.argument("ticker")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed extraction notes")
def extract(ticker, verbose):
    """Extract financial data from SEC EDGAR for TICKER.

    This fetches XBRL data from SEC EDGAR and uses an LLM to interpret
    and calculate financial metrics and ratios.

    Example: uv run python -m src.cli extract AMZN
    """
    from src.extractors.llm_extractor import extract_financial_data, print_extraction_result

    click.echo(f"Extracting financial data for {ticker} from SEC EDGAR...")
    click.echo("This will call the Claude API to interpret the XBRL data.\n")

    result = extract_financial_data(ticker)

    if result:
        print_extraction_result(result)
        if verbose and result.notes:
            click.echo("\nDetailed extraction notes:")
            for note in result.notes:
                click.echo(f"  - {note}")
    else:
        click.echo(f"Failed to extract data for {ticker}.")
        click.echo("Check that the ticker is valid and ANTHROPIC_API_KEY is set in .env")


@cli.command()
@click.argument("ticker")
def fetch(ticker):
    """Fetch raw SEC EDGAR data for TICKER (no LLM, just raw data).

    This is useful for debugging and seeing what XBRL concepts are available.

    Example: uv run python -m src.cli fetch AMZN
    """
    from src.fetchers.sec_edgar import fetch_financial_data, print_data_summary

    click.echo(f"Fetching SEC EDGAR data for {ticker}...")

    data = fetch_financial_data(ticker)
    if data:
        print_data_summary(data)
    else:
        click.echo(f"Could not find SEC data for {ticker}")


@cli.command()
@click.argument("ticker")
def info(ticker):
    """Fetch company info from Yahoo Finance for TICKER.

    Example: uv run python -m src.cli info AMZN
    """
    from src.fetchers.yahoo import fetch_company_info, fetch_corporate_actions

    click.echo(f"Fetching company info for {ticker}...\n")

    company = fetch_company_info(ticker)
    click.echo(f"Company: {company.name}")
    click.echo(f"Sector: {company.sector}")
    click.echo(f"Industry: {company.industry}")
    click.echo(f"Website: {company.website}")
    click.echo(f"Employees: {company.employees:,}")
    click.echo(f"HQ: {company.hq_city}, {company.hq_state}, {company.hq_country}")
    click.echo(f"\nDescription:\n{company.description[:500]}...")

    actions = fetch_corporate_actions(ticker, limit=5)
    if actions:
        click.echo(f"\nRecent Corporate Actions:")
        for action in actions:
            click.echo(f"  {action.date}: {action.action_type} - {action.description}")


if __name__ == "__main__":
    cli()

"""
CLI entry point for financial report generation.

NOTE: This is for DEVELOPMENT/TESTING only.
The production interface is a web app (FastAPI backend + React frontend).
This CLI exists to test the pipeline without spinning up the full web stack.
"""

import click
from pathlib import Path


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Financial Reporting Tool - Generate PDF reports from CSV financials."""
    pass


@cli.command()
@click.option("--ticker", "-t", required=True, help="Stock ticker symbol (e.g., VZ)")
@click.option("--csvs", "-c", type=click.Path(exists=True), required=True,
              help="Directory containing CSV files")
@click.option("--output", "-o", type=click.Path(), default="./output",
              help="Output directory for generated report")
@click.option("--sp-rating", default=None, help="S&P credit rating (e.g., B, BB+)")
@click.option("--sp-outlook", default=None, help="S&P outlook (e.g., Stable, Positive)")
@click.option("--moodys-rating", default=None, help="Moody's rating (e.g., Ba2)")
@click.option("--moodys-outlook", default=None, help="Moody's outlook")
@click.option("--hq", default=None, help="Headquarters location")
@click.option("--locations", default=None, help="Number of locations")
def generate(ticker, csvs, output, sp_rating, sp_outlook, moodys_rating,
             moodys_outlook, hq, locations):
    """Generate a financial report for a company."""
    click.echo(f"Generating report for {ticker}...")

    csv_path = Path(csvs)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    # TODO: Implement pipeline
    # 1. Parse CSVs
    # 2. Calculate metrics and ratios
    # 3. Fetch company info from Yahoo Finance
    # 4. Fetch logo from Clearbit
    # 5. Generate narrative via LLM
    # 6. Render PDF

    click.echo(f"  CSV directory: {csv_path}")
    click.echo(f"  Output directory: {output_path}")

    if sp_rating:
        click.echo(f"  S&P Rating: {sp_rating} ({sp_outlook or 'N/A'})")
    if moodys_rating:
        click.echo(f"  Moody's Rating: {moodys_rating} ({moodys_outlook or 'N/A'})")

    click.echo("Report generation not yet implemented.")


@cli.command()
@click.option("--csvs", "-c", type=click.Path(exists=True), required=True,
              help="Directory containing CSV files")
def validate(csvs):
    """Validate CSV files without generating a report."""
    click.echo(f"Validating CSVs in {csvs}...")
    # TODO: Implement validation
    click.echo("Validation not yet implemented.")


if __name__ == "__main__":
    cli()

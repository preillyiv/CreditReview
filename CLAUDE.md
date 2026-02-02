# Financial Reporting Tool

## Project Overview
Internal web application that generates PDF financial reports for publicly traded companies from CSV uploads.

**Target users:** Internal team members (non-technical) who upload CSVs via browser and download PDF reports.

## Architecture
**Web-based** with a Python backend API:

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React)                                           │
│  - CSV upload UI                                            │
│  - Manual input fields (S&P/Moody's ratings, etc.)          │
│  - Report preview & PDF download                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                      │
│  POST /api/reports/generate                                 │
│  - Receives CSVs + manual inputs                            │
│  - Returns generated PDF                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Report Generation Pipeline (Python)                        │
│  1. Parse CSVs → pandas DataFrames                          │
│  2. Calculate metrics & ratios                              │
│  3. Fetch company info (yfinance) + logo (Clearbit)         │
│  4. Generate narrative (Anthropic API)                      │
│  5. Render HTML template → PDF (WeasyPrint)                 │
└─────────────────────────────────────────────────────────────┘
```

This is a **deterministic pipeline**, not an agent. No branching logic or tool selection needed.

## Input
- CSV files: annual financials, balance sheet, cash flows (uploaded via web UI)
- Manual inputs via form: S&P/Moody's ratings, HQ, locations, etc.
- Ticker symbol for Yahoo Finance lookups

## Output
PDF report containing:
1. Company logo + basic info
2. Company story/narrative (LLM-generated from financials + scraped context)
3. Financial Statements Overview table (metrics with YoY deltas, color-coded)
4. Ratios table (current ratio, debt-to-equity, etc.)
5. Key Corporate Actions (from Yahoo Finance)
6. S&P/Moody's outlook section

## Tech Stack
**Backend (Python):**
- **FastAPI** - REST API
- **pandas** - CSV parsing and financial calculations
- **yfinance** - Yahoo Finance data (company info, corporate actions)
- **anthropic** - LLM calls for narrative generation
- **Jinja2 + WeasyPrint** - HTML to PDF conversion

**Frontend (TBD):**
- **React + Vite** (recommended)
- File upload, form inputs, PDF preview/download

**Development only:**
- CLI wrapper (`cli.py`) for testing the pipeline without the web UI

## Package Management
Uses **uv** (not pip). All commands auto-use the project's `.venv/` - no manual activation needed.

```bash
# Install uv (one-time)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows
# or: curl -LsSf https://astral.sh/uv/install.sh | sh       # Unix

# Project setup
uv sync                      # Install dependencies (creates .venv automatically)
uv sync --extra dev          # Include dev dependencies (pytest, click)

# Running code
uv run python -m src.cli     # Run CLI
uv run uvicorn src.api:app   # Run API server
uv run pytest                # Run tests

# Adding dependencies
uv add <package>             # Add to [dependencies]
uv add --dev <package>       # Add to [dev] optional group
```

**IMPORTANT:** Never use `pip install` directly. Always use `uv add` or `uv sync`.

## Project Structure
```
src/
├── api/                # FastAPI routes (TBD)
├── pipeline.py         # Main report generation orchestration
├── parsers/            # CSV parsing logic
├── calculators/        # Metrics and ratios calculations
├── fetchers/           # External data (yfinance, Clearbit)
├── generators/         # Narrative (LLM) and PDF generation
└── templates/          # Jinja2 HTML templates

frontend/               # React app (TBD)
data/sample/            # Sample CSVs for testing
output/                 # Generated reports (dev only)
tests/                  # Unit tests
```

## Key Metrics (from images)
### Financial Statements Overview
- Tangible Net Worth
- Cash Balance
- Top Line Revenue
- Gross Profit / Margin
- Operating Income / Margin
- EBITDA / Margin
- Adjusted EBITDA / Margin
- Net Income / Margin

### Ratios
- Current Ratio
- Cash Ratio
- Debt-to-Equity Ratio
- EBITDA Interest Coverage
- Net Debt / EBITDA
- Net Debt / Adj. EBITDA
- Days Sales Outstanding
- Working Capital
- Return on Assets
- Return on Equity

## Table Formatting
- Green background: positive delta
- Red background: negative delta
- Red text: negative values
- Values formatted with $ and M/B suffixes

## API Endpoints (planned)
```
POST /api/reports/generate
  - Body: multipart form with CSV files + JSON metadata
  - Returns: PDF file

GET /api/company/{ticker}/info
  - Returns: Company info from Yahoo Finance (for preview)
```

## Development CLI
For testing the pipeline without spinning up the web app:
```bash
uv run python -m src.cli generate --ticker VZ --csvs ./data/
```
This is **dev-only** - not the product interface.

## Environment Variables
Stored in `.env` (git-ignored):
- `ANTHROPIC_API_KEY` - Required for narrative generation

## Notes
- CSV format expected to match Yahoo Finance export structure (TBD based on actual samples)
- S&P/Moody's ratings must be input manually via web form - no free API exists
- Logo fetching uses Clearbit's free endpoint (no API key needed)
- PDF generation happens server-side; frontend just displays/downloads the result

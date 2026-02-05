# Financial Reporting Tool

> **Note to Claude:** Keep this file up to date. When you make significant changes to the project (new features, architectural changes, new dependencies, modified APIs, changed workflows), update the relevant sections of this document to reflect the current state.

## Project Overview
Internal web application that generates financial reports for publicly traded companies by extracting data directly from SEC EDGAR filings.

**Target users:** Internal team members (non-technical) who enter a ticker symbol and get a comprehensive financial report.

## Architecture
**Web-based** with a Python backend API:

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                    │
│  - Ticker input and extraction controls                     │
│  - Raw value review/approval UI                             │
│  - Manual input fields (S&P/Moody's ratings, etc.)          │
│  - Export to Word/Excel/PDF                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                      │
│  POST /api/extract - Start extraction for ticker            │
│  GET  /api/extract/{id}/status - Check extraction progress  │
│  POST /api/approve - Approve reviewed raw values            │
│  POST /api/export/excel - Export to Excel                   │
│  POST /api/export/report - Export to Word                   │
│  POST /api/export/pdf - Export to PDF                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Report Generation Pipeline (Python)                        │
│  1. Fetch XBRL data from SEC EDGAR                          │
│  2. Extract raw values via LLM (Claude)                     │
│  3. User reviews/approves raw values                        │
│  4. Calculate metrics & ratios from approved values         │
│  5. Fetch company info (yfinance) + logo (Logo.dev/fallbacks)│
│  6. Generate narrative (Anthropic API)                      │
│  7. Generate Word report (python-docx)                      │
└─────────────────────────────────────────────────────────────┘
```

## Input
- Ticker symbol (data fetched automatically from SEC EDGAR)
- 10-K PDF file (alternative to ticker lookup)
- Manual inputs via form: S&P/Moody's ratings, HQ, locations, etc.

## Data Units - SEC Standard
**CRITICAL:** All 10-K financial statement amounts are reported in **MILLIONS** (SEC standard - no exceptions):
- Both SEC XBRL extraction and PDF 10-K extraction assume all amounts are in millions
- Both paths multiply values by 1,000,000 to convert to actual dollars for calculations
- Frontend displays use the normalized dollar amounts to determine M/B formatting (e.g., $134.8B)

## Output
Word/Excel/PDF report containing:
1. Company logo + basic info
2. Company story/narrative (LLM-generated from financials)
3. Financial Statements Overview table (metrics with YoY deltas, color-coded)
4. Ratios table (current ratio, debt-to-equity, etc.)
5. EBITDA Reconciliation table
6. Key Corporate Actions (from Yahoo Finance)
7. S&P/Moody's outlook section (manual input with [EDIT] placeholders)

## Tech Stack
**Backend (Python):**
- **FastAPI** - REST API
- **anthropic** - LLM calls for data extraction and narrative generation
- **yfinance** - Yahoo Finance data (company info, corporate actions)
- **python-docx** - Word document generation
- **openpyxl** - Excel export with formulas
- **Pillow** - Image processing for logo conversion
- **requests** - SEC EDGAR API and logo fetching

**Frontend:**
- **React + Vite** - Located in `frontend/`
- Extraction UI, raw value review, export controls

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
├── api/                    # FastAPI routes
│   └── routes/
│       ├── extraction.py   # /api/extract endpoints
│       └── export.py       # /api/export endpoints
├── extractors/             # SEC EDGAR data extraction
│   ├── llm_extractor.py    # Main LLM-based extraction
│   ├── concept_mapper.py   # XBRL concept mapping
│   └── value_extractor.py  # Raw value extraction helpers
├── calculators/            # Metrics and ratios calculations
│   ├── metrics.py          # Financial metrics (EBITDA, margins, etc.)
│   └── ratios.py           # Financial ratios (current ratio, etc.)
├── fetchers/               # External data fetching
│   ├── sec_edgar.py        # SEC EDGAR XBRL data
│   ├── yahoo.py            # Yahoo Finance (company info, actions)
│   └── logo.py             # Logo fetching (Logo.dev + fallbacks)
├── generators/             # Report generation
│   ├── word_report.py      # Word document (.docx)
│   ├── excel_export.py     # Excel with formulas (.xlsx)
│   ├── narrative.py        # LLM narrative generation
│   └── extraction_log.py   # Extraction audit log
├── models/                 # Data models
│   └── extraction.py       # ExtractionSession, RawValue, etc.
└── cli.py                  # Development CLI

frontend/                   # React + Vite app
output/                     # Generated reports (dev only)
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

## API Endpoints
```
# Extraction
POST /api/extract           - Start extraction for a ticker
GET  /api/extract/{id}      - Get extraction session status
POST /api/approve           - Approve reviewed raw values

# Export
POST /api/export/excel      - Export to Excel with formulas
POST /api/export/report     - Export to Word document
POST /api/export/pdf        - Export to PDF (requires LibreOffice)
```

## Development CLI
For testing the pipeline without spinning up the web app:
```bash
uv run python -m src.cli generate AMZN    # Full report generation
uv run python -m src.cli extract AMZN     # Extract data only (shows metrics)
uv run python -m src.cli fetch AMZN       # Raw SEC EDGAR data (no LLM)
uv run python -m src.cli info AMZN        # Yahoo Finance company info
```
This is **dev-only** - not the product interface.

## Environment Variables
Stored in `.env` (git-ignored):
- `ANTHROPIC_API_KEY` - Required for LLM extraction and narrative generation
- `LOGO_DEV_TOKEN` - Logo.dev API token for company logo fetching

## Notes
- Data is fetched from SEC EDGAR XBRL filings (no CSV upload needed)
- S&P/Moody's ratings must be input manually via web form - no free API exists
- Logo fetching uses multiple providers with fallbacks: Logo.dev (primary), Clearbit, Google S2, DuckDuckGo
- Logos are converted to PNG for best python-docx compatibility
- PDF export requires LibreOffice installed; Word export works without it
- The extraction workflow includes a human review step before final report generation

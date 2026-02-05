# Financial Reporting Tool

Generate comprehensive financial reports for publicly traded companies by extracting data from SEC EDGAR filings or uploaded 10-K PDFs.

## Quick Start

### 1. Install Dependencies

```bash
uv sync
cd frontend && npm install
```

### 2. Run the Backend API Server

```bash
uv run uvicorn src.api:app --reload
```

The API will be available at `http://localhost:8000`

**API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI)

### 3. Run the Frontend (in a new terminal)

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Development Commands

### Backend

| Command | Purpose |
|---------|---------|
| `uv run uvicorn src.api:app --reload` | **Run API server** (main command) |
| `uv run python -m src.cli generate AMZN` | Generate full report via CLI |
| `uv run python -m src.cli extract AMZN` | Extract data only |
| `uv run python -m src.cli fetch AMZN` | Fetch raw SEC EDGAR data |
| `uv run python -m src.cli info AMZN` | Fetch Yahoo Finance data |

### Frontend

| Command | Purpose |
|---------|---------|
| `cd frontend && npm run dev` | **Run dev server** (main command) |
| `cd frontend && npm run build` | Build for production |
| `cd frontend && npm run preview` | Preview production build |

## Usage

1. **Open the web app**: `http://localhost:5173`
2. **Choose input method**:
   - Enter a stock ticker or SEC CIK number (e.g., `AMZN`, `TSLA`, `0001018724`)
   - Or upload a 10-K PDF file
3. **Review extracted values**: Edit any incorrect values
4. **Approve**: Run calculations
5. **Export**: Download Word/Excel report

## Project Structure

```
├── src/                          # Python backend
│   ├── api/                      # FastAPI routes
│   │   └── routes/extraction.py  # /extract and /extract-pdf endpoints
│   ├── extractors/               # Data extraction
│   │   ├── session_builder.py    # Shared builder (both paths)
│   │   ├── pdf_extractor.py      # PDF extraction
│   │   ├── concept_mapper.py     # XBRL concept mapping
│   │   └── value_extractor.py    # Value extraction from XBRL
│   ├── calculators/              # Metrics and ratios
│   ├── fetchers/                 # External data (SEC EDGAR, Yahoo Finance)
│   ├── generators/               # Report generation
│   ├── models/                   # Data models
│   └── cli.py                    # Development CLI
├── frontend/                     # React + Vite
│   ├── src/components/           # React components
│   ├── src/api/                  # API client
│   └── src/App.tsx               # Main app
└── pyproject.toml                # Python dependencies
```

## Environment Setup

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=your_key_here
LOGO_DEV_TOKEN=your_token_here  # Optional - for company logo fetching
```

## Tech Stack

**Backend**: FastAPI, Python 3.11+, Anthropic API, pdfplumber
**Frontend**: React, TypeScript, Vite
**Data**: SEC EDGAR XBRL, Yahoo Finance

## Notes

- The app uses **in-memory session storage** (fine for development, use Redis/DB for production)
- PDF extraction requires the document to have searchable text (not scanned images)
- S&P/Moody's ratings must be entered manually via the web form
- Company logos are fetched automatically if a ticker is available

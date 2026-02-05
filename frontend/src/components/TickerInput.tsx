import { useState, FormEvent, ChangeEvent } from 'react';

export type InputMode = 'ticker' | 'pdf';
export type LLMModel = 'claude-opus-4-5-20251101' | 'claude-sonnet-4-5-20250929' | 'claude-haiku-4-5-20251001';

interface DataInputProps {
  onSubmit: (mode: InputMode, data: string | File, model: LLMModel) => void;
}

const MODEL_OPTIONS: { value: LLMModel; label: string }[] = [
  { value: 'claude-opus-4-5-20251101', label: 'Claude Opus 4.5' },
  { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
];

export function DataInput({ onSubmit }: DataInputProps) {
  const [ticker, setTicker] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState<LLMModel>('claude-opus-4-5-20251101');

  const handleTickerSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSubmit('ticker', ticker.trim(), model);
    }
  };

  const handlePdfSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (file) {
      onSubmit('pdf', file, model);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    setFile(files ? files[0] : null);
  };

  return (
    <div>
      {/* Model selector at top */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div className="flex gap-1" style={{ alignItems: 'center' }}>
          <label className="text-sm text-muted" htmlFor="model-select">LLM Model:</label>
          <select
            id="model-select"
            value={model}
            onChange={(e) => setModel(e.target.value as LLMModel)}
            style={{
              padding: '0.4em 0.8em',
              borderRadius: '6px',
              border: '1px solid #ccc',
              fontSize: '0.875rem',
              backgroundColor: 'white',
              color: '#333',
              cursor: 'pointer',
              minWidth: '160px',
            }}
          >
            {MODEL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Ticker input card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2>Enter Stock Ticker or CIK</h2>
        <p className="text-sm text-muted mb-2">
          Enter a US stock ticker or SEC CIK number to extract financial data from SEC EDGAR filings.
        </p>
        <form onSubmit={handleTickerSubmit} className="flex gap-2">
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="e.g., AMZN, TSLA, or 0001398987"
            style={{ maxWidth: '300px' }}
          />
          <button type="submit" className="primary" disabled={!ticker.trim()}>
            Extract Data
          </button>
        </form>
        <p className="text-sm text-muted" style={{ marginTop: '1rem' }}>
          Smaller companies may not be in the ticker list. Use the{' '}
          <a
            href="https://www.sec.gov/search-filings/cik-lookup"
            target="_blank"
            rel="noopener noreferrer"
          >
            SEC CIK Lookup
          </a>{' '}
          to find the CIK number by company name.
        </p>
      </div>

      {/* PDF upload card */}
      <div className="card">
        <h2>Upload 10-K PDF</h2>
        <p className="text-sm text-muted mb-2">
          Upload a 10-K filing PDF to extract financial data, company information, and credit ratings directly from the document.
        </p>
        <form onSubmit={handlePdfSubmit} className="flex gap-2">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            style={{ maxWidth: '300px' }}
          />
          <button type="submit" className="primary" disabled={!file}>
            Extract Data
          </button>
        </form>
        <p className="text-sm text-muted" style={{ marginTop: '1rem' }}>
          The PDF must contain searchable text (not scanned images). Supports 10-K annual reports.
        </p>
      </div>
    </div>
  );
}

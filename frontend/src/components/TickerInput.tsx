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
  const [mode, setMode] = useState<InputMode>('ticker');
  const [ticker, setTicker] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [model, setModel] = useState<LLMModel>('claude-opus-4-5-20251101');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (mode === 'ticker' && ticker.trim()) {
      onSubmit('ticker', ticker.trim(), model);
    } else if (mode === 'pdf' && file) {
      onSubmit('pdf', file, model);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    setFile(files ? files[0] : null);
  };

  const isValid = mode === 'ticker' ? ticker.trim() : file !== null;

  return (
    <div className="card">
      <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Extract Financial Data</h2>
          <p className="text-sm text-muted mb-2">
            {mode === 'ticker'
              ? 'Enter a US stock ticker or SEC CIK number to extract financial data from SEC EDGAR filings.'
              : 'Upload a 10-K PDF filing to extract financial data and company information.'}
          </p>
        </div>
        <div className="flex gap-1" style={{ alignItems: 'center' }}>
          <label className="text-sm text-muted" htmlFor="model-select">Model:</label>
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

      {/* Input mode toggle */}
      <div className="flex gap-3" style={{ marginBottom: '1.5rem' }}>
        <label className="flex gap-2" style={{ alignItems: 'center', cursor: 'pointer' }}>
          <input
            type="radio"
            name="input-mode"
            value="ticker"
            checked={mode === 'ticker'}
            onChange={() => setMode('ticker')}
          />
          <span>Enter Ticker/CIK</span>
        </label>
        <label className="flex gap-2" style={{ alignItems: 'center', cursor: 'pointer' }}>
          <input
            type="radio"
            name="input-mode"
            value="pdf"
            checked={mode === 'pdf'}
            onChange={() => setMode('pdf')}
          />
          <span>Upload 10-K PDF</span>
        </label>
      </div>

      {/* Conditional input based on mode */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        {mode === 'ticker' ? (
          <>
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="e.g., AMZN, TSLA, or 0001398987"
              style={{ maxWidth: '300px' }}
            />
            <button type="submit" className="primary" disabled={!isValid}>
              Extract Data
            </button>
          </>
        ) : (
          <>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              style={{ maxWidth: '300px' }}
            />
            <button type="submit" className="primary" disabled={!isValid}>
              Extract Data
            </button>
          </>
        )}
      </form>

      {mode === 'ticker' && (
        <p className="text-sm text-muted" style={{ marginTop: '1.5rem' }}>
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
      )}
    </div>
  );
}

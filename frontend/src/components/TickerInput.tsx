import { useState, FormEvent } from 'react';

export type LLMModel = 'claude-opus-4-5-20251101' | 'claude-sonnet-4-5-20250929' | 'claude-haiku-4-5-20251001';

interface TickerInputProps {
  onSubmit: (ticker: string, model: LLMModel) => void;
}

const MODEL_OPTIONS: { value: LLMModel; label: string }[] = [
  { value: 'claude-opus-4-5-20251101', label: 'Claude Opus 4.5' },
  { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5' },
  { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
];

export function TickerInput({ onSubmit }: TickerInputProps) {
  const [ticker, setTicker] = useState('');
  const [model, setModel] = useState<LLMModel>('claude-opus-4-5-20251101');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onSubmit(ticker.trim(), model);
    }
  };

  return (
    <div className="card">
      <div className="flex" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Enter Stock Ticker or CIK</h2>
          <p className="text-sm text-muted mb-2">
            Enter a US stock ticker or SEC CIK number to extract financial data from SEC EDGAR filings.
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
      <form onSubmit={handleSubmit} className="flex gap-2">
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
    </div>
  );
}

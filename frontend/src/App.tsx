import { useState } from 'react';
import {
  ExtractResponse,
  ApproveResponse,
  EditedValue,
  extractData,
  approveExtraction,
  exportExcel,
  exportReport,
} from './api/client';
import { TickerInput, LLMModel } from './components/TickerInput';
import { ReviewTable } from './components/ReviewTable';
import { UnmappedSection } from './components/UnmappedSection';
import { ExportButtons } from './components/ExportButtons';
import { CalculatedResults } from './components/CalculatedResults';

type AppState = 'input' | 'extracting' | 'review' | 'approving' | 'results';

function App() {
  const [state, setState] = useState<AppState>('input');
  const [error, setError] = useState<string | null>(null);
  const [extractResult, setExtractResult] = useState<ExtractResponse | null>(null);
  const [approveResult, setApproveResult] = useState<ApproveResponse | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, EditedValue>>({});
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingWord, setExportingWord] = useState(false);

  const handleExtract = async (ticker: string, model: LLMModel) => {
    setState('extracting');
    setError(null);
    setEditedValues({});

    try {
      const result = await extractData(ticker, model);
      setExtractResult(result);
      setState('review');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to extract data');
      setState('input');
    }
  };

  const handleValueChange = (metricKey: string, value: number | undefined, isPrior: boolean) => {
    setEditedValues((prev) => {
      const existing = prev[metricKey] || { metric_key: metricKey };
      return {
        ...prev,
        [metricKey]: isPrior
          ? { ...existing, value_prior: value }
          : { ...existing, value: value },
      };
    });
  };

  const handleResetValue = (metricKey: string, isPrior: boolean) => {
    setEditedValues((prev) => {
      const existing = prev[metricKey];
      if (!existing) return prev;

      const updated = { ...existing };
      if (isPrior) {
        delete updated.value_prior;
      } else {
        delete updated.value;
      }

      // If no edits left, remove the entry entirely
      if (updated.value === undefined && updated.value_prior === undefined) {
        const { [metricKey]: _, ...rest } = prev;
        return rest;
      }

      return { ...prev, [metricKey]: updated };
    });
  };

  const handleApprove = async () => {
    if (!extractResult) return;

    setState('approving');
    setError(null);

    try {
      const edits = Object.values(editedValues);
      const result = await approveExtraction(extractResult.session_id, edits);
      setApproveResult(result);
      setState('results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve extraction');
      setState('review');
    }
  };

  const handleExportExcel = async () => {
    if (!extractResult) return;

    setExportingExcel(true);
    setError(null);
    try {
      const blob = await exportExcel(extractResult.session_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${extractResult.ticker}_Financial_Analysis.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export Excel');
    } finally {
      setExportingExcel(false);
    }
  };

  const handleExportReport = async () => {
    if (!extractResult) return;

    setExportingWord(true);
    setError(null);
    try {
      const blob = await exportReport(extractResult.session_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${extractResult.ticker}_Financial_Report.docx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export report');
    } finally {
      setExportingWord(false);
    }
  };

  const handleStartOver = () => {
    setState('input');
    setExtractResult(null);
    setApproveResult(null);
    setEditedValues({});
    setError(null);
  };

  return (
    <div>
      <h1>Financial Reporting Tool</h1>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong>{' '}
          {error.includes('https://www.sec.gov') ? (
            <>
              {error.split('https://www.sec.gov')[0]}
              <a
                href={`https://www.sec.gov${error.split('https://www.sec.gov')[1].split(' ')[0]}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                SEC EDGAR Company Search
              </a>
              {error.split('https://www.sec.gov')[1].split(' ').slice(1).join(' ')}
            </>
          ) : (
            error
          )}
        </div>
      )}

      {/* Step 1: Ticker Input */}
      {state === 'input' && (
        <TickerInput onSubmit={handleExtract} />
      )}

      {/* Loading: Extracting */}
      {state === 'extracting' && (
        <div className="card">
          <div className="loading">
            <div className="spinner"></div>
          </div>
          <p className="text-center">Extracting financial data from SEC EDGAR...</p>
          <p className="text-center text-sm text-muted">
            This may take a moment as we fetch XBRL data and map concepts.
          </p>
        </div>
      )}

      {/* Step 2: Review Table */}
      {state === 'review' && extractResult && (
        <>
          <div className="card">
            <h2>{extractResult.company_name}{extractResult.ticker && !extractResult.ticker.startsWith('CIK') ? ` (${extractResult.ticker})` : ''}</h2>
            <p className="text-sm text-muted">
              {extractResult.ticker && !extractResult.ticker.startsWith('CIK') ? `Ticker: ${extractResult.ticker} | ` : ''}CIK: {extractResult.cik} | Fiscal Year: {extractResult.fiscal_year_end}
            </p>
          </div>

          {extractResult.llm_warnings.length > 0 && (
            <div className="alert alert-warning">
              <strong>Warnings:</strong>
              <ul>
                {extractResult.llm_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="card">
            <h3>Review Extracted Values</h3>
            <p className="text-sm text-muted mb-2">
              Click any value to edit. Click the source link to view the SEC filing.
            </p>
            <ReviewTable
              rawValues={extractResult.raw_values}
              fiscalYearEnd={extractResult.fiscal_year_end}
              fiscalYearEndPrior={extractResult.fiscal_year_end_prior}
              editedValues={editedValues}
              onValueChange={handleValueChange}
              onResetValue={handleResetValue}
            />
          </div>

          {extractResult.not_found.length > 0 && (
            <div className="card">
              <h3>Not Found Metrics</h3>
              <p className="text-sm text-muted mb-2">
                These metrics could not be mapped from XBRL data:
              </p>
              <ul>
                {extractResult.not_found.map((nf) => (
                  <li key={nf.metric_key}>
                    <strong>{nf.display_name}:</strong> {nf.llm_note}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {extractResult.unmapped_values.length > 0 && (
            <UnmappedSection unmappedValues={extractResult.unmapped_values} />
          )}

          {extractResult.llm_notes.length > 0 && (
            <div className="card">
              <h3>Extraction Notes</h3>
              <ul>
                {extractResult.llm_notes.map((note, i) => (
                  <li key={i}>{note}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="card">
            <p className="text-sm text-muted mb-2">
              Review the values above, edit if needed, then proceed to calculate metrics and export.
            </p>
            <div className="flex gap-2">
              <button className="primary" onClick={handleApprove}>
                Approve & Calculate (then Export)
              </button>
              <button className="secondary" onClick={handleStartOver}>
                Start Over
              </button>
            </div>
          </div>
        </>
      )}

      {/* Loading: Approving */}
      {state === 'approving' && (
        <div className="card">
          <div className="loading">
            <div className="spinner"></div>
          </div>
          <p className="text-center">Running calculations...</p>
        </div>
      )}

      {/* Step 3: Results */}
      {state === 'results' && extractResult && approveResult && (
        <>
          <div className="card">
            <h2>{extractResult.company_name}{extractResult.ticker && !extractResult.ticker.startsWith('CIK') ? ` (${extractResult.ticker})` : ''}</h2>
          </div>

          <CalculatedResults
            metrics={approveResult.metrics}
            ratios={approveResult.ratios}
            fiscalYearEnd={extractResult.fiscal_year_end}
            fiscalYearEndPrior={extractResult.fiscal_year_end_prior}
          />

          <ExportButtons
            onExportExcel={handleExportExcel}
            onExportReport={handleExportReport}
            exportingExcel={exportingExcel}
            exportingWord={exportingWord}
          />

          <div className="card">
            <div className="flex gap-2">
              <button className="secondary" onClick={() => setState('review')}>
                Back to Review
              </button>
              <button className="secondary" onClick={handleStartOver}>
                Start New Extraction
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default App;

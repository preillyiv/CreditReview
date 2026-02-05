/**
 * API client for the Financial Reporting backend.
 */

const API_BASE = '/api';

export interface SourceCitation {
  xbrl_concept: string;
  xbrl_label: string;
  filing_url: string;
  accession_number: string;
  filing_date: string;
  form_type: string;
  period_end: string;
  raw_value: number;
  statement: string | null;  // Which financial statement (e.g., "Income Statement")
}

export interface ExtractedValue {
  metric_key: string;
  display_name: string;
  value: number;
  value_prior: number;
  citation: SourceCitation | null;
  citation_prior: SourceCitation | null;
  llm_reasoning: string;
  is_editable: boolean;
}

export interface UnmappedValue {
  xbrl_concept: string;
  xbrl_label: string;
  value_current: number;
  value_prior: number;
  llm_note: string;
  citation: SourceCitation | null;
  citation_prior: SourceCitation | null;
}

export interface NotFoundMetric {
  metric_key: string;
  display_name: string;
  llm_note: string;
}

export interface ExtractResponse {
  session_id: string;
  ticker: string;
  company_name: string;
  cik: string;
  fiscal_year_end: string;
  fiscal_year_end_prior: string;
  raw_values: Record<string, ExtractedValue>;
  unmapped_values: UnmappedValue[];
  not_found: NotFoundMetric[];
  llm_notes: string[];
  llm_warnings: string[];
}

export interface CalculatedMetrics {
  tangible_net_worth: number;
  tangible_net_worth_prior: number;
  cash_balance: number;
  cash_balance_prior: number;
  top_line_revenue: number;
  top_line_revenue_prior: number;
  gross_profit: number;
  gross_profit_prior: number;
  gross_profit_margin: number;
  gross_profit_margin_prior: number;
  operating_income: number;
  operating_income_prior: number;
  operating_income_margin: number;
  operating_income_margin_prior: number;
  ebitda: number;
  ebitda_prior: number;
  ebitda_margin: number;
  ebitda_margin_prior: number;
  adjusted_ebitda: number;
  adjusted_ebitda_prior: number;
  adjusted_ebitda_margin: number;
  adjusted_ebitda_margin_prior: number;
  net_income: number;
  net_income_prior: number;
  net_income_margin: number;
  net_income_margin_prior: number;
}

export interface CalculatedRatios {
  current_ratio: number;
  current_ratio_prior: number;
  cash_ratio: number;
  cash_ratio_prior: number;
  debt_to_equity: number;
  debt_to_equity_prior: number;
  ebitda_interest_coverage: number;
  ebitda_interest_coverage_prior: number;
  net_debt_to_ebitda: number;
  net_debt_to_ebitda_prior: number;
  net_debt_to_adj_ebitda: number;
  net_debt_to_adj_ebitda_prior: number;
  days_sales_outstanding: number;
  days_sales_outstanding_prior: number;
  working_capital: number;
  working_capital_prior: number;
  return_on_assets: number;
  return_on_assets_prior: number;
  return_on_equity: number;
  return_on_equity_prior: number;
}

export interface CalculationStep {
  metric: string;
  formula: string;
  formula_excel: string;
  inputs: Record<string, number>;
  result: number;
}

export interface ApproveResponse {
  session_id: string;
  approved_at: string;
  metrics: CalculatedMetrics;
  ratios: CalculatedRatios;
  calculation_steps: CalculationStep[];
}

export interface EditedValue {
  metric_key: string;
  value?: number;
  value_prior?: number;
}

/**
 * Extract financial data for a ticker.
 */
export async function extractData(ticker: string, model?: string): Promise<ExtractResponse> {
  const response = await fetch(`${API_BASE}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ticker, model }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to extract data');
  }

  return response.json();
}

/**
 * Extract financial data from uploaded 10-K PDF.
 */
export async function extractDataFromPDF(file: File, model?: string): Promise<ExtractResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (model) {
    formData.append('model', model);
  }

  const response = await fetch(`${API_BASE}/extract-pdf`, {
    method: 'POST',
    body: formData,
    // No Content-Type header - browser sets multipart boundary automatically
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to extract data from PDF');
  }

  return response.json();
}

/**
 * Approve extraction with optional edits.
 */
export async function approveExtraction(
  sessionId: string,
  editedValues: EditedValue[] = []
): Promise<ApproveResponse> {
  const response = await fetch(`${API_BASE}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      edited_values: editedValues,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to approve extraction');
  }

  return response.json();
}

/**
 * Export to Excel.
 */
export async function exportExcel(sessionId: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/export/excel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to export Excel');
  }

  return response.blob();
}

/**
 * Export to Word report.
 */
export async function exportReport(
  sessionId: string,
  manualInputs: Record<string, string> = {},
  includeNarrative: boolean = true
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/export/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      manual_inputs: manualInputs,
      include_narrative: includeNarrative,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to export report');
  }

  return response.blob();
}

/**
 * Export to PDF report.
 */
export async function exportPdf(
  sessionId: string,
  manualInputs: Record<string, string> = {},
  includeNarrative: boolean = true
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/export/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      manual_inputs: manualInputs,
      include_narrative: includeNarrative,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to export PDF');
  }

  return response.blob();
}

/**
 * Format a number for display.
 */
export function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1e9) {
    return `$${(value / 1e9).toFixed(1)}B`;
  } else if (Math.abs(value) >= 1e6) {
    return `$${(value / 1e6).toFixed(1)}M`;
  } else {
    return `$${value.toLocaleString()}`;
  }
}

/**
 * Format a percentage for display.
 */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Format a ratio for display.
 */
export function formatRatio(value: number): string {
  return `${value.toFixed(2)}x`;
}

/**
 * Format delta for display.
 */
export function formatDelta(value: number, isPercent: boolean = false): string {
  const sign = value >= 0 ? '+' : '';
  if (isPercent) {
    return `${sign}${(value * 100).toFixed(1)}%`;
  }
  if (Math.abs(value) >= 1e9) {
    return `${sign}${(value / 1e9).toFixed(1)}B`;
  } else if (Math.abs(value) >= 1e6) {
    return `${sign}${(value / 1e6).toFixed(1)}M`;
  }
  return `${sign}${value.toLocaleString()}`;
}

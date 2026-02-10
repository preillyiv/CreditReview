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

export interface VerificationCheck {
  check_id: string;
  description: string;
  formula: string;
  lhs_value: number;
  rhs_value: number;
  difference: number;
  tolerance: number;
  passed: boolean;
  severity: string;
  year: string;
  skipped: boolean;
}

export interface VerificationResult {
  checks: VerificationCheck[];
  pass_count: number;
  fail_count: number;
  warning_count: number;
  error_count: number;
  skip_count: number;
}

export interface StatementLineItem {
  metric_key: string;
  display_name: string;
  statement: string;
  section: string;
  indent_level: number;
  is_subtotal: boolean;
  is_bold: boolean;
  sort_order: number;
}

export interface ExtractResponse {
  session_id: string;
  ticker: string;
  company_name: string;
  cik: string;
  fiscal_year_end: string;
  fiscal_year_end_prior: string;
  unit: string;  // Unit of financial metrics (e.g., "millions", "thousands", "dollars")
  raw_values: Record<string, ExtractedValue>;
  unmapped_values: UnmappedValue[];
  not_found: NotFoundMetric[];
  llm_notes: string[];
  llm_warnings: string[];
  verification: VerificationResult | null;
}

// === Financial Statement Line Item Registries ===

export const INCOME_STATEMENT_ITEMS: StatementLineItem[] = [
  { metric_key: 'revenue', display_name: 'Top Line Revenue', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: false, is_bold: true, sort_order: 0 },
  { metric_key: 'cost_of_revenue', display_name: 'Cost of Revenue', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 1 },
  { metric_key: 'gross_profit', display_name: 'Gross Profit', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 2 },
  { metric_key: 'sga_expense', display_name: 'Selling, General & Administrative', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 3 },
  { metric_key: 'rd_expense', display_name: 'Research & Development', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 4 },
  { metric_key: 'depreciation_amortization', display_name: 'Depreciation & Amortization', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 5 },
  { metric_key: 'other_operating_expense', display_name: 'Other Operating Expenses', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 6 },
  { metric_key: 'total_operating_expenses', display_name: 'Total Operating Expenses', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 7 },
  { metric_key: 'operating_income', display_name: 'Operating Income', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 8 },
  { metric_key: 'interest_expense', display_name: 'Interest Expense', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 9 },
  { metric_key: 'other_income_expense', display_name: 'Other Income/Expense, Net', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 10 },
  { metric_key: 'income_before_tax', display_name: 'Income Before Income Tax', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 11 },
  { metric_key: 'income_tax_expense', display_name: 'Income Tax Expense', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 12 },
  { metric_key: 'net_income', display_name: 'Net Income', statement: 'income_statement', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 13 },
  { metric_key: 'stock_compensation', display_name: 'Stock-Based Compensation', statement: 'income_statement', section: '', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 14 },
];

export const BALANCE_SHEET_ITEMS: StatementLineItem[] = [
  { metric_key: 'cash', display_name: 'Cash & Cash Equivalents', statement: 'balance_sheet', section: 'Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 0 },
  { metric_key: 'short_term_investments', display_name: 'Short-term Investments', statement: 'balance_sheet', section: 'Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 1 },
  { metric_key: 'accounts_receivable', display_name: 'Accounts Receivable', statement: 'balance_sheet', section: 'Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 2 },
  { metric_key: 'inventories', display_name: 'Inventories', statement: 'balance_sheet', section: 'Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 3 },
  { metric_key: 'other_current_assets', display_name: 'Other Current Assets', statement: 'balance_sheet', section: 'Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 4 },
  { metric_key: 'current_assets', display_name: 'Total Current Assets', statement: 'balance_sheet', section: 'Current Assets', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 5 },
  { metric_key: 'ppe_net', display_name: 'Property, Plant & Equipment, Net', statement: 'balance_sheet', section: 'Non-Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 6 },
  { metric_key: 'goodwill', display_name: 'Goodwill', statement: 'balance_sheet', section: 'Non-Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 7 },
  { metric_key: 'intangible_assets', display_name: 'Intangible Assets', statement: 'balance_sheet', section: 'Non-Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 8 },
  { metric_key: 'other_noncurrent_assets', display_name: 'Other Non-Current Assets', statement: 'balance_sheet', section: 'Non-Current Assets', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 9 },
  { metric_key: 'total_assets', display_name: 'Total Assets', statement: 'balance_sheet', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 10 },
  { metric_key: 'accounts_payable', display_name: 'Accounts Payable', statement: 'balance_sheet', section: 'Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 11 },
  { metric_key: 'short_term_debt', display_name: 'Short-term Debt', statement: 'balance_sheet', section: 'Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 12 },
  { metric_key: 'accrued_liabilities', display_name: 'Accrued Liabilities', statement: 'balance_sheet', section: 'Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 13 },
  { metric_key: 'other_current_liabilities', display_name: 'Other Current Liabilities', statement: 'balance_sheet', section: 'Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 14 },
  { metric_key: 'current_liabilities', display_name: 'Total Current Liabilities', statement: 'balance_sheet', section: 'Current Liabilities', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 15 },
  { metric_key: 'long_term_debt', display_name: 'Long-term Debt', statement: 'balance_sheet', section: 'Non-Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 16 },
  { metric_key: 'other_noncurrent_liabilities', display_name: 'Other Non-Current Liabilities', statement: 'balance_sheet', section: 'Non-Current Liabilities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 17 },
  { metric_key: 'total_liabilities', display_name: 'Total Liabilities', statement: 'balance_sheet', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 18 },
  { metric_key: 'stockholders_equity', display_name: "Stockholders' Equity", statement: 'balance_sheet', section: 'Equity', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 19 },
];

export const CASH_FLOW_ITEMS: StatementLineItem[] = [
  { metric_key: 'cf_net_income', display_name: 'Net Income', statement: 'cash_flow', section: 'Operating Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 0 },
  { metric_key: 'cf_depreciation_amortization', display_name: 'Depreciation & Amortization', statement: 'cash_flow', section: 'Operating Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 1 },
  { metric_key: 'cf_stock_compensation', display_name: 'Stock-Based Compensation', statement: 'cash_flow', section: 'Operating Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 2 },
  { metric_key: 'cf_working_capital_changes', display_name: 'Changes in Working Capital', statement: 'cash_flow', section: 'Operating Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 3 },
  { metric_key: 'cf_other_operating', display_name: 'Other Operating Activities', statement: 'cash_flow', section: 'Operating Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 4 },
  { metric_key: 'cash_from_operations', display_name: 'Cash from Operations', statement: 'cash_flow', section: 'Operating Activities', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 5 },
  { metric_key: 'capital_expenditures', display_name: 'Capital Expenditures', statement: 'cash_flow', section: 'Investing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 6 },
  { metric_key: 'acquisitions', display_name: 'Acquisitions', statement: 'cash_flow', section: 'Investing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 7 },
  { metric_key: 'cf_other_investing', display_name: 'Other Investing Activities', statement: 'cash_flow', section: 'Investing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 8 },
  { metric_key: 'cash_from_investing', display_name: 'Cash from Investing', statement: 'cash_flow', section: 'Investing Activities', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 9 },
  { metric_key: 'debt_issuance_repayment', display_name: 'Debt Issuance/Repayment, Net', statement: 'cash_flow', section: 'Financing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 10 },
  { metric_key: 'stock_repurchases', display_name: 'Stock Repurchases', statement: 'cash_flow', section: 'Financing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 11 },
  { metric_key: 'dividends_paid', display_name: 'Dividends Paid', statement: 'cash_flow', section: 'Financing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 12 },
  { metric_key: 'cf_other_financing', display_name: 'Other Financing Activities', statement: 'cash_flow', section: 'Financing Activities', indent_level: 1, is_subtotal: false, is_bold: false, sort_order: 13 },
  { metric_key: 'cash_from_financing', display_name: 'Cash from Financing', statement: 'cash_flow', section: 'Financing Activities', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 14 },
  { metric_key: 'net_change_in_cash', display_name: 'Net Change in Cash', statement: 'cash_flow', section: '', indent_level: 0, is_subtotal: true, is_bold: true, sort_order: 15 },
];

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
 * Re-run verification checks with current edited values.
 */
export async function verifySession(
  sessionId: string,
  editedValues: EditedValue[] = []
): Promise<VerificationResult> {
  const response = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      edited_values: editedValues,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to verify');
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
 * Format a number for display as currency with appropriate scale suffix (M for millions, B for billions).
 * @param value - The numeric value in dollars (after backend normalization)
 * @param unit - The original unit for context (not used in formatting, included for consistency)
 */
export function formatCurrency(value: number, unit?: string): string {
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

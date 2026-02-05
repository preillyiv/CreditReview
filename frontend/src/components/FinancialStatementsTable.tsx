import { ExtractedValue, formatCurrency } from '../api/client';
import { SourcePopover } from './SourcePopover';

interface FinancialStatementsTableProps {
  rawValues: Record<string, ExtractedValue>;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  editedValues: Record<string, any>;
  onValueChange: (metricKey: string, value: number | undefined, isPrior: boolean) => void;
  onResetValue?: (metricKey: string, isPrior: boolean) => void;
}

interface LineItem {
  key: string;
  label: string;
  indent: number;
  isBold: boolean;
  isSubtotal: boolean;
}

const FINANCIAL_STATEMENT_SECTIONS: LineItem[] = [
  // INCOME STATEMENT
  { key: 'revenue', label: 'Top Line Revenue', indent: 0, isBold: true, isSubtotal: false },
  { key: 'cost_of_revenue', label: 'Cost of Revenue', indent: 1, isBold: false, isSubtotal: false },
  { key: 'gross_profit', label: 'Gross Profit', indent: 0, isBold: true, isSubtotal: true },
  { key: 'depreciation_amortization', label: 'Depreciation & Amortization', indent: 1, isBold: false, isSubtotal: false },
  { key: 'interest_expense', label: 'Interest Expense', indent: 1, isBold: false, isSubtotal: false },
  { key: 'operating_income', label: 'Operating Income', indent: 0, isBold: true, isSubtotal: true },
  { key: 'net_income', label: 'Net Income', indent: 0, isBold: true, isSubtotal: true },

  // PROFITABILITY MARGINS
  { key: 'gross_margin', label: 'Gross Profit Margin', indent: 1, isBold: false, isSubtotal: false },
  { key: 'operating_margin', label: 'Operating Income Margin', indent: 1, isBold: false, isSubtotal: false },
  { key: 'net_margin', label: 'Net Income Margin', indent: 1, isBold: false, isSubtotal: false },

  // BALANCE SHEET - ASSETS
  { key: 'current_assets', label: 'Current Assets', indent: 1, isBold: true, isSubtotal: false },
  { key: 'accounts_receivable', label: 'Accounts Receivable', indent: 2, isBold: false, isSubtotal: false },
  { key: 'intangible_assets', label: 'Intangible Assets', indent: 1, isBold: false, isSubtotal: false },
  { key: 'goodwill', label: 'Goodwill', indent: 1, isBold: false, isSubtotal: false },
  { key: 'total_assets', label: 'Total Assets', indent: 0, isBold: true, isSubtotal: true },

  // BALANCE SHEET - LIABILITIES
  { key: 'current_liabilities', label: 'Current Liabilities', indent: 1, isBold: true, isSubtotal: false },
  { key: 'total_debt', label: 'Total Debt', indent: 1, isBold: false, isSubtotal: false },
  { key: 'total_liabilities', label: 'Total Liabilities', indent: 0, isBold: true, isSubtotal: true },

  // BALANCE SHEET - EQUITY
  { key: 'stockholders_equity', label: "Stockholders' Equity", indent: 0, isBold: true, isSubtotal: false },
  { key: 'tangible_net_worth', label: 'Tangible Net Worth', indent: 0, isBold: true, isSubtotal: false },

  // LIQUIDITY
  { key: 'cash', label: 'Cash & Cash Equivalents', indent: 0, isBold: true, isSubtotal: false },
];

export function FinancialStatementsTable({
  rawValues,
  fiscalYearEnd,
  fiscalYearEndPrior,
  editedValues,
  onValueChange,
  onResetValue,
}: FinancialStatementsTableProps) {
  const getCurrentValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    if (edited?.value !== undefined) {
      return edited.value;
    }
    return rawValues[metricKey]?.value ?? 0;
  };

  const getPriorValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    if (edited?.value_prior !== undefined) {
      return edited.value_prior;
    }
    return rawValues[metricKey]?.value_prior ?? 0;
  };

  const isPercentage = (key: string): boolean => {
    return key.includes('margin') || key.includes('ratio') || key.includes('return');
  };

  const formatValue = (value: number, key: string): string => {
    if (isPercentage(key)) {
      return `${(value * 100).toFixed(1)}%`;
    }
    return formatCurrency(value);
  };

  const getFiscalYear = (dateStr: string): string => {
    return dateStr.split('-')[0] || dateStr;
  };

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#1f4e79', color: 'white' }}>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'left' }}>
              Financial Statement
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
              FY {getFiscalYear(fiscalYearEnd)}
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
              FY {getFiscalYear(fiscalYearEndPrior)}
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
              Delta
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
              Source
            </th>
          </tr>
        </thead>
        <tbody>
          {FINANCIAL_STATEMENT_SECTIONS.map((item) => {
            // Skip items not in rawValues
            if (!rawValues[item.key]) {
              return null;
            }

            const ev = rawValues[item.key];
            const currentVal = getCurrentValue(item.key);
            const priorVal = getPriorValue(item.key);
            const delta = currentVal - priorVal;
            const backgroundColor = delta >= 0 ? '#d4edda' : '#f8d7da';
            const indentPx = item.indent * 20;

            return (
              <tr key={item.key} style={{ backgroundColor: item.isBold ? '#f5f5f5' : 'white' }}>
                <td
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    paddingLeft: `${1 + indentPx}rem`,
                    fontWeight: item.isBold ? 'bold' : 'normal',
                  }}
                >
                  <span className="tooltip">
                    {item.label}
                    {ev.llm_reasoning && (
                      <span className="tooltip-text">{ev.llm_reasoning}</span>
                    )}
                  </span>
                </td>
                <td
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    textAlign: 'center',
                    fontWeight: item.isBold ? 'bold' : 'normal',
                  }}
                >
                  {formatValue(currentVal, item.key)}
                </td>
                <td
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    textAlign: 'center',
                    fontWeight: item.isBold ? 'bold' : 'normal',
                  }}
                >
                  {formatValue(priorVal, item.key)}
                </td>
                <td
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    textAlign: 'center',
                    backgroundColor: isPercentage(item.key) ? 'white' : backgroundColor,
                    fontWeight: item.isBold ? 'bold' : 'normal',
                  }}
                >
                  {formatValue(delta, item.key)}
                </td>
                <td
                  style={{
                    padding: '0.75rem',
                    border: '1px solid #ddd',
                    textAlign: 'center',
                  }}
                >
                  {ev.citation && <SourcePopover citation={ev.citation} />}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

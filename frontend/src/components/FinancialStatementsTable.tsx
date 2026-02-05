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
  indent: boolean;
  isBold: boolean;
}

function StatementRow({
  item,
  ev,
  currentVal,
  priorVal,
  delta,
}: {
  item: LineItem;
  ev: ExtractedValue;
  currentVal: number;
  priorVal: number;
  delta: number;
}) {
  const isPercentage = item.key.includes('margin');
  const deltaColor = !isPercentage && (delta >= 0 ? '#d4edda' : '#f8d7da');

  const formatValue = (value: number) => {
    if (isPercentage) {
      return `${(value * 100).toFixed(1)}%`;
    }
    return formatCurrency(value);
  };

  return (
    <tr style={{ backgroundColor: item.isBold ? '#f5f5f5' : 'white' }}>
      <td
        style={{
          padding: '0.75rem',
          border: '1px solid #ddd',
          paddingLeft: item.indent ? '2rem' : '0.75rem',
          fontWeight: item.isBold ? '600' : 'normal',
          textAlign: 'left',
        }}
      >
        <span className="tooltip">
          {item.label}
          {ev.llm_reasoning && <span className="tooltip-text">{ev.llm_reasoning}</span>}
        </span>
      </td>
      <td style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'right', fontWeight: item.isBold ? '600' : 'normal' }}>
        {formatValue(currentVal)}
      </td>
      <td style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'right', fontWeight: item.isBold ? '600' : 'normal' }}>
        {formatValue(priorVal)}
      </td>
      <td
        style={{
          padding: '0.75rem',
          border: '1px solid #ddd',
          textAlign: 'right',
          backgroundColor: deltaColor,
          fontWeight: item.isBold ? '600' : 'normal',
        }}
      >
        {formatValue(delta)}
      </td>
      <td style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
        {ev.citation && <SourcePopover citation={ev.citation} />}
      </td>
    </tr>
  );
}

function StatementTable({
  title,
  items,
  rawValues,
  fiscalYearEnd,
  fiscalYearEndPrior,
  editedValues,
}: {
  title: string;
  items: LineItem[];
  rawValues: Record<string, ExtractedValue>;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  editedValues: Record<string, any>;
}) {
  const getCurrentValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    return edited?.value !== undefined ? edited.value : rawValues[metricKey]?.value ?? 0;
  };

  const getPriorValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    return edited?.value_prior !== undefined ? edited.value_prior : rawValues[metricKey]?.value_prior ?? 0;
  };

  const getFiscalYear = (dateStr: string): string => dateStr.split('-')[0] || dateStr;

  // Filter to only items that exist in rawValues
  const visibleItems = items.filter((item) => rawValues[item.key]);

  if (visibleItems.length === 0) return null;

  return (
    <div style={{ marginBottom: '2rem' }}>
      <h4 style={{ marginBottom: '0.75rem', color: '#1f4e79' }}>{title}</h4>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
        <thead>
          <tr style={{ backgroundColor: '#1f4e79', color: 'white' }}>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'left' }}>Item</th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'right', minWidth: '100px' }}>
              FY {getFiscalYear(fiscalYearEnd)}
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'right', minWidth: '100px' }}>
              FY {getFiscalYear(fiscalYearEndPrior)}
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'right', minWidth: '100px' }}>
              Delta
            </th>
            <th style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center', minWidth: '80px' }}>
              Source
            </th>
          </tr>
        </thead>
        <tbody>
          {visibleItems.map((item) => {
            const ev = rawValues[item.key];
            const currentVal = getCurrentValue(item.key);
            const priorVal = getPriorValue(item.key);
            const delta = currentVal - priorVal;

            return (
              <StatementRow
                key={item.key}
                item={item}
                ev={ev}
                currentVal={currentVal}
                priorVal={priorVal}
                delta={delta}
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function FinancialStatementsTable({
  rawValues,
  fiscalYearEnd,
  fiscalYearEndPrior,
  editedValues,
  onValueChange,
  onResetValue,
}: FinancialStatementsTableProps) {
  const incomeStatementItems: LineItem[] = [
    { key: 'revenue', label: 'Top Line Revenue', indent: false, isBold: true },
    { key: 'cost_of_revenue', label: 'Cost of Revenue', indent: true, isBold: false },
    { key: 'gross_profit', label: 'Gross Profit', indent: false, isBold: true },
    { key: 'depreciation_amortization', label: 'Depreciation & Amortization', indent: true, isBold: false },
    { key: 'interest_expense', label: 'Interest Expense', indent: true, isBold: false },
    { key: 'operating_income', label: 'Operating Income', indent: false, isBold: true },
    { key: 'net_income', label: 'Net Income', indent: false, isBold: true },
    { key: 'gross_margin', label: 'Gross Profit Margin %', indent: true, isBold: false },
    { key: 'operating_margin', label: 'Operating Income Margin %', indent: true, isBold: false },
    { key: 'net_margin', label: 'Net Income Margin %', indent: true, isBold: false },
  ];

  const balanceSheetItems: LineItem[] = [
    { key: 'current_assets', label: 'Current Assets', indent: false, isBold: true },
    { key: 'accounts_receivable', label: 'Accounts Receivable', indent: true, isBold: false },
    { key: 'intangible_assets', label: 'Intangible Assets', indent: false, isBold: false },
    { key: 'goodwill', label: 'Goodwill', indent: false, isBold: false },
    { key: 'total_assets', label: 'Total Assets', indent: false, isBold: true },
    { key: 'current_liabilities', label: 'Current Liabilities', indent: false, isBold: true },
    { key: 'total_debt', label: 'Total Debt', indent: true, isBold: false },
    { key: 'total_liabilities', label: 'Total Liabilities', indent: false, isBold: true },
    { key: 'stockholders_equity', label: "Stockholders' Equity", indent: false, isBold: true },
  ];

  const liquidityItems: LineItem[] = [
    { key: 'cash', label: 'Cash & Cash Equivalents', indent: false, isBold: true },
    { key: 'tangible_net_worth', label: 'Tangible Net Worth', indent: false, isBold: true },
  ];

  return (
    <div style={{ width: '100%' }}>
      <StatementTable
        title="Income Statement"
        items={incomeStatementItems}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
      />
      <StatementTable
        title="Balance Sheet"
        items={balanceSheetItems}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
      />
      <StatementTable
        title="Liquidity & Equity"
        items={liquidityItems}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
      />
    </div>
  );
}

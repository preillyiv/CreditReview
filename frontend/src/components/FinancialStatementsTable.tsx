import { useState } from 'react';
import {
  ExtractedValue,
  VerificationResult,
  VerificationCheck,
  StatementLineItem,
  INCOME_STATEMENT_ITEMS,
  BALANCE_SHEET_ITEMS,
  CASH_FLOW_ITEMS,
  formatCurrency,
} from '../api/client';
import { SourcePopover } from './SourcePopover';

interface FinancialStatementsTableProps {
  rawValues: Record<string, ExtractedValue>;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  editedValues: Record<string, any>;
  onValueChange: (metricKey: string, value: number | undefined, isPrior: boolean) => void;
  onResetValue?: (metricKey: string, isPrior: boolean) => void;
  verification: VerificationResult | null;
}

function EditableCell({
  metricKey,
  value,
  originalValue,
  isPrior,
  isBold,
  onValueChange,
  onResetValue,
}: {
  metricKey: string;
  value: number;
  originalValue: number;
  isPrior: boolean;
  isBold: boolean;
  onValueChange: (metricKey: string, value: number | undefined, isPrior: boolean) => void;
  onResetValue?: (metricKey: string, isPrior: boolean) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [inputVal, setInputVal] = useState('');
  const isEdited = value !== originalValue;

  const handleClick = () => {
    setInputVal(String(value));
    setEditing(true);
  };

  const handleBlur = () => {
    setEditing(false);
    const parsed = parseFloat(inputVal);
    if (!isNaN(parsed) && parsed !== originalValue) {
      onValueChange(metricKey, parsed, isPrior);
    } else if (inputVal === '' || parsed === originalValue) {
      onValueChange(metricKey, undefined, isPrior);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      (e.target as HTMLInputElement).blur();
    } else if (e.key === 'Escape') {
      setEditing(false);
    }
  };

  if (editing) {
    return (
      <td style={{ padding: '0.25rem', border: '1px solid #ddd', textAlign: 'center' }}>
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          autoFocus
          style={{
            width: '100%',
            padding: '0.25rem',
            textAlign: 'center',
            border: '2px solid #4472C4',
            borderRadius: '2px',
            fontSize: '0.9rem',
          }}
        />
      </td>
    );
  }

  return (
    <td
      onClick={handleClick}
      style={{
        padding: '0.75rem',
        border: '1px solid #ddd',
        textAlign: 'center',
        fontWeight: isBold ? '600' : 'normal',
        cursor: 'pointer',
        backgroundColor: isEdited ? '#fff3cd' : undefined,
        position: 'relative',
      }}
      title="Click to edit"
    >
      {formatCurrency(value)}
      {isEdited && onResetValue && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onResetValue(metricKey, isPrior);
          }}
          style={{
            position: 'absolute',
            top: '2px',
            right: '2px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '0.7rem',
            color: '#999',
            padding: '0',
            lineHeight: '1',
          }}
          title="Reset to original"
        >
          x
        </button>
      )}
    </td>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <tr>
      <td
        colSpan={5}
        style={{
          padding: '0.5rem 0.75rem',
          fontWeight: 600,
          fontSize: '0.85rem',
          color: '#1f4e79',
          backgroundColor: '#e8ecf0',
          borderBottom: '1px solid #ccc',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        {label}
      </td>
    </tr>
  );
}

function StatementSection({
  title,
  items,
  rawValues,
  fiscalYearEnd,
  fiscalYearEndPrior,
  editedValues,
  onValueChange,
  onResetValue,
  checks: _checks,
}: {
  title: string;
  items: StatementLineItem[];
  rawValues: Record<string, ExtractedValue>;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  editedValues: Record<string, any>;
  onValueChange: (metricKey: string, value: number | undefined, isPrior: boolean) => void;
  onResetValue?: (metricKey: string, isPrior: boolean) => void;
  checks: VerificationCheck[];
}) {
  const [expanded, setExpanded] = useState(true);

  // Filter to items present in rawValues
  const visibleItems = items.filter((item) => rawValues[item.metric_key]);
  const totalItems = items.length;
  const foundItems = visibleItems.length;

  if (foundItems === 0) return null;

  const getCurrentValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    return edited?.value !== undefined ? edited.value : rawValues[metricKey]?.value ?? 0;
  };

  const getPriorValue = (metricKey: string): number => {
    const edited = editedValues[metricKey];
    return edited?.value_prior !== undefined ? edited.value_prior : rawValues[metricKey]?.value_prior ?? 0;
  };

  const getFiscalYear = (dateStr: string): string => dateStr.split('-')[0] || dateStr;

  // Track sections for section headers
  let lastSection = '';

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1rem',
          backgroundColor: '#1f4e79',
          color: 'white',
          cursor: 'pointer',
          borderRadius: expanded ? '6px 6px 0 0' : '6px',
          userSelect: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: '0.5rem', fontSize: '0.8rem' }}>{expanded ? '\u25BC' : '\u25B6'}</span>
          <h4 style={{ margin: 0, fontSize: '1rem' }}>{title}</h4>
          <span style={{ marginLeft: '0.75rem', fontSize: '0.8rem', opacity: 0.8 }}>
            {foundItems} of {totalItems} items found
          </span>
          {/* Verification badge hidden for now */}
        </div>
      </div>

      {expanded && (
        <div style={{ border: '1px solid #ddd', borderTop: 'none', borderRadius: '0 0 6px 6px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
            <thead>
              <tr>
                {['Item', `FY ${getFiscalYear(fiscalYearEnd)}`, `FY ${getFiscalYear(fiscalYearEndPrior)}`, 'Delta', 'Source'].map(
                  (header, idx) => (
                    <th
                      key={header}
                      style={{
                        padding: '0.5rem 0.75rem',
                        border: '1px solid #ddd',
                        textAlign: idx === 0 ? 'left' : 'center',
                        minWidth: idx === 0 ? 'auto' : idx === 4 ? '80px' : '100px',
                        fontSize: '0.85rem',
                      }}
                    >
                      {header}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {visibleItems.map((item) => {
                const ev = rawValues[item.metric_key];
                const currentVal = getCurrentValue(item.metric_key);
                const priorVal = getPriorValue(item.metric_key);
                const delta = currentVal - priorVal;
                const deltaColor = delta >= 0 ? '#d4edda' : '#f8d7da';

                // Insert section header if section changed
                const rows: React.ReactNode[] = [];
                if (item.section && item.section !== lastSection) {
                  lastSection = item.section;
                  rows.push(<SectionHeader key={`section-${item.section}`} label={item.section} />);
                } else if (!item.section && lastSection) {
                  lastSection = '';
                }

                rows.push(
                  <tr key={item.metric_key} style={{ backgroundColor: item.is_bold ? '#f8f9fa' : 'white' }}>
                    <td
                      style={{
                        padding: '0.75rem',
                        paddingLeft: item.indent_level > 0 ? '2rem' : '0.75rem',
                        border: '1px solid #ddd',
                        fontWeight: item.is_bold ? '600' : 'normal',
                        textAlign: 'left',
                        borderTop: item.is_subtotal ? '2px solid #999' : undefined,
                      }}
                    >
                      <span className="tooltip">
                        {item.display_name}
                        {ev.llm_reasoning && <span className="tooltip-text">{ev.llm_reasoning}</span>}
                      </span>
                    </td>
                    <EditableCell
                      metricKey={item.metric_key}
                      value={currentVal}
                      originalValue={ev.value}
                      isPrior={false}
                      isBold={item.is_bold}
                      onValueChange={onValueChange}
                      onResetValue={onResetValue}
                    />
                    <EditableCell
                      metricKey={item.metric_key}
                      value={priorVal}
                      originalValue={ev.value_prior}
                      isPrior={true}
                      isBold={item.is_bold}
                      onValueChange={onValueChange}
                      onResetValue={onResetValue}
                    />
                    <td
                      style={{
                        padding: '0.75rem',
                        border: '1px solid #ddd',
                        textAlign: 'center',
                        backgroundColor: deltaColor,
                        fontWeight: item.is_bold ? '600' : 'normal',
                      }}
                    >
                      {formatCurrency(delta)}
                    </td>
                    <td style={{ padding: '0.75rem', border: '1px solid #ddd', textAlign: 'center' }}>
                      {ev.citation && <SourcePopover citation={ev.citation} />}
                    </td>
                  </tr>
                );

                return rows;
              })}
            </tbody>
          </table>

          {/* Verification alerts hidden for now */}
        </div>
      )}
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
  verification,
}: FinancialStatementsTableProps) {
  // Get checks relevant to each statement
  const getChecksForStatement = (statementType: string): VerificationCheck[] => {
    if (!verification) return [];
    const checkMap: Record<string, string[]> = {
      income_statement: ['gross_profit', 'operating_income', 'net_income'],
      balance_sheet: ['current_assets', 'accounting_equation', 'current_liabilities'],
      cash_flow: ['cash_flow'],
    };
    const relevantIds = checkMap[statementType] || [];
    return verification.checks.filter((c) => relevantIds.includes(c.check_id));
  };

  return (
    <div style={{ width: '100%' }}>
      <StatementSection
        title="Income Statement"
        items={INCOME_STATEMENT_ITEMS}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
        onValueChange={onValueChange}
        onResetValue={onResetValue}
        checks={getChecksForStatement('income_statement')}
      />
      <StatementSection
        title="Balance Sheet"
        items={BALANCE_SHEET_ITEMS}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
        onValueChange={onValueChange}
        onResetValue={onResetValue}
        checks={getChecksForStatement('balance_sheet')}
      />
      <StatementSection
        title="Cash Flow Statement"
        items={CASH_FLOW_ITEMS}
        rawValues={rawValues}
        fiscalYearEnd={fiscalYearEnd}
        fiscalYearEndPrior={fiscalYearEndPrior}
        editedValues={editedValues}
        onValueChange={onValueChange}
        onResetValue={onResetValue}
        checks={getChecksForStatement('cash_flow')}
      />
    </div>
  );
}

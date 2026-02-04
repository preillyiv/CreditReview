import { useState } from 'react';
import { ExtractedValue, EditedValue, formatCurrency } from '../api/client';
import { SourcePopover } from './SourcePopover';

interface ReviewTableProps {
  rawValues: Record<string, ExtractedValue>;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  editedValues: Record<string, EditedValue>;
  onValueChange: (metricKey: string, value: number | undefined, isPrior: boolean) => void;
  onResetValue?: (metricKey: string, isPrior: boolean) => void;
}

export function ReviewTable({
  rawValues,
  fiscalYearEnd,
  fiscalYearEndPrior,
  editedValues,
  onValueChange,
  onResetValue,
}: ReviewTableProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  const metrics = Object.values(rawValues);

  const getCurrentValue = (ev: ExtractedValue): number => {
    const edited = editedValues[ev.metric_key];
    if (edited?.value !== undefined) {
      return edited.value;
    }
    return ev.value;
  };

  const getPriorValue = (ev: ExtractedValue): number => {
    const edited = editedValues[ev.metric_key];
    if (edited?.value_prior !== undefined) {
      return edited.value_prior;
    }
    return ev.value_prior;
  };

  const isEdited = (metricKey: string, isPrior: boolean): boolean => {
    const edited = editedValues[metricKey];
    if (!edited) return false;
    const original = rawValues[metricKey];
    if (!original) return false;

    if (isPrior) {
      // Only show as edited if value actually changed from original
      return edited.value_prior !== undefined && edited.value_prior !== original.value_prior;
    } else {
      return edited.value !== undefined && edited.value !== original.value;
    }
  };

  const startEditing = (metricKey: string, isPrior: boolean, currentValue: number) => {
    const cellId = `${metricKey}-${isPrior ? 'prior' : 'current'}`;
    setEditingCell(cellId);
    setEditValue(currentValue.toString());
  };

  const finishEditing = (metricKey: string, isPrior: boolean) => {
    const newValue = parseFloat(editValue);
    if (!isNaN(newValue)) {
      onValueChange(metricKey, newValue, isPrior);
    }
    setEditingCell(null);
    setEditValue('');
  };

  const cancelEditing = () => {
    setEditingCell(null);
    setEditValue('');
  };

  const getFiscalYear = (dateStr: string): string => {
    return dateStr.split('-')[0] || dateStr;
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th className="text-right">FY {getFiscalYear(fiscalYearEnd)}</th>
          <th className="text-right">FY {getFiscalYear(fiscalYearEndPrior)}</th>
          <th className="text-right">Delta</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody>
        {metrics.map((ev) => {
          const currentVal = getCurrentValue(ev);
          const priorVal = getPriorValue(ev);
          const delta = currentVal - priorVal;
          const currentCellId = `${ev.metric_key}-current`;
          const priorCellId = `${ev.metric_key}-prior`;

          return (
            <tr key={ev.metric_key}>
              <td>
                <span className="tooltip">
                  {ev.display_name}
                  {ev.llm_reasoning && (
                    <span className="tooltip-text">{ev.llm_reasoning}</span>
                  )}
                </span>
              </td>
              <td className="text-right">
                {editingCell === currentCellId ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => finishEditing(ev.metric_key, false)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') finishEditing(ev.metric_key, false);
                      if (e.key === 'Escape') cancelEditing();
                    }}
                    autoFocus
                    style={{ width: '100px', textAlign: 'right' }}
                  />
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                    <span
                      className={`editable-cell ${isEdited(ev.metric_key, false) ? 'edited-value' : ''}`}
                      onClick={() => startEditing(ev.metric_key, false, currentVal)}
                    >
                      {formatCurrency(currentVal)}
                    </span>
                    {isEdited(ev.metric_key, false) && onResetValue && (
                      <button
                        className="reset-btn"
                        onClick={(e) => { e.stopPropagation(); onResetValue(ev.metric_key, false); }}
                        title={`Reset to original: ${formatCurrency(ev.value)}`}
                      >
                        ↺
                      </button>
                    )}
                  </span>
                )}
              </td>
              <td className="text-right">
                {editingCell === priorCellId ? (
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    onBlur={() => finishEditing(ev.metric_key, true)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') finishEditing(ev.metric_key, true);
                      if (e.key === 'Escape') cancelEditing();
                    }}
                    autoFocus
                    style={{ width: '100px', textAlign: 'right' }}
                  />
                ) : (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                    <span
                      className={`editable-cell ${isEdited(ev.metric_key, true) ? 'edited-value' : ''}`}
                      onClick={() => startEditing(ev.metric_key, true, priorVal)}
                    >
                      {formatCurrency(priorVal)}
                    </span>
                    {isEdited(ev.metric_key, true) && onResetValue && (
                      <button
                        className="reset-btn"
                        onClick={(e) => { e.stopPropagation(); onResetValue(ev.metric_key, true); }}
                        title={`Reset to original: ${formatCurrency(ev.value_prior)}`}
                      >
                        ↺
                      </button>
                    )}
                  </span>
                )}
              </td>
              <td className={`text-right ${delta >= 0 ? 'positive' : 'negative'}`}>
                {formatCurrency(delta)}
              </td>
              <td>
                {ev.citation && <SourcePopover citation={ev.citation} />}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

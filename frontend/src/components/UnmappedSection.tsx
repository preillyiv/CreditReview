import { UnmappedValue, formatCurrency } from '../api/client';
import { SourcePopover } from './SourcePopover';

interface UnmappedSectionProps {
  unmappedValues: UnmappedValue[];
}

export function UnmappedSection({ unmappedValues }: UnmappedSectionProps) {
  if (unmappedValues.length === 0) return null;

  return (
    <div className="card">
      <h3>Unmapped but Notable</h3>
      <p className="text-sm text-muted mb-2">
        These XBRL concepts weren't mapped to required metrics but may be relevant:
      </p>
      <table>
        <thead>
          <tr>
            <th>Concept</th>
            <th>Label</th>
            <th className="text-right">Current</th>
            <th className="text-right">Prior</th>
            <th>Note</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {unmappedValues.map((uv, i) => (
            <tr key={i}>
              <td className="font-mono text-sm">{uv.xbrl_concept}</td>
              <td>{uv.xbrl_label}</td>
              <td className="text-right">{formatCurrency(uv.value_current)}</td>
              <td className="text-right">{formatCurrency(uv.value_prior)}</td>
              <td className="text-sm">{uv.llm_note}</td>
              <td>
                {uv.citation && <SourcePopover citation={uv.citation} />}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { SourceCitation, formatCurrency } from '../api/client';

interface SourcePopoverProps {
  citation: SourceCitation;
}

export function SourcePopover({ citation }: SourcePopoverProps) {
  return (
    <span className="tooltip">
      <a
        href={citation.filing_url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ fontSize: '0.8rem' }}
      >
        View Source
      </a>
      <span className="tooltip-text">
        {citation.statement && (
          <>
            <strong style={{ color: '#4ade80' }}>Found in:</strong><br />
            {citation.statement}<br /><br />
          </>
        )}
        <strong>XBRL Concept:</strong><br />
        {citation.xbrl_concept}<br /><br />
        <strong>Label:</strong><br />
        {citation.xbrl_label}<br /><br />
        <strong>Form Type:</strong> {citation.form_type}<br />
        <strong>Filing Date:</strong> {citation.filing_date}<br />
        <strong>Period End:</strong> {citation.period_end}<br />
        <strong>Raw Value:</strong> {formatCurrency(citation.raw_value)}<br />
        <strong>Accession:</strong> {citation.accession_number}
      </span>
    </span>
  );
}

import { SourceCitation, formatCurrency } from '../api/client';

interface SourcePopoverProps {
  citation: SourceCitation;
}

export function SourcePopover({ citation }: SourcePopoverProps) {
  // Check if this is a PDF citation (no filing_url)
  const isPdfSource = !citation.filing_url;

  // Extract just the page number for display (e.g., "Page 98" from "Page 98 of PDF: ...")
  const getPageDisplay = (statement: string): string => {
    if (!statement) return 'PDF';
    const match = statement.match(/Page (\d+)/);
    return match ? `Page ${match[1]}` : statement;
  };

  // TODO: Future enhancement - embed PDF viewer in review UI with page navigation
  // This would allow clicking citations to jump to the specific page in the PDF

  return (
    <span className="tooltip">
      {isPdfSource ? (
        <span style={{ fontSize: '0.8rem', color: '#666' }}>
          {getPageDisplay(citation.statement ?? '')}
        </span>
      ) : (
        <a
          href={citation.filing_url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontSize: '0.8rem' }}
        >
          View Source
        </a>
      )}
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
        {citation.filing_date && (
          <>
            <strong>Filing Date:</strong> {citation.filing_date}<br />
          </>
        )}
        <strong>Period End:</strong> {citation.period_end}<br />
        <strong>Raw Value:</strong> {formatCurrency(citation.raw_value)}<br />
        {citation.accession_number && (
          <>
            <strong>Accession:</strong> {citation.accession_number}
          </>
        )}
      </span>
    </span>
  );
}

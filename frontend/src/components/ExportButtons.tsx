interface ExportButtonsProps {
  onExportExcel: () => void;
  onExportReport: () => void;
  exportingExcel?: boolean;
  exportingWord?: boolean;
}

export function ExportButtons({
  onExportExcel,
  onExportReport,
  exportingExcel = false,
  exportingWord = false,
}: ExportButtonsProps) {
  const anyExporting = exportingExcel || exportingWord;

  return (
    <div className="card">
      <h3>Export</h3>
      <p className="text-sm text-muted mb-2">
        Download the analysis in your preferred format:
      </p>
      <div className="flex gap-2">
        <button
          className="primary"
          onClick={onExportExcel}
          disabled={anyExporting}
        >
          {exportingExcel ? 'Exporting...' : 'Download Excel (with formulas)'}
        </button>
        <button
          className="secondary"
          onClick={onExportReport}
          disabled={anyExporting}
        >
          {exportingWord ? 'Generating Report...' : 'Download Word Report'}
        </button>
      </div>
      {exportingWord && (
        <p className="text-sm text-muted mt-2">
          Generating narrative with AI... this may take a moment.
        </p>
      )}
    </div>
  );
}

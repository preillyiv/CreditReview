import {
  CalculatedMetrics,
  CalculatedRatios,
  formatCurrency,
  formatPercent,
  formatRatio,
  formatDelta,
} from '../api/client';

interface CalculatedResultsProps {
  metrics: CalculatedMetrics;
  ratios: CalculatedRatios;
  fiscalYearEnd: string;
  fiscalYearEndPrior: string;
  unit?: string;
}

interface MetricRow {
  label: string;
  current: number;
  prior: number;
  isPercentage?: boolean;
  isBold?: boolean;
}

interface RatioRow {
  label: string;
  current: number;
  prior: number;
  formatter: 'ratio' | 'currency' | 'days' | 'percentage';
  decreaseIsGood?: boolean;
  isBold?: boolean;
}

interface TableSection {
  title: string;
  rows: MetricRow[] | RatioRow[];
}

function MetricsTable({
  section,
  fiscalYear,
  priorYear,
  unit,
}: {
  section: TableSection;
  fiscalYear: string;
  priorYear: string;
  unit?: string;
}) {
  const getFiscalYear = (dateStr: string): string => dateStr.split('-')[0] || dateStr;

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h4 style={{ fontSize: '1rem', color: '#1f4e79', marginBottom: '0.75rem', fontWeight: 600 }}>
        {section.title}
      </h4>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: 'left' }}>Metric</th>
            <th style={{ textAlign: 'center' }}>FY {getFiscalYear(fiscalYear)}</th>
            <th style={{ textAlign: 'center' }}>FY {getFiscalYear(priorYear)}</th>
            <th style={{ textAlign: 'center' }}>Delta</th>
          </tr>
        </thead>
        <tbody>
          {(section.rows as MetricRow[]).map((row, idx) => (
            <tr key={idx} style={row.isBold ? { fontWeight: 'bold' } : {}}>
              <td style={{ textAlign: 'left' }}>{row.label}</td>
              <td style={{ textAlign: 'center' }}>
                {row.isPercentage ? formatPercent(row.current) : formatCurrency(row.current, unit)}
              </td>
              <td style={{ textAlign: 'center' }}>
                {row.isPercentage ? formatPercent(row.prior) : formatCurrency(row.prior, unit)}
              </td>
              <td
                style={{ textAlign: 'center' }}
                className={`${
                  row.current - row.prior >= 0 ? 'positive' : 'negative'
                }`}
              >
                {row.isPercentage
                  ? formatDelta(row.current - row.prior, true)
                  : formatDelta(row.current - row.prior)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RatiosTable({
  section,
  fiscalYear,
  priorYear,
  unit,
}: {
  section: TableSection;
  fiscalYear: string;
  priorYear: string;
  unit?: string;
}) {
  const getFiscalYear = (dateStr: string): string => dateStr.split('-')[0] || dateStr;

  const formatValue = (row: RatioRow) => {
    switch (row.formatter) {
      case 'ratio':
        return formatRatio(row.current);
      case 'currency':
        return formatCurrency(row.current, unit);
      case 'days':
        return row.current ? `${row.current.toFixed(1)} days` : '-';
      case 'percentage':
        return formatPercent(row.current);
      default:
        return String(row.current);
    }
  };

  const formatPriorValue = (row: RatioRow) => {
    switch (row.formatter) {
      case 'ratio':
        return formatRatio(row.prior);
      case 'currency':
        return formatCurrency(row.prior, unit);
      case 'days':
        return row.prior ? `${row.prior.toFixed(1)} days` : '-';
      case 'percentage':
        return formatPercent(row.prior);
      default:
        return String(row.prior);
    }
  };

  const getDeltaColor = (row: RatioRow): string => {
    const delta = row.current - row.prior;
    if (delta === 0) return 'none';

    if (row.decreaseIsGood) {
      return delta < 0 ? 'positive' : 'negative';
    }
    return delta > 0 ? 'positive' : 'negative';
  };

  const getDeltaValue = (row: RatioRow) => {
    const delta = row.current - row.prior;
    if (delta === 0) return '-';

    switch (row.formatter) {
      case 'ratio':
        return `${delta >= 0 ? '+' : ''}${delta.toFixed(2)}x`;
      case 'days':
        return `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} days`;
      case 'percentage':
        return formatDelta(delta, true);
      case 'currency':
        return formatDelta(delta);
      default:
        return String(delta);
    }
  };

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <h4 style={{ fontSize: '1rem', color: '#1f4e79', marginBottom: '0.75rem', fontWeight: 600 }}>
        {section.title}
      </h4>
      <table>
        <thead>
          <tr>
            <th style={{ textAlign: 'left' }}>Ratio</th>
            <th style={{ textAlign: 'center' }}>FY {getFiscalYear(fiscalYear)}</th>
            <th style={{ textAlign: 'center' }}>FY {getFiscalYear(priorYear)}</th>
            <th style={{ textAlign: 'center' }}>Delta</th>
          </tr>
        </thead>
        <tbody>
          {(section.rows as RatioRow[]).map((row, idx) => (
            <tr key={idx} style={row.isBold ? { fontWeight: 'bold' } : {}}>
              <td style={{ textAlign: 'left' }}>{row.label}</td>
              <td style={{ textAlign: 'center' }}>{formatValue(row)}</td>
              <td style={{ textAlign: 'center' }}>{formatPriorValue(row)}</td>
              <td style={{ textAlign: 'center' }} className={getDeltaColor(row)}>
                {getDeltaValue(row)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function CalculatedResults({
  metrics,
  ratios,
  fiscalYearEnd,
  fiscalYearEndPrior,
  unit,
}: CalculatedResultsProps) {
  const metricsSections: TableSection[] = [
    {
      title: 'Income Statement',
      rows: [
        { label: 'Top Line Revenue', current: metrics.top_line_revenue, prior: metrics.top_line_revenue_prior, isBold: true },
        { label: 'Gross Profit', current: metrics.gross_profit, prior: metrics.gross_profit_prior, isBold: true },
        { label: 'Operating Income', current: metrics.operating_income, prior: metrics.operating_income_prior, isBold: true },
        { label: 'EBITDA', current: metrics.ebitda, prior: metrics.ebitda_prior, isBold: true },
        { label: 'Adjusted EBITDA', current: metrics.adjusted_ebitda, prior: metrics.adjusted_ebitda_prior },
        { label: 'Net Income', current: metrics.net_income, prior: metrics.net_income_prior, isBold: true },
      ],
    },
    {
      title: 'Profitability Margins',
      rows: [
        { label: 'Gross Margin', current: metrics.gross_profit_margin, prior: metrics.gross_profit_margin_prior, isPercentage: true },
        { label: 'Operating Margin', current: metrics.operating_income_margin, prior: metrics.operating_income_margin_prior, isPercentage: true },
        { label: 'EBITDA Margin', current: metrics.ebitda_margin, prior: metrics.ebitda_margin_prior, isPercentage: true },
        { label: 'Net Margin', current: metrics.net_income_margin, prior: metrics.net_income_margin_prior, isPercentage: true },
      ],
    },
    {
      title: 'Balance Sheet',
      rows: [
        { label: 'Cash Balance', current: metrics.cash_balance, prior: metrics.cash_balance_prior, isBold: true },
        { label: 'Tangible Net Worth', current: metrics.tangible_net_worth, prior: metrics.tangible_net_worth_prior, isBold: true },
      ],
    },
  ];

  const ratiosSections: TableSection[] = [
    {
      title: 'Liquidity Ratios',
      rows: [
        { label: 'Current Ratio', current: ratios.current_ratio, prior: ratios.current_ratio_prior, formatter: 'ratio' as const },
        { label: 'Cash Ratio', current: ratios.cash_ratio, prior: ratios.cash_ratio_prior, formatter: 'ratio' as const },
      ],
    },
    {
      title: 'Leverage Ratios',
      rows: [
        { label: 'Debt-to-Equity', current: ratios.debt_to_equity, prior: ratios.debt_to_equity_prior, formatter: 'ratio' as const, decreaseIsGood: true },
        { label: 'Net Debt / EBITDA', current: ratios.net_debt_to_ebitda, prior: ratios.net_debt_to_ebitda_prior, formatter: 'ratio' as const, decreaseIsGood: true },
      ],
    },
    {
      title: 'Coverage Ratios',
      rows: [
        { label: 'EBITDA Interest Coverage', current: ratios.ebitda_interest_coverage, prior: ratios.ebitda_interest_coverage_prior, formatter: 'ratio' as const },
      ],
    },
    {
      title: 'Efficiency & Activity',
      rows: [
        { label: 'Days Sales Outstanding', current: ratios.days_sales_outstanding, prior: ratios.days_sales_outstanding_prior, formatter: 'days' as const, decreaseIsGood: true },
        { label: 'Working Capital', current: ratios.working_capital, prior: ratios.working_capital_prior, formatter: 'currency' as const },
      ],
    },
    {
      title: 'Profitability Ratios',
      rows: [
        { label: 'Return on Assets', current: ratios.return_on_assets, prior: ratios.return_on_assets_prior, formatter: 'percentage' as const },
        { label: 'Return on Equity', current: ratios.return_on_equity, prior: ratios.return_on_equity_prior, formatter: 'percentage' as const },
      ],
    },
  ];

  return (
    <>
      <div className="card">
        <h3>Calculated Financial Metrics</h3>
        {metricsSections.map((section, idx) => (
          <MetricsTable
            key={idx}
            section={section}
            fiscalYear={fiscalYearEnd}
            priorYear={fiscalYearEndPrior}
            unit={unit}
          />
        ))}
      </div>

      <div className="card">
        <h3>Calculated Financial Ratios</h3>
        {ratiosSections.map((section, idx) => (
          <RatiosTable
            key={idx}
            section={section}
            fiscalYear={fiscalYearEnd}
            priorYear={fiscalYearEndPrior}
            unit={unit}
          />
        ))}
      </div>
    </>
  );
}

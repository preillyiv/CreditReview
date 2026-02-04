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
}

export function CalculatedResults({
  metrics,
  ratios,
  fiscalYearEnd,
  fiscalYearEndPrior,
}: CalculatedResultsProps) {
  const getFiscalYear = (dateStr: string): string => {
    return dateStr.split('-')[0] || dateStr;
  };

  return (
    <>
      <div className="card">
        <h3>Calculated Financial Metrics</h3>
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th className="text-right">FY {getFiscalYear(fiscalYearEnd)}</th>
              <th className="text-right">FY {getFiscalYear(fiscalYearEndPrior)}</th>
              <th className="text-right">Delta</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Top Line Revenue</td>
              <td className="text-right">{formatCurrency(metrics.top_line_revenue)}</td>
              <td className="text-right">{formatCurrency(metrics.top_line_revenue_prior)}</td>
              <td className={`text-right ${metrics.top_line_revenue - metrics.top_line_revenue_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.top_line_revenue - metrics.top_line_revenue_prior)}
              </td>
            </tr>
            <tr>
              <td>Gross Profit</td>
              <td className="text-right">{formatCurrency(metrics.gross_profit)}</td>
              <td className="text-right">{formatCurrency(metrics.gross_profit_prior)}</td>
              <td className={`text-right ${metrics.gross_profit - metrics.gross_profit_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.gross_profit - metrics.gross_profit_prior)}
              </td>
            </tr>
            <tr>
              <td>Gross Margin</td>
              <td className="text-right">{formatPercent(metrics.gross_profit_margin)}</td>
              <td className="text-right">{formatPercent(metrics.gross_profit_margin_prior)}</td>
              <td className={`text-right ${metrics.gross_profit_margin - metrics.gross_profit_margin_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.gross_profit_margin - metrics.gross_profit_margin_prior, true)}
              </td>
            </tr>
            <tr>
              <td>Operating Income</td>
              <td className="text-right">{formatCurrency(metrics.operating_income)}</td>
              <td className="text-right">{formatCurrency(metrics.operating_income_prior)}</td>
              <td className={`text-right ${metrics.operating_income - metrics.operating_income_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.operating_income - metrics.operating_income_prior)}
              </td>
            </tr>
            <tr>
              <td>Operating Margin</td>
              <td className="text-right">{formatPercent(metrics.operating_income_margin)}</td>
              <td className="text-right">{formatPercent(metrics.operating_income_margin_prior)}</td>
              <td className={`text-right ${metrics.operating_income_margin - metrics.operating_income_margin_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.operating_income_margin - metrics.operating_income_margin_prior, true)}
              </td>
            </tr>
            <tr>
              <td>EBITDA</td>
              <td className="text-right">{formatCurrency(metrics.ebitda)}</td>
              <td className="text-right">{formatCurrency(metrics.ebitda_prior)}</td>
              <td className={`text-right ${metrics.ebitda - metrics.ebitda_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.ebitda - metrics.ebitda_prior)}
              </td>
            </tr>
            <tr>
              <td>EBITDA Margin</td>
              <td className="text-right">{formatPercent(metrics.ebitda_margin)}</td>
              <td className="text-right">{formatPercent(metrics.ebitda_margin_prior)}</td>
              <td className={`text-right ${metrics.ebitda_margin - metrics.ebitda_margin_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.ebitda_margin - metrics.ebitda_margin_prior, true)}
              </td>
            </tr>
            <tr>
              <td>Adjusted EBITDA</td>
              <td className="text-right">{formatCurrency(metrics.adjusted_ebitda)}</td>
              <td className="text-right">{formatCurrency(metrics.adjusted_ebitda_prior)}</td>
              <td className={`text-right ${metrics.adjusted_ebitda - metrics.adjusted_ebitda_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.adjusted_ebitda - metrics.adjusted_ebitda_prior)}
              </td>
            </tr>
            <tr>
              <td>Net Income</td>
              <td className="text-right">{formatCurrency(metrics.net_income)}</td>
              <td className="text-right">{formatCurrency(metrics.net_income_prior)}</td>
              <td className={`text-right ${metrics.net_income - metrics.net_income_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.net_income - metrics.net_income_prior)}
              </td>
            </tr>
            <tr>
              <td>Net Margin</td>
              <td className="text-right">{formatPercent(metrics.net_income_margin)}</td>
              <td className="text-right">{formatPercent(metrics.net_income_margin_prior)}</td>
              <td className={`text-right ${metrics.net_income_margin - metrics.net_income_margin_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.net_income_margin - metrics.net_income_margin_prior, true)}
              </td>
            </tr>
            <tr>
              <td>Cash Balance</td>
              <td className="text-right">{formatCurrency(metrics.cash_balance)}</td>
              <td className="text-right">{formatCurrency(metrics.cash_balance_prior)}</td>
              <td className={`text-right ${metrics.cash_balance - metrics.cash_balance_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.cash_balance - metrics.cash_balance_prior)}
              </td>
            </tr>
            <tr>
              <td>Tangible Net Worth</td>
              <td className="text-right">{formatCurrency(metrics.tangible_net_worth)}</td>
              <td className="text-right">{formatCurrency(metrics.tangible_net_worth_prior)}</td>
              <td className={`text-right ${metrics.tangible_net_worth - metrics.tangible_net_worth_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(metrics.tangible_net_worth - metrics.tangible_net_worth_prior)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Calculated Financial Ratios</h3>
        <table>
          <thead>
            <tr>
              <th>Ratio</th>
              <th className="text-right">FY {getFiscalYear(fiscalYearEnd)}</th>
              <th className="text-right">FY {getFiscalYear(fiscalYearEndPrior)}</th>
              <th className="text-right">Delta</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Current Ratio</td>
              <td className="text-right">{formatRatio(ratios.current_ratio)}</td>
              <td className="text-right">{formatRatio(ratios.current_ratio_prior)}</td>
              <td className={`text-right ${ratios.current_ratio - ratios.current_ratio_prior >= 0 ? 'positive' : 'negative'}`}>
                {(ratios.current_ratio - ratios.current_ratio_prior).toFixed(2)}x
              </td>
            </tr>
            <tr>
              <td>Cash Ratio</td>
              <td className="text-right">{formatRatio(ratios.cash_ratio)}</td>
              <td className="text-right">{formatRatio(ratios.cash_ratio_prior)}</td>
              <td className={`text-right ${ratios.cash_ratio - ratios.cash_ratio_prior >= 0 ? 'positive' : 'negative'}`}>
                {(ratios.cash_ratio - ratios.cash_ratio_prior).toFixed(2)}x
              </td>
            </tr>
            <tr>
              <td>Debt-to-Equity</td>
              <td className="text-right">{formatRatio(ratios.debt_to_equity)}</td>
              <td className="text-right">{formatRatio(ratios.debt_to_equity_prior)}</td>
              <td className={`text-right ${ratios.debt_to_equity - ratios.debt_to_equity_prior <= 0 ? 'positive' : 'negative'}`}>
                {(ratios.debt_to_equity - ratios.debt_to_equity_prior).toFixed(2)}x
              </td>
            </tr>
            <tr>
              <td>EBITDA Interest Coverage</td>
              <td className="text-right">{formatRatio(ratios.ebitda_interest_coverage)}</td>
              <td className="text-right">{formatRatio(ratios.ebitda_interest_coverage_prior)}</td>
              <td className={`text-right ${ratios.ebitda_interest_coverage - ratios.ebitda_interest_coverage_prior >= 0 ? 'positive' : 'negative'}`}>
                {(ratios.ebitda_interest_coverage - ratios.ebitda_interest_coverage_prior).toFixed(2)}x
              </td>
            </tr>
            <tr>
              <td>Net Debt / EBITDA</td>
              <td className="text-right">{formatRatio(ratios.net_debt_to_ebitda)}</td>
              <td className="text-right">{formatRatio(ratios.net_debt_to_ebitda_prior)}</td>
              <td className={`text-right ${ratios.net_debt_to_ebitda - ratios.net_debt_to_ebitda_prior <= 0 ? 'positive' : 'negative'}`}>
                {(ratios.net_debt_to_ebitda - ratios.net_debt_to_ebitda_prior).toFixed(2)}x
              </td>
            </tr>
            <tr>
              <td>Days Sales Outstanding</td>
              <td className="text-right">{ratios.days_sales_outstanding.toFixed(1)} days</td>
              <td className="text-right">{ratios.days_sales_outstanding_prior.toFixed(1)} days</td>
              <td className={`text-right ${ratios.days_sales_outstanding - ratios.days_sales_outstanding_prior <= 0 ? 'positive' : 'negative'}`}>
                {(ratios.days_sales_outstanding - ratios.days_sales_outstanding_prior).toFixed(1)} days
              </td>
            </tr>
            <tr>
              <td>Working Capital</td>
              <td className="text-right">{formatCurrency(ratios.working_capital)}</td>
              <td className="text-right">{formatCurrency(ratios.working_capital_prior)}</td>
              <td className={`text-right ${ratios.working_capital - ratios.working_capital_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(ratios.working_capital - ratios.working_capital_prior)}
              </td>
            </tr>
            <tr>
              <td>Return on Assets</td>
              <td className="text-right">{formatPercent(ratios.return_on_assets)}</td>
              <td className="text-right">{formatPercent(ratios.return_on_assets_prior)}</td>
              <td className={`text-right ${ratios.return_on_assets - ratios.return_on_assets_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(ratios.return_on_assets - ratios.return_on_assets_prior, true)}
              </td>
            </tr>
            <tr>
              <td>Return on Equity</td>
              <td className="text-right">{formatPercent(ratios.return_on_equity)}</td>
              <td className="text-right">{formatPercent(ratios.return_on_equity_prior)}</td>
              <td className={`text-right ${ratios.return_on_equity - ratios.return_on_equity_prior >= 0 ? 'positive' : 'negative'}`}>
                {formatDelta(ratios.return_on_equity - ratios.return_on_equity_prior, true)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}

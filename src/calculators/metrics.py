"""
Financial metrics calculations.

This module contains deterministic calculations for financial metrics.
All calculations are performed in Python - no LLM involvement.

Formulas:
- gross_profit = revenue - cost_of_revenue (or use directly if reported)
- gross_margin = gross_profit / revenue
- operating_margin = operating_income / revenue
- ebitda = operating_income + depreciation_amortization
- ebitda_margin = ebitda / revenue
- adjusted_ebitda = ebitda + stock_compensation
- adjusted_ebitda_margin = adjusted_ebitda / revenue
- net_margin = net_income / revenue
- tangible_net_worth = stockholders_equity - intangible_assets - goodwill
"""

from dataclasses import dataclass
from src.models.extraction import ExtractionSession, CalculationStep


@dataclass
class FinancialMetrics:
    """Calculated financial metrics for a company."""
    # Net Worth
    tangible_net_worth: float = 0.0
    tangible_net_worth_prior: float = 0.0

    # Cash
    cash_balance: float = 0.0
    cash_balance_prior: float = 0.0

    # Revenue
    top_line_revenue: float = 0.0
    top_line_revenue_prior: float = 0.0

    # Profitability
    gross_profit: float = 0.0
    gross_profit_prior: float = 0.0
    gross_profit_margin: float = 0.0
    gross_profit_margin_prior: float = 0.0

    operating_income: float = 0.0
    operating_income_prior: float = 0.0
    operating_income_margin: float = 0.0
    operating_income_margin_prior: float = 0.0

    ebitda: float = 0.0
    ebitda_prior: float = 0.0
    ebitda_margin: float = 0.0
    ebitda_margin_prior: float = 0.0

    adjusted_ebitda: float = 0.0
    adjusted_ebitda_prior: float = 0.0
    adjusted_ebitda_margin: float = 0.0
    adjusted_ebitda_margin_prior: float = 0.0

    net_income: float = 0.0
    net_income_prior: float = 0.0
    net_income_margin: float = 0.0
    net_income_margin_prior: float = 0.0

    def calculate_deltas(self) -> dict:
        """Calculate YoY deltas for all metrics."""
        return {
            "tangible_net_worth_delta": self.tangible_net_worth - self.tangible_net_worth_prior,
            "cash_balance_delta": self.cash_balance - self.cash_balance_prior,
            "top_line_revenue_delta": self.top_line_revenue - self.top_line_revenue_prior,
            "gross_profit_delta": self.gross_profit - self.gross_profit_prior,
            "gross_profit_margin_delta": self.gross_profit_margin - self.gross_profit_margin_prior,
            "operating_income_delta": self.operating_income - self.operating_income_prior,
            "operating_income_margin_delta": self.operating_income_margin - self.operating_income_margin_prior,
            "ebitda_delta": self.ebitda - self.ebitda_prior,
            "ebitda_margin_delta": self.ebitda_margin - self.ebitda_margin_prior,
            "adjusted_ebitda_delta": self.adjusted_ebitda - self.adjusted_ebitda_prior,
            "adjusted_ebitda_margin_delta": self.adjusted_ebitda_margin - self.adjusted_ebitda_margin_prior,
            "net_income_delta": self.net_income - self.net_income_prior,
            "net_income_margin_delta": self.net_income_margin - self.net_income_margin_prior,
        }


def _safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def _get_value(session: ExtractionSession, metric_key: str, prior: bool = False) -> float:
    """Get a raw value from the session, returning 0.0 if not found."""
    val = session.get_raw_value(metric_key, prior=prior)
    return val if val is not None else 0.0


def calculate_metrics_from_raw(session: ExtractionSession) -> tuple[FinancialMetrics, list[CalculationStep]]:
    """
    Calculate financial metrics from raw extracted values.

    This function performs all metric calculations using deterministic Python formulas.
    It returns both the calculated metrics and an audit trail of calculation steps.

    Args:
        session: ExtractionSession with raw_values populated

    Returns:
        Tuple of (FinancialMetrics, list of CalculationStep for audit trail)
    """
    steps = []

    # Get base values for current year
    revenue = _get_value(session, "revenue")
    cost_of_revenue = _get_value(session, "cost_of_revenue")
    gross_profit_raw = _get_value(session, "gross_profit")
    operating_income = _get_value(session, "operating_income")
    depreciation_amortization = _get_value(session, "depreciation_amortization")
    net_income = _get_value(session, "net_income")
    stockholders_equity = _get_value(session, "stockholders_equity")
    intangible_assets = _get_value(session, "intangible_assets")
    goodwill = _get_value(session, "goodwill")
    cash = _get_value(session, "cash")
    stock_compensation = _get_value(session, "stock_compensation")

    # Get base values for prior year
    revenue_prior = _get_value(session, "revenue", prior=True)
    cost_of_revenue_prior = _get_value(session, "cost_of_revenue", prior=True)
    gross_profit_raw_prior = _get_value(session, "gross_profit", prior=True)
    operating_income_prior = _get_value(session, "operating_income", prior=True)
    depreciation_amortization_prior = _get_value(session, "depreciation_amortization", prior=True)
    net_income_prior = _get_value(session, "net_income", prior=True)
    stockholders_equity_prior = _get_value(session, "stockholders_equity", prior=True)
    intangible_assets_prior = _get_value(session, "intangible_assets", prior=True)
    goodwill_prior = _get_value(session, "goodwill", prior=True)
    cash_prior = _get_value(session, "cash", prior=True)
    stock_compensation_prior = _get_value(session, "stock_compensation", prior=True)

    # ========== GROSS PROFIT ==========
    # Use reported gross profit if available, otherwise calculate
    if gross_profit_raw != 0:
        gross_profit = gross_profit_raw
        steps.append(CalculationStep(
            metric="gross_profit",
            formula="Gross Profit (reported directly)",
            formula_excel="=RawValues!B_gross_profit",
            inputs={"gross_profit_raw": gross_profit_raw},
            result=gross_profit,
        ))
    else:
        gross_profit = revenue - cost_of_revenue
        steps.append(CalculationStep(
            metric="gross_profit",
            formula="Gross Profit = Revenue - Cost of Revenue",
            formula_excel="=B_revenue-B_cost_of_revenue",
            inputs={"revenue": revenue, "cost_of_revenue": cost_of_revenue},
            result=gross_profit,
        ))

    if gross_profit_raw_prior != 0:
        gross_profit_prior = gross_profit_raw_prior
    else:
        gross_profit_prior = revenue_prior - cost_of_revenue_prior

    # ========== GROSS MARGIN ==========
    gross_margin = _safe_divide(gross_profit, revenue)
    steps.append(CalculationStep(
        metric="gross_profit_margin",
        formula="Gross Margin = Gross Profit / Revenue",
        formula_excel="=B_gross_profit/B_revenue",
        inputs={"gross_profit": gross_profit, "revenue": revenue},
        result=gross_margin,
    ))
    gross_margin_prior = _safe_divide(gross_profit_prior, revenue_prior)

    # ========== OPERATING MARGIN ==========
    operating_margin = _safe_divide(operating_income, revenue)
    steps.append(CalculationStep(
        metric="operating_income_margin",
        formula="Operating Margin = Operating Income / Revenue",
        formula_excel="=B_operating_income/B_revenue",
        inputs={"operating_income": operating_income, "revenue": revenue},
        result=operating_margin,
    ))
    operating_margin_prior = _safe_divide(operating_income_prior, revenue_prior)

    # ========== EBITDA ==========
    ebitda = operating_income + depreciation_amortization
    steps.append(CalculationStep(
        metric="ebitda",
        formula="EBITDA = Operating Income + Depreciation & Amortization",
        formula_excel="=B_operating_income+B_depreciation_amortization",
        inputs={
            "operating_income": operating_income,
            "depreciation_amortization": depreciation_amortization,
        },
        result=ebitda,
    ))
    ebitda_prior = operating_income_prior + depreciation_amortization_prior

    # ========== EBITDA MARGIN ==========
    ebitda_margin = _safe_divide(ebitda, revenue)
    steps.append(CalculationStep(
        metric="ebitda_margin",
        formula="EBITDA Margin = EBITDA / Revenue",
        formula_excel="=B_ebitda/B_revenue",
        inputs={"ebitda": ebitda, "revenue": revenue},
        result=ebitda_margin,
    ))
    ebitda_margin_prior = _safe_divide(ebitda_prior, revenue_prior)

    # ========== ADJUSTED EBITDA ==========
    # Only calculate if we have stock compensation data
    if stock_compensation != 0:
        adjusted_ebitda = ebitda + stock_compensation
        steps.append(CalculationStep(
            metric="adjusted_ebitda",
            formula="Adjusted EBITDA = EBITDA + Stock-Based Compensation",
            formula_excel="=B_ebitda+B_stock_compensation",
            inputs={"ebitda": ebitda, "stock_compensation": stock_compensation},
            result=adjusted_ebitda,
        ))
    else:
        adjusted_ebitda = ebitda  # Fall back to EBITDA if no SBC data
        steps.append(CalculationStep(
            metric="adjusted_ebitda",
            formula="Adjusted EBITDA = EBITDA (no SBC data available)",
            formula_excel="=B_ebitda",
            inputs={"ebitda": ebitda},
            result=adjusted_ebitda,
        ))

    if stock_compensation_prior != 0:
        adjusted_ebitda_prior = ebitda_prior + stock_compensation_prior
    else:
        adjusted_ebitda_prior = ebitda_prior

    # ========== ADJUSTED EBITDA MARGIN ==========
    adjusted_ebitda_margin = _safe_divide(adjusted_ebitda, revenue)
    steps.append(CalculationStep(
        metric="adjusted_ebitda_margin",
        formula="Adjusted EBITDA Margin = Adjusted EBITDA / Revenue",
        formula_excel="=B_adjusted_ebitda/B_revenue",
        inputs={"adjusted_ebitda": adjusted_ebitda, "revenue": revenue},
        result=adjusted_ebitda_margin,
    ))
    adjusted_ebitda_margin_prior = _safe_divide(adjusted_ebitda_prior, revenue_prior)

    # ========== NET MARGIN ==========
    net_margin = _safe_divide(net_income, revenue)
    steps.append(CalculationStep(
        metric="net_income_margin",
        formula="Net Margin = Net Income / Revenue",
        formula_excel="=B_net_income/B_revenue",
        inputs={"net_income": net_income, "revenue": revenue},
        result=net_margin,
    ))
    net_margin_prior = _safe_divide(net_income_prior, revenue_prior)

    # ========== TANGIBLE NET WORTH ==========
    tangible_net_worth = stockholders_equity - intangible_assets - goodwill
    steps.append(CalculationStep(
        metric="tangible_net_worth",
        formula="Tangible Net Worth = Stockholders' Equity - Intangible Assets - Goodwill",
        formula_excel="=B_stockholders_equity-B_intangible_assets-B_goodwill",
        inputs={
            "stockholders_equity": stockholders_equity,
            "intangible_assets": intangible_assets,
            "goodwill": goodwill,
        },
        result=tangible_net_worth,
    ))
    tangible_net_worth_prior = stockholders_equity_prior - intangible_assets_prior - goodwill_prior

    # Build the metrics object
    metrics = FinancialMetrics(
        tangible_net_worth=tangible_net_worth,
        tangible_net_worth_prior=tangible_net_worth_prior,
        cash_balance=cash,
        cash_balance_prior=cash_prior,
        top_line_revenue=revenue,
        top_line_revenue_prior=revenue_prior,
        gross_profit=gross_profit,
        gross_profit_prior=gross_profit_prior,
        gross_profit_margin=gross_margin,
        gross_profit_margin_prior=gross_margin_prior,
        operating_income=operating_income,
        operating_income_prior=operating_income_prior,
        operating_income_margin=operating_margin,
        operating_income_margin_prior=operating_margin_prior,
        ebitda=ebitda,
        ebitda_prior=ebitda_prior,
        ebitda_margin=ebitda_margin,
        ebitda_margin_prior=ebitda_margin_prior,
        adjusted_ebitda=adjusted_ebitda,
        adjusted_ebitda_prior=adjusted_ebitda_prior,
        adjusted_ebitda_margin=adjusted_ebitda_margin,
        adjusted_ebitda_margin_prior=adjusted_ebitda_margin_prior,
        net_income=net_income,
        net_income_prior=net_income_prior,
        net_income_margin=net_margin,
        net_income_margin_prior=net_margin_prior,
    )

    return metrics, steps


def print_metrics_summary(metrics: FinancialMetrics) -> None:
    """Print a formatted summary of calculated metrics."""
    print("\n" + "=" * 70)
    print("CALCULATED FINANCIAL METRICS")
    print("=" * 70 + "\n")

    print(f"{'Metric':<30} {'Current':>15} {'Prior':>15} {'Delta':>15}")
    print("-" * 75)

    deltas = metrics.calculate_deltas()

    # Helper for formatting
    def fmt_currency(val: float) -> str:
        if abs(val) >= 1e9:
            return f"${val/1e9:,.1f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:,.1f}M"
        else:
            return f"${val:,.0f}"

    def fmt_pct(val: float) -> str:
        return f"{val:.1%}"

    def fmt_delta(val: float, is_pct: bool = False) -> str:
        if is_pct:
            return f"{val:+.1%}"
        if abs(val) >= 1e9:
            return f"{'+' if val >= 0 else ''}{val/1e9:,.1f}B"
        elif abs(val) >= 1e6:
            return f"{'+' if val >= 0 else ''}{val/1e6:,.1f}M"
        else:
            return f"{'+' if val >= 0 else ''}{val:,.0f}"

    # Currency metrics
    print(f"{'Top Line Revenue':<30} {fmt_currency(metrics.top_line_revenue):>15} "
          f"{fmt_currency(metrics.top_line_revenue_prior):>15} "
          f"{fmt_delta(deltas['top_line_revenue_delta']):>15}")

    print(f"{'Gross Profit':<30} {fmt_currency(metrics.gross_profit):>15} "
          f"{fmt_currency(metrics.gross_profit_prior):>15} "
          f"{fmt_delta(deltas['gross_profit_delta']):>15}")

    print(f"{'Gross Margin':<30} {fmt_pct(metrics.gross_profit_margin):>15} "
          f"{fmt_pct(metrics.gross_profit_margin_prior):>15} "
          f"{fmt_delta(deltas['gross_profit_margin_delta'], is_pct=True):>15}")

    print(f"{'Operating Income':<30} {fmt_currency(metrics.operating_income):>15} "
          f"{fmt_currency(metrics.operating_income_prior):>15} "
          f"{fmt_delta(deltas['operating_income_delta']):>15}")

    print(f"{'Operating Margin':<30} {fmt_pct(metrics.operating_income_margin):>15} "
          f"{fmt_pct(metrics.operating_income_margin_prior):>15} "
          f"{fmt_delta(deltas['operating_income_margin_delta'], is_pct=True):>15}")

    print(f"{'EBITDA':<30} {fmt_currency(metrics.ebitda):>15} "
          f"{fmt_currency(metrics.ebitda_prior):>15} "
          f"{fmt_delta(deltas['ebitda_delta']):>15}")

    print(f"{'EBITDA Margin':<30} {fmt_pct(metrics.ebitda_margin):>15} "
          f"{fmt_pct(metrics.ebitda_margin_prior):>15} "
          f"{fmt_delta(deltas['ebitda_margin_delta'], is_pct=True):>15}")

    print(f"{'Adjusted EBITDA':<30} {fmt_currency(metrics.adjusted_ebitda):>15} "
          f"{fmt_currency(metrics.adjusted_ebitda_prior):>15} "
          f"{fmt_delta(deltas['adjusted_ebitda_delta']):>15}")

    print(f"{'Net Income':<30} {fmt_currency(metrics.net_income):>15} "
          f"{fmt_currency(metrics.net_income_prior):>15} "
          f"{fmt_delta(deltas['net_income_delta']):>15}")

    print(f"{'Net Margin':<30} {fmt_pct(metrics.net_income_margin):>15} "
          f"{fmt_pct(metrics.net_income_margin_prior):>15} "
          f"{fmt_delta(deltas['net_income_margin_delta'], is_pct=True):>15}")

    print(f"{'Cash Balance':<30} {fmt_currency(metrics.cash_balance):>15} "
          f"{fmt_currency(metrics.cash_balance_prior):>15} "
          f"{fmt_delta(deltas['cash_balance_delta']):>15}")

    print(f"{'Tangible Net Worth':<30} {fmt_currency(metrics.tangible_net_worth):>15} "
          f"{fmt_currency(metrics.tangible_net_worth_prior):>15} "
          f"{fmt_delta(deltas['tangible_net_worth_delta']):>15}")

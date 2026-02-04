"""
Financial ratios calculations.

This module contains deterministic calculations for financial ratios.
All calculations are performed in Python - no LLM involvement.

Formulas:
- current_ratio = current_assets / current_liabilities
- cash_ratio = cash / current_liabilities
- debt_to_equity = total_debt / stockholders_equity
- ebitda_interest_coverage = ebitda / interest_expense
- net_debt = total_debt - cash
- net_debt_to_ebitda = net_debt / ebitda
- net_debt_to_adj_ebitda = net_debt / adjusted_ebitda
- days_sales_outstanding = (accounts_receivable / revenue) * 365
- working_capital = current_assets - current_liabilities
- return_on_assets = net_income / total_assets
- return_on_equity = net_income / stockholders_equity
"""

from dataclasses import dataclass
from src.models.extraction import ExtractionSession, CalculationStep


@dataclass
class FinancialRatios:
    """Calculated financial ratios for a company."""
    # Liquidity
    current_ratio: float = 0.0
    current_ratio_prior: float = 0.0

    cash_ratio: float = 0.0
    cash_ratio_prior: float = 0.0

    # Leverage
    debt_to_equity: float = 0.0
    debt_to_equity_prior: float = 0.0

    # Coverage
    ebitda_interest_coverage: float = 0.0
    ebitda_interest_coverage_prior: float = 0.0

    net_debt_to_ebitda: float = 0.0
    net_debt_to_ebitda_prior: float = 0.0

    net_debt_to_adj_ebitda: float = 0.0
    net_debt_to_adj_ebitda_prior: float = 0.0

    # Efficiency
    days_sales_outstanding: float = 0.0
    days_sales_outstanding_prior: float = 0.0

    # Working Capital
    working_capital: float = 0.0
    working_capital_prior: float = 0.0

    # Returns
    return_on_assets: float = 0.0
    return_on_assets_prior: float = 0.0

    return_on_equity: float = 0.0
    return_on_equity_prior: float = 0.0

    def calculate_deltas(self) -> dict:
        """Calculate YoY deltas for all ratios."""
        return {
            "current_ratio_delta": self.current_ratio - self.current_ratio_prior,
            "cash_ratio_delta": self.cash_ratio - self.cash_ratio_prior,
            "debt_to_equity_delta": self.debt_to_equity - self.debt_to_equity_prior,
            "ebitda_interest_coverage_delta": self.ebitda_interest_coverage - self.ebitda_interest_coverage_prior,
            "net_debt_to_ebitda_delta": self.net_debt_to_ebitda - self.net_debt_to_ebitda_prior,
            "net_debt_to_adj_ebitda_delta": self.net_debt_to_adj_ebitda - self.net_debt_to_adj_ebitda_prior,
            "days_sales_outstanding_delta": self.days_sales_outstanding - self.days_sales_outstanding_prior,
            "working_capital_delta": self.working_capital - self.working_capital_prior,
            "return_on_assets_delta": self.return_on_assets - self.return_on_assets_prior,
            "return_on_equity_delta": self.return_on_equity - self.return_on_equity_prior,
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


def calculate_ratios_from_raw(
    session: ExtractionSession,
    ebitda: float,
    ebitda_prior: float,
    adjusted_ebitda: float,
    adjusted_ebitda_prior: float,
) -> tuple[FinancialRatios, list[CalculationStep]]:
    """
    Calculate financial ratios from raw extracted values.

    This function performs all ratio calculations using deterministic Python formulas.
    It returns both the calculated ratios and an audit trail of calculation steps.

    Args:
        session: ExtractionSession with raw_values populated
        ebitda: Calculated EBITDA from metrics (current year)
        ebitda_prior: Calculated EBITDA (prior year)
        adjusted_ebitda: Calculated Adjusted EBITDA (current year)
        adjusted_ebitda_prior: Calculated Adjusted EBITDA (prior year)

    Returns:
        Tuple of (FinancialRatios, list of CalculationStep for audit trail)
    """
    steps = []

    # Get base values for current year
    current_assets = _get_value(session, "current_assets")
    current_liabilities = _get_value(session, "current_liabilities")
    cash = _get_value(session, "cash")
    total_debt = _get_value(session, "total_debt")
    stockholders_equity = _get_value(session, "stockholders_equity")
    interest_expense = _get_value(session, "interest_expense")
    accounts_receivable = _get_value(session, "accounts_receivable")
    revenue = _get_value(session, "revenue")
    net_income = _get_value(session, "net_income")
    total_assets = _get_value(session, "total_assets")

    # Get base values for prior year
    current_assets_prior = _get_value(session, "current_assets", prior=True)
    current_liabilities_prior = _get_value(session, "current_liabilities", prior=True)
    cash_prior = _get_value(session, "cash", prior=True)
    total_debt_prior = _get_value(session, "total_debt", prior=True)
    stockholders_equity_prior = _get_value(session, "stockholders_equity", prior=True)
    interest_expense_prior = _get_value(session, "interest_expense", prior=True)
    accounts_receivable_prior = _get_value(session, "accounts_receivable", prior=True)
    revenue_prior = _get_value(session, "revenue", prior=True)
    net_income_prior = _get_value(session, "net_income", prior=True)
    total_assets_prior = _get_value(session, "total_assets", prior=True)

    # ========== CURRENT RATIO ==========
    current_ratio = _safe_divide(current_assets, current_liabilities)
    steps.append(CalculationStep(
        metric="current_ratio",
        formula="Current Ratio = Current Assets / Current Liabilities",
        formula_excel="=B_current_assets/B_current_liabilities",
        inputs={"current_assets": current_assets, "current_liabilities": current_liabilities},
        result=current_ratio,
    ))
    current_ratio_prior = _safe_divide(current_assets_prior, current_liabilities_prior)

    # ========== CASH RATIO ==========
    cash_ratio = _safe_divide(cash, current_liabilities)
    steps.append(CalculationStep(
        metric="cash_ratio",
        formula="Cash Ratio = Cash / Current Liabilities",
        formula_excel="=B_cash/B_current_liabilities",
        inputs={"cash": cash, "current_liabilities": current_liabilities},
        result=cash_ratio,
    ))
    cash_ratio_prior = _safe_divide(cash_prior, current_liabilities_prior)

    # ========== DEBT-TO-EQUITY ==========
    debt_to_equity = _safe_divide(total_debt, stockholders_equity)
    steps.append(CalculationStep(
        metric="debt_to_equity",
        formula="Debt-to-Equity = Total Debt / Stockholders' Equity",
        formula_excel="=B_total_debt/B_stockholders_equity",
        inputs={"total_debt": total_debt, "stockholders_equity": stockholders_equity},
        result=debt_to_equity,
    ))
    debt_to_equity_prior = _safe_divide(total_debt_prior, stockholders_equity_prior)

    # ========== EBITDA INTEREST COVERAGE ==========
    ebitda_interest_coverage = _safe_divide(ebitda, interest_expense)
    steps.append(CalculationStep(
        metric="ebitda_interest_coverage",
        formula="EBITDA Interest Coverage = EBITDA / Interest Expense",
        formula_excel="=B_ebitda/B_interest_expense",
        inputs={"ebitda": ebitda, "interest_expense": interest_expense},
        result=ebitda_interest_coverage,
    ))
    ebitda_interest_coverage_prior = _safe_divide(ebitda_prior, interest_expense_prior)

    # ========== NET DEBT ==========
    net_debt = total_debt - cash
    steps.append(CalculationStep(
        metric="net_debt",
        formula="Net Debt = Total Debt - Cash",
        formula_excel="=B_total_debt-B_cash",
        inputs={"total_debt": total_debt, "cash": cash},
        result=net_debt,
    ))
    net_debt_prior = total_debt_prior - cash_prior

    # ========== NET DEBT / EBITDA ==========
    net_debt_to_ebitda = _safe_divide(net_debt, ebitda)
    steps.append(CalculationStep(
        metric="net_debt_to_ebitda",
        formula="Net Debt / EBITDA = Net Debt / EBITDA",
        formula_excel="=B_net_debt/B_ebitda",
        inputs={"net_debt": net_debt, "ebitda": ebitda},
        result=net_debt_to_ebitda,
    ))
    net_debt_to_ebitda_prior = _safe_divide(net_debt_prior, ebitda_prior)

    # ========== NET DEBT / ADJUSTED EBITDA ==========
    net_debt_to_adj_ebitda = _safe_divide(net_debt, adjusted_ebitda)
    steps.append(CalculationStep(
        metric="net_debt_to_adj_ebitda",
        formula="Net Debt / Adj. EBITDA = Net Debt / Adjusted EBITDA",
        formula_excel="=B_net_debt/B_adjusted_ebitda",
        inputs={"net_debt": net_debt, "adjusted_ebitda": adjusted_ebitda},
        result=net_debt_to_adj_ebitda,
    ))
    net_debt_to_adj_ebitda_prior = _safe_divide(net_debt_prior, adjusted_ebitda_prior)

    # ========== DAYS SALES OUTSTANDING ==========
    days_sales_outstanding = _safe_divide(accounts_receivable, revenue) * 365
    steps.append(CalculationStep(
        metric="days_sales_outstanding",
        formula="Days Sales Outstanding = (Accounts Receivable / Revenue) × 365",
        formula_excel="=(B_accounts_receivable/B_revenue)*365",
        inputs={"accounts_receivable": accounts_receivable, "revenue": revenue},
        result=days_sales_outstanding,
    ))
    days_sales_outstanding_prior = _safe_divide(accounts_receivable_prior, revenue_prior) * 365

    # ========== WORKING CAPITAL ==========
    working_capital = current_assets - current_liabilities
    steps.append(CalculationStep(
        metric="working_capital",
        formula="Working Capital = Current Assets - Current Liabilities",
        formula_excel="=B_current_assets-B_current_liabilities",
        inputs={"current_assets": current_assets, "current_liabilities": current_liabilities},
        result=working_capital,
    ))
    working_capital_prior = current_assets_prior - current_liabilities_prior

    # ========== RETURN ON ASSETS ==========
    return_on_assets = _safe_divide(net_income, total_assets)
    steps.append(CalculationStep(
        metric="return_on_assets",
        formula="Return on Assets = Net Income / Total Assets",
        formula_excel="=B_net_income/B_total_assets",
        inputs={"net_income": net_income, "total_assets": total_assets},
        result=return_on_assets,
    ))
    return_on_assets_prior = _safe_divide(net_income_prior, total_assets_prior)

    # ========== RETURN ON EQUITY ==========
    return_on_equity = _safe_divide(net_income, stockholders_equity)
    steps.append(CalculationStep(
        metric="return_on_equity",
        formula="Return on Equity = Net Income / Stockholders' Equity",
        formula_excel="=B_net_income/B_stockholders_equity",
        inputs={"net_income": net_income, "stockholders_equity": stockholders_equity},
        result=return_on_equity,
    ))
    return_on_equity_prior = _safe_divide(net_income_prior, stockholders_equity_prior)

    # Build the ratios object
    ratios = FinancialRatios(
        current_ratio=current_ratio,
        current_ratio_prior=current_ratio_prior,
        cash_ratio=cash_ratio,
        cash_ratio_prior=cash_ratio_prior,
        debt_to_equity=debt_to_equity,
        debt_to_equity_prior=debt_to_equity_prior,
        ebitda_interest_coverage=ebitda_interest_coverage,
        ebitda_interest_coverage_prior=ebitda_interest_coverage_prior,
        net_debt_to_ebitda=net_debt_to_ebitda,
        net_debt_to_ebitda_prior=net_debt_to_ebitda_prior,
        net_debt_to_adj_ebitda=net_debt_to_adj_ebitda,
        net_debt_to_adj_ebitda_prior=net_debt_to_adj_ebitda_prior,
        days_sales_outstanding=days_sales_outstanding,
        days_sales_outstanding_prior=days_sales_outstanding_prior,
        working_capital=working_capital,
        working_capital_prior=working_capital_prior,
        return_on_assets=return_on_assets,
        return_on_assets_prior=return_on_assets_prior,
        return_on_equity=return_on_equity,
        return_on_equity_prior=return_on_equity_prior,
    )

    return ratios, steps


def print_ratios_summary(ratios: FinancialRatios) -> None:
    """Print a formatted summary of calculated ratios."""
    print("\n" + "=" * 70)
    print("CALCULATED FINANCIAL RATIOS")
    print("=" * 70 + "\n")

    print(f"{'Ratio':<30} {'Current':>15} {'Prior':>15} {'Delta':>15}")
    print("-" * 75)

    deltas = ratios.calculate_deltas()

    # Helper for formatting
    def fmt_ratio(val: float) -> str:
        return f"{val:.2f}x"

    def fmt_pct(val: float) -> str:
        return f"{val:.1%}"

    def fmt_currency(val: float) -> str:
        if abs(val) >= 1e9:
            return f"${val/1e9:,.1f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:,.1f}M"
        else:
            return f"${val:,.0f}"

    def fmt_days(val: float) -> str:
        return f"{val:.1f} days"

    def fmt_delta_ratio(val: float) -> str:
        return f"{val:+.2f}x"

    def fmt_delta_pct(val: float) -> str:
        return f"{val:+.1%}"

    def fmt_delta_currency(val: float) -> str:
        if abs(val) >= 1e9:
            return f"{'+' if val >= 0 else ''}{val/1e9:,.1f}B"
        elif abs(val) >= 1e6:
            return f"{'+' if val >= 0 else ''}{val/1e6:,.1f}M"
        else:
            return f"{'+' if val >= 0 else ''}{val:,.0f}"

    def fmt_delta_days(val: float) -> str:
        return f"{val:+.1f} days"

    # Liquidity Ratios
    print("\nLIQUIDITY")
    print(f"{'Current Ratio':<30} {fmt_ratio(ratios.current_ratio):>15} "
          f"{fmt_ratio(ratios.current_ratio_prior):>15} "
          f"{fmt_delta_ratio(deltas['current_ratio_delta']):>15}")

    print(f"{'Cash Ratio':<30} {fmt_ratio(ratios.cash_ratio):>15} "
          f"{fmt_ratio(ratios.cash_ratio_prior):>15} "
          f"{fmt_delta_ratio(deltas['cash_ratio_delta']):>15}")

    # Leverage Ratios
    print("\nLEVERAGE")
    print(f"{'Debt-to-Equity':<30} {fmt_ratio(ratios.debt_to_equity):>15} "
          f"{fmt_ratio(ratios.debt_to_equity_prior):>15} "
          f"{fmt_delta_ratio(deltas['debt_to_equity_delta']):>15}")

    # Coverage Ratios
    print("\nCOVERAGE")
    print(f"{'EBITDA Interest Coverage':<30} {fmt_ratio(ratios.ebitda_interest_coverage):>15} "
          f"{fmt_ratio(ratios.ebitda_interest_coverage_prior):>15} "
          f"{fmt_delta_ratio(deltas['ebitda_interest_coverage_delta']):>15}")

    print(f"{'Net Debt / EBITDA':<30} {fmt_ratio(ratios.net_debt_to_ebitda):>15} "
          f"{fmt_ratio(ratios.net_debt_to_ebitda_prior):>15} "
          f"{fmt_delta_ratio(deltas['net_debt_to_ebitda_delta']):>15}")

    print(f"{'Net Debt / Adj. EBITDA':<30} {fmt_ratio(ratios.net_debt_to_adj_ebitda):>15} "
          f"{fmt_ratio(ratios.net_debt_to_adj_ebitda_prior):>15} "
          f"{fmt_delta_ratio(deltas['net_debt_to_adj_ebitda_delta']):>15}")

    # Efficiency
    print("\nEFFICIENCY")
    print(f"{'Days Sales Outstanding':<30} {fmt_days(ratios.days_sales_outstanding):>15} "
          f"{fmt_days(ratios.days_sales_outstanding_prior):>15} "
          f"{fmt_delta_days(deltas['days_sales_outstanding_delta']):>15}")

    # Working Capital
    print("\nWORKING CAPITAL")
    print(f"{'Working Capital':<30} {fmt_currency(ratios.working_capital):>15} "
          f"{fmt_currency(ratios.working_capital_prior):>15} "
          f"{fmt_delta_currency(deltas['working_capital_delta']):>15}")

    # Returns
    print("\nRETURNS")
    print(f"{'Return on Assets':<30} {fmt_pct(ratios.return_on_assets):>15} "
          f"{fmt_pct(ratios.return_on_assets_prior):>15} "
          f"{fmt_delta_pct(deltas['return_on_assets_delta']):>15}")

    print(f"{'Return on Equity':<30} {fmt_pct(ratios.return_on_equity):>15} "
          f"{fmt_pct(ratios.return_on_equity_prior):>15} "
          f"{fmt_delta_pct(deltas['return_on_equity_delta']):>15}")

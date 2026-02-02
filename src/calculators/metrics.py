"""Financial metrics calculations."""

import pandas as pd
from dataclasses import dataclass


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


def calculate_metrics(
    income_statement: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cash_flows: pd.DataFrame,
) -> FinancialMetrics:
    """
    Calculate financial metrics from parsed statements.

    Args:
        income_statement: Parsed income statement DataFrame
        balance_sheet: Parsed balance sheet DataFrame
        cash_flows: Parsed cash flows DataFrame

    Returns:
        FinancialMetrics with calculated values
    """
    # TODO: Implement based on actual DataFrame structure
    raise NotImplementedError("Metrics calculation not yet implemented")

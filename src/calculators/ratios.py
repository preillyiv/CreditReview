"""Financial ratios calculations."""

import pandas as pd
from dataclasses import dataclass


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


def calculate_ratios(
    income_statement: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cash_flows: pd.DataFrame,
    ebitda: float,
    adjusted_ebitda: float,
) -> FinancialRatios:
    """
    Calculate financial ratios from parsed statements.

    Args:
        income_statement: Parsed income statement DataFrame
        balance_sheet: Parsed balance sheet DataFrame
        cash_flows: Parsed cash flows DataFrame
        ebitda: Calculated EBITDA from metrics
        adjusted_ebitda: Calculated Adjusted EBITDA from metrics

    Returns:
        FinancialRatios with calculated values
    """
    # TODO: Implement based on actual DataFrame structure
    raise NotImplementedError("Ratios calculation not yet implemented")

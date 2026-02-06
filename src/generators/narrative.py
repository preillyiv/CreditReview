"""LLM-based narrative generation for company reports."""

import os
from anthropic import Anthropic

from src.fetchers.yahoo import CompanyInfo, CorporateAction
from src.calculators.metrics import FinancialMetrics
from src.calculators.ratios import FinancialRatios


def generate_company_narrative(
    company_info: CompanyInfo,
    metrics: FinancialMetrics,
    ratios: FinancialRatios,
    corporate_actions: list[CorporateAction] | None = None,
) -> str:
    """
    Generate a company narrative using Claude.

    Args:
        company_info: Company information from Yahoo Finance
        metrics: Calculated financial metrics
        ratios: Calculated financial ratios
        corporate_actions: Recent corporate actions

    Returns:
        Generated narrative text
    """
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Build context for the prompt
    metrics_summary = _format_metrics_for_prompt(metrics)
    ratios_summary = _format_ratios_for_prompt(ratios)
    actions_summary = _format_actions_for_prompt(corporate_actions or [])

    prompt = f"""Write a brief company overview for {company_info.name} ({company_info.ticker}) for a financial report.

Company Background:
{company_info.description}

Sector: {company_info.sector}
Industry: {company_info.industry}
Employees: {company_info.employees:,}
Headquarters: {company_info.hq_city}, {company_info.hq_state}

Key Financial Metrics (Current vs Prior Year):
{metrics_summary}

Key Financial Ratios:
{ratios_summary}

Recent Corporate Actions:
{actions_summary}

Write 2-3 paragraphs covering:
1. What the company does and its market position
2. Recent financial performance highlights (growth, profitability trends)
3. Key developments or corporate actions

Keep the tone professional and factual. Focus on the most important insights from the financial data."""

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def _format_metrics_for_prompt(metrics: FinancialMetrics) -> str:
    """Format metrics for inclusion in prompt."""
    deltas = metrics.calculate_deltas()

    def fmt_currency(val: float) -> str:
        """Format a currency value with B/M suffix."""
        if abs(val) >= 1e9:
            return f"${val/1e9:,.1f}B"
        elif abs(val) >= 1e6:
            return f"${val/1e6:,.1f}M"
        else:
            return f"${val:,.0f}"

    return f"""- Revenue: {fmt_currency(metrics.top_line_revenue)} (Delta: {fmt_currency(deltas['top_line_revenue_delta'])})
- Gross Profit Margin: {metrics.gross_profit_margin:.1%} (Delta: {deltas['gross_profit_margin_delta']:.1%})
- Operating Income Margin: {metrics.operating_income_margin:.1%} (Delta: {deltas['operating_income_margin_delta']:.1%})
- EBITDA: {fmt_currency(metrics.ebitda)} (Delta: {fmt_currency(deltas['ebitda_delta'])})
- Net Income: {fmt_currency(metrics.net_income)} (Delta: {fmt_currency(deltas['net_income_delta'])})"""


def _format_ratios_for_prompt(ratios: FinancialRatios) -> str:
    """Format ratios for inclusion in prompt."""
    return f"""- Current Ratio: {ratios.current_ratio:.2f}x
- Debt-to-Equity: {ratios.debt_to_equity:.2f}x
- Net Debt/EBITDA: {ratios.net_debt_to_ebitda:.2f}x
- Return on Equity: {ratios.return_on_equity:.1%}"""


def _format_actions_for_prompt(actions: list[CorporateAction]) -> str:
    """Format corporate actions for inclusion in prompt."""
    if not actions:
        return "No recent corporate actions available."

    lines = []
    for action in actions[:5]:
        lines.append(f"- {action.date}: {action.description}")
    return "\n".join(lines)

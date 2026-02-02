"""Yahoo Finance data fetching via yfinance."""

import yfinance as yf
from dataclasses import dataclass


@dataclass
class CompanyInfo:
    """Company information from Yahoo Finance."""
    name: str = ""
    ticker: str = ""
    sector: str = ""
    industry: str = ""
    website: str = ""
    description: str = ""
    employees: int = 0
    hq_city: str = ""
    hq_state: str = ""
    hq_country: str = ""


@dataclass
class CorporateAction:
    """A corporate action event."""
    date: str
    action_type: str  # e.g., "dividend", "stock_split", "acquisition"
    description: str
    value: float | None = None


def fetch_company_info(ticker: str) -> CompanyInfo:
    """
    Fetch company information from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol

    Returns:
        CompanyInfo with company details
    """
    stock = yf.Ticker(ticker)
    info = stock.info

    return CompanyInfo(
        name=info.get("longName", ""),
        ticker=ticker,
        sector=info.get("sector", ""),
        industry=info.get("industry", ""),
        website=info.get("website", ""),
        description=info.get("longBusinessSummary", ""),
        employees=info.get("fullTimeEmployees", 0),
        hq_city=info.get("city", ""),
        hq_state=info.get("state", ""),
        hq_country=info.get("country", ""),
    )


def fetch_corporate_actions(ticker: str, limit: int = 10) -> list[CorporateAction]:
    """
    Fetch recent corporate actions from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of actions to return

    Returns:
        List of CorporateAction events
    """
    stock = yf.Ticker(ticker)
    actions = []

    # Dividends
    dividends = stock.dividends
    if not dividends.empty:
        for date, value in dividends.tail(5).items():
            actions.append(CorporateAction(
                date=str(date.date()),
                action_type="dividend",
                description=f"Dividend payment",
                value=float(value),
            ))

    # Stock splits
    splits = stock.splits
    if not splits.empty:
        for date, value in splits.tail(3).items():
            actions.append(CorporateAction(
                date=str(date.date()),
                action_type="stock_split",
                description=f"{value}:1 stock split",
                value=float(value),
            ))

    # Sort by date descending and limit
    actions.sort(key=lambda x: x.date, reverse=True)
    return actions[:limit]


def fetch_news(ticker: str, limit: int = 5) -> list[dict]:
    """
    Fetch recent news for a company.

    Args:
        ticker: Stock ticker symbol
        limit: Maximum number of news items

    Returns:
        List of news items with title, link, publisher, date
    """
    stock = yf.Ticker(ticker)
    news = stock.news[:limit] if stock.news else []

    return [
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "publisher": item.get("publisher", ""),
            "date": item.get("providerPublishTime", ""),
        }
        for item in news
    ]

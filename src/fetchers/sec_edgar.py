"""SEC EDGAR data fetching for financial statements."""

import requests
from dataclasses import dataclass, field


# SEC requires a User-Agent header with contact info
SEC_HEADERS = {
    "User-Agent": "FinancialReportingTool/1.0 (contact@example.com)",
    "Accept-Encoding": "gzip, deflate",
}

# Base URLs for SEC EDGAR API
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


@dataclass
class SECCompanyInfo:
    """Basic company info from SEC."""
    cik: str
    name: str
    ticker: str


@dataclass
class FinancialFact:
    """A single financial fact from XBRL."""
    label: str
    value: float
    unit: str
    end_date: str  # The actual period end date (use this for the data year)
    start_date: str  # Period start date (for income statement items)
    fiscal_year: int  # Fiscal year of the FILING (not the data!)
    fiscal_period: str  # FY, Q1, Q2, Q3, Q4
    form: str  # 10-K, 10-Q
    filed: str
    frame: str = ""  # e.g., "CY2024" - the calendar year frame


@dataclass
class SECFinancialData:
    """Raw financial data extracted from SEC EDGAR."""
    company: SECCompanyInfo
    facts: dict[str, list[FinancialFact]] = field(default_factory=dict)
    # Organized by concept name -> list of facts across time periods


def lookup_cik(ticker: str) -> SECCompanyInfo | None:
    """
    Look up a company's CIK number from their ticker symbol.

    Args:
        ticker: Stock ticker symbol (e.g., "AMZN")

    Returns:
        SECCompanyInfo with CIK, name, and ticker, or None if not found
    """
    response = requests.get(SEC_COMPANY_TICKERS_URL, headers=SEC_HEADERS)
    response.raise_for_status()

    data = response.json()
    ticker_upper = ticker.upper()

    # SEC returns dict with numeric keys, each containing cik_str, ticker, title
    for entry in data.values():
        if entry.get("ticker") == ticker_upper:
            # CIK needs to be zero-padded to 10 digits
            cik = str(entry["cik_str"]).zfill(10)
            return SECCompanyInfo(
                cik=cik,
                name=entry.get("title", ""),
                ticker=ticker_upper,
            )

    return None


def fetch_company_facts(cik: str) -> dict:
    """
    Fetch all XBRL facts for a company from SEC EDGAR.

    Args:
        cik: 10-digit CIK number (zero-padded)

    Returns:
        Raw JSON response with all company facts
    """
    url = SEC_COMPANY_FACTS_URL.format(cik=cik)
    response = requests.get(url, headers=SEC_HEADERS)
    response.raise_for_status()

    return response.json()


def extract_facts(raw_data: dict, concept: str, taxonomy: str = "us-gaap") -> list[FinancialFact]:
    """
    Extract facts for a specific concept from raw SEC data.

    Args:
        raw_data: Raw JSON from fetch_company_facts
        concept: XBRL concept name (e.g., "Revenues", "NetIncomeLoss")
        taxonomy: XBRL taxonomy (usually "us-gaap")

    Returns:
        List of FinancialFact objects for this concept
    """
    facts = []

    try:
        taxonomy_data = raw_data.get("facts", {}).get(taxonomy, {})
        concept_data = taxonomy_data.get(concept, {})

        # Facts are organized by unit type (USD, shares, etc.)
        for unit_type, unit_data in concept_data.get("units", {}).items():
            for entry in unit_data:
                # Skip if no fiscal year info
                if "fy" not in entry:
                    continue

                facts.append(FinancialFact(
                    label=concept_data.get("label", concept),
                    value=entry.get("val", 0),
                    unit=unit_type,
                    end_date=entry.get("end", ""),
                    start_date=entry.get("start", ""),
                    fiscal_year=entry.get("fy", 0),
                    fiscal_period=entry.get("fp", ""),
                    form=entry.get("form", ""),
                    filed=entry.get("filed", ""),
                    frame=entry.get("frame", ""),
                ))
    except (KeyError, TypeError):
        pass

    return facts


def get_calendar_year(fact: FinancialFact) -> int:
    """Extract the calendar year from a fact's end_date."""
    if fact.end_date:
        try:
            return int(fact.end_date[:4])
        except (ValueError, IndexError):
            pass
    return 0


def is_full_year_period(start_date: str, end_date: str) -> bool:
    """Check if the period between start and end is approximately one year."""
    if not start_date or not end_date:
        return True  # Balance sheet items have no start_date

    try:
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        # Full year should be roughly 360-370 days
        return 350 <= days <= 380
    except (ValueError, TypeError):
        return True


def get_annual_facts(facts: list[FinancialFact], years: int = 2) -> list[FinancialFact]:
    """
    Filter facts to get only annual (10-K) data for recent years.

    Uses the end_date to determine the fiscal year end,
    not the fiscal year of the filing (which includes prior years for comparison).

    Args:
        facts: List of FinancialFact objects
        years: Number of recent years to include

    Returns:
        Filtered list with only 10-K data, sorted by end_date descending
    """
    # Filter for 10-K filings with full-year data
    annual = []
    for f in facts:
        if f.form != "10-K":
            continue
        # For income statement items (have start_date), ensure it's a full year period
        if f.start_date and not is_full_year_period(f.start_date, f.end_date):
            continue
        annual.append(f)

    # Sort by end_date descending, then by filed date descending
    # to get the most recent filing's data for each period
    annual.sort(key=lambda x: (x.end_date, x.filed), reverse=True)

    # Take the most recent data for each unique end_date (fiscal year end)
    seen_ends = set()
    result = []
    for fact in annual:
        if fact.end_date and fact.end_date not in seen_ends:
            seen_ends.add(fact.end_date)
            result.append(fact)
            if len(result) >= years:
                break

    return result


# Common US-GAAP concepts we're interested in
# Note: Companies may use different concepts for similar items
# Order matters - put newer/more common tags first
COMMON_CONCEPTS = {
    # Revenue (ASC 606 tags first, then older)
    "revenue": [
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "TotalRevenuesAndOtherIncome",
    ],
    # Net Income
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    # Gross Profit
    "gross_profit": [
        "GrossProfit",
    ],
    # Operating Income
    "operating_income": [
        "OperatingIncomeLoss",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ],
    # Total Assets
    "total_assets": [
        "Assets",
    ],
    # Total Liabilities (don't include LiabilitiesAndStockholdersEquity - that's Assets!)
    "total_liabilities": [
        "Liabilities",
    ],
    # Stockholders Equity
    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    # Cash
    "cash": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
        "Cash",
    ],
    # Current Assets
    "current_assets": [
        "AssetsCurrent",
    ],
    # Current Liabilities
    "current_liabilities": [
        "LiabilitiesCurrent",
    ],
    # Long-term Debt
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    # Total Debt
    "total_debt": [
        "DebtLongtermAndShorttermCombinedAmount",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    # Interest Expense
    "interest_expense": [
        "InterestExpense",
        "InterestExpenseDebt",
    ],
    # Depreciation & Amortization (for EBITDA calculation)
    "depreciation_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
    ],
    # Cost of Revenue
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
    ],
    # Inventory
    "inventory": [
        "InventoryNet",
        "InventoryFinishedGoodsNetOfReserves",
    ],
    # Accounts Receivable
    "accounts_receivable": [
        "AccountsReceivableNetCurrent",
        "AccountsReceivableNet",
        "ReceivablesNetCurrent",
    ],
}


def fetch_financial_data(ticker: str) -> SECFinancialData | None:
    """
    Fetch all relevant financial data for a company from SEC EDGAR.

    Args:
        ticker: Stock ticker symbol

    Returns:
        SECFinancialData with company info and facts, or None if not found
    """
    # Look up CIK
    company = lookup_cik(ticker)
    if not company:
        return None

    # Fetch raw facts
    raw_data = fetch_company_facts(company.cik)

    # Extract facts for each concept we care about
    result = SECFinancialData(company=company)

    for category, concepts in COMMON_CONCEPTS.items():
        best_facts = None
        best_recency = ""

        for concept in concepts:
            facts = extract_facts(raw_data, concept)
            if facts:
                # Get the most recent annual fact for this concept
                annual = get_annual_facts(facts, years=1)
                if annual:
                    recency = annual[0].end_date
                    # Pick the concept with the most recent data
                    if recency > best_recency:
                        best_recency = recency
                        best_facts = facts

        if best_facts:
            result.facts[category] = best_facts

    return result


def get_available_concepts(raw_data: dict, taxonomy: str = "us-gaap") -> list[str]:
    """
    List all available concepts in the raw SEC data.
    Useful for exploring what data a company reports.

    Args:
        raw_data: Raw JSON from fetch_company_facts
        taxonomy: XBRL taxonomy to check

    Returns:
        List of concept names available in this company's filings
    """
    try:
        return list(raw_data.get("facts", {}).get(taxonomy, {}).keys())
    except (KeyError, TypeError):
        return []


def print_data_summary(data: SECFinancialData) -> None:
    """Print a summary of fetched data for debugging."""
    print(f"\n{'='*60}")
    print(f"Company: {data.company.name} ({data.company.ticker})")
    print(f"CIK: {data.company.cik}")
    print(f"{'='*60}\n")

    for category, facts in data.facts.items():
        annual = get_annual_facts(facts, years=2)
        if annual:
            print(f"{category}:")
            for fact in annual:
                value_str = f"${fact.value:,.0f}" if fact.unit == "USD" else f"{fact.value:,.2f}"
                period = f"{fact.start_date} to {fact.end_date}" if fact.start_date else f"as of {fact.end_date}"
                print(f"  {period}: {value_str}")
            print()

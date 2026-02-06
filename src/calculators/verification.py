"""
Verification checks for extracted financial data.

Runs automatic consistency checks to verify that subtotals add up correctly.
Checks are tolerance-based and run for both current and prior year.
"""

from dataclasses import dataclass, field

from src.models.extraction import ExtractionSession


@dataclass
class VerificationCheck:
    """A single verification check result."""
    check_id: str
    description: str
    formula: str
    lhs_value: float          # Left-hand side (computed)
    rhs_value: float          # Right-hand side (expected)
    difference: float         # Absolute difference
    tolerance: float          # Allowed tolerance as fraction (e.g., 0.01 = 1%)
    passed: bool
    severity: str             # "error" or "warning"
    year: str                 # "current" or "prior"
    skipped: bool = False     # True if required inputs were missing

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "description": self.description,
            "formula": self.formula,
            "lhs_value": self.lhs_value,
            "rhs_value": self.rhs_value,
            "difference": self.difference,
            "tolerance": self.tolerance,
            "passed": self.passed,
            "severity": self.severity,
            "year": self.year,
            "skipped": self.skipped,
        }


@dataclass
class VerificationResult:
    """Result of all verification checks."""
    checks: list[VerificationCheck] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.passed and not c.skipped)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and not c.skipped)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and not c.skipped and c.severity == "warning")

    @property
    def error_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed and not c.skipped and c.severity == "error")

    @property
    def skip_count(self) -> int:
        return sum(1 for c in self.checks if c.skipped)

    def to_dict(self) -> dict:
        return {
            "checks": [c.to_dict() for c in self.checks],
            "pass_count": self.pass_count,
            "fail_count": self.fail_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "skip_count": self.skip_count,
        }


def _check_tolerance(lhs: float, rhs: float, tolerance: float) -> bool:
    """Check if lhs and rhs are within tolerance of each other."""
    if lhs == 0 and rhs == 0:
        return True
    max_val = max(abs(lhs), abs(rhs))
    if max_val == 0:
        return True
    return abs(lhs - rhs) / max_val <= tolerance


def _get_val(session: ExtractionSession, key: str, prior: bool = False) -> float | None:
    """Get a raw value, returning None if not present."""
    return session.get_raw_value(key, prior=prior)


def _run_check(
    session: ExtractionSession,
    check_id: str,
    description: str,
    formula: str,
    lhs_keys: list[tuple[str, float]],  # list of (metric_key, multiplier) to sum for LHS
    rhs_key: str,
    tolerance: float,
    severity: str,
    prior: bool = False,
) -> VerificationCheck:
    """Run a single verification check."""
    year = "prior" if prior else "current"

    # Get RHS value
    rhs = _get_val(session, rhs_key, prior=prior)
    if rhs is None:
        return VerificationCheck(
            check_id=check_id, description=description, formula=formula,
            lhs_value=0, rhs_value=0, difference=0, tolerance=tolerance,
            passed=True, severity=severity, year=year, skipped=True,
        )

    # Compute LHS
    lhs = 0.0
    all_found = True
    for key, multiplier in lhs_keys:
        val = _get_val(session, key, prior=prior)
        if val is None:
            all_found = False
            break
        lhs += val * multiplier

    if not all_found:
        return VerificationCheck(
            check_id=check_id, description=description, formula=formula,
            lhs_value=0, rhs_value=rhs, difference=0, tolerance=tolerance,
            passed=True, severity=severity, year=year, skipped=True,
        )

    difference = abs(lhs - rhs)
    passed = _check_tolerance(lhs, rhs, tolerance)

    return VerificationCheck(
        check_id=check_id, description=description, formula=formula,
        lhs_value=lhs, rhs_value=rhs, difference=difference, tolerance=tolerance,
        passed=passed, severity=severity, year=year,
    )


def _run_accounting_equation(
    session: ExtractionSession,
    prior: bool = False,
) -> VerificationCheck:
    """Special check: Total Assets = Total Liabilities + Stockholders' Equity."""
    year = "prior" if prior else "current"
    check_id = "accounting_equation"
    description = "Accounting Equation"
    formula = "Total Assets = Total Liabilities + Stockholders' Equity"
    tolerance = 0.005  # 0.5%
    severity = "error"

    total_assets = _get_val(session, "total_assets", prior=prior)
    total_liabilities = _get_val(session, "total_liabilities", prior=prior)
    equity = _get_val(session, "stockholders_equity", prior=prior)

    if any(v is None for v in [total_assets, total_liabilities, equity]):
        return VerificationCheck(
            check_id=check_id, description=description, formula=formula,
            lhs_value=0, rhs_value=0, difference=0, tolerance=tolerance,
            passed=True, severity=severity, year=year, skipped=True,
        )

    lhs = total_assets
    rhs = total_liabilities + equity
    difference = abs(lhs - rhs)
    passed = _check_tolerance(lhs, rhs, tolerance)

    return VerificationCheck(
        check_id=check_id, description=description, formula=formula,
        lhs_value=lhs, rhs_value=rhs, difference=difference, tolerance=tolerance,
        passed=passed, severity=severity, year=year,
    )


def run_verification(session: ExtractionSession) -> VerificationResult:
    """
    Run all verification checks on an extraction session.

    Checks run for both current and prior year. Checks are skipped
    (not failed) if required inputs are missing.
    """
    result = VerificationResult()

    for prior in [False, True]:
        # 1. Gross Profit: Revenue - COGS = Gross Profit (1% tolerance, error)
        result.checks.append(_run_check(
            session,
            check_id="gross_profit",
            description="Gross Profit Check",
            formula="Revenue - Cost of Revenue = Gross Profit",
            lhs_keys=[("revenue", 1.0), ("cost_of_revenue", -1.0)],
            rhs_key="gross_profit",
            tolerance=0.01,
            severity="error",
            prior=prior,
        ))

        # 2. Operating Income: Gross Profit - OpEx items = Operating Income (5% tolerance, warning)
        result.checks.append(_run_check(
            session,
            check_id="operating_income",
            description="Operating Income Check",
            formula="Gross Profit - SGA - R&D - D&A - Other OpEx = Operating Income",
            lhs_keys=[
                ("gross_profit", 1.0),
                ("sga_expense", -1.0),
                ("rd_expense", -1.0),
                ("depreciation_amortization", -1.0),
                ("other_operating_expense", -1.0),
            ],
            rhs_key="operating_income",
            tolerance=0.05,
            severity="warning",
            prior=prior,
        ))

        # 3. Net Income: Pre-tax - Tax = Net Income (5% tolerance, warning)
        result.checks.append(_run_check(
            session,
            check_id="net_income",
            description="Net Income Check",
            formula="Income Before Tax - Income Tax = Net Income",
            lhs_keys=[("income_before_tax", 1.0), ("income_tax_expense", -1.0)],
            rhs_key="net_income",
            tolerance=0.05,
            severity="warning",
            prior=prior,
        ))

        # 4. Current Assets: sub-items sum = Total Current Assets (2% tolerance, warning)
        result.checks.append(_run_check(
            session,
            check_id="current_assets",
            description="Current Assets Check",
            formula="Cash + ST Investments + A/R + Inventories + Other CA = Total Current Assets",
            lhs_keys=[
                ("cash", 1.0),
                ("short_term_investments", 1.0),
                ("accounts_receivable", 1.0),
                ("inventories", 1.0),
                ("other_current_assets", 1.0),
            ],
            rhs_key="current_assets",
            tolerance=0.02,
            severity="warning",
            prior=prior,
        ))

        # 5. Accounting Equation: Total Assets = Total Liabilities + Equity (0.5% tolerance, error)
        result.checks.append(_run_accounting_equation(session, prior=prior))

        # 6. Current Liabilities: sub-items sum = Total Current Liabilities (2% tolerance, warning)
        result.checks.append(_run_check(
            session,
            check_id="current_liabilities",
            description="Current Liabilities Check",
            formula="A/P + ST Debt + Accrued + Other CL = Total Current Liabilities",
            lhs_keys=[
                ("accounts_payable", 1.0),
                ("short_term_debt", 1.0),
                ("accrued_liabilities", 1.0),
                ("other_current_liabilities", 1.0),
            ],
            rhs_key="current_liabilities",
            tolerance=0.02,
            severity="warning",
            prior=prior,
        ))

        # 7. Cash Flow: Ops + Investing + Financing = Net Change (1% tolerance, error)
        result.checks.append(_run_check(
            session,
            check_id="cash_flow",
            description="Cash Flow Check",
            formula="Cash from Ops + Cash from Investing + Cash from Financing = Net Change in Cash",
            lhs_keys=[
                ("cash_from_operations", 1.0),
                ("cash_from_investing", 1.0),
                ("cash_from_financing", 1.0),
            ],
            rhs_key="net_change_in_cash",
            tolerance=0.01,
            severity="error",
            prior=prior,
        ))

    return result

"""
FairCredit AI SA - Affordability Assessment Engine

This module provides a prototype affordability pre-assessment based on
South Africa's National Credit Act affordability framework and Regulation 23A.

The engine is intended for educational and prototype purposes only.
It does not replace the affordability assessment performed by a registered
South African credit provider and must not be interpreted as a guarantee
of credit approval.

References
----------
National Credit Act 34 of 2005
National Credit Regulations - Regulation 23A
Government Gazette No. 53154, 13 August 2025
"""

from dataclasses import dataclass, asdict


@dataclass
class AffordabilityResult:
    """
    Stores the results of a FairCredit affordability assessment.

    Monetary values are expressed in South African Rand (ZAR).
    """

    gross_income: float
    statutory_deductions: float
    net_income: float

    declared_living_expenses: float
    minimum_expense_norm: float
    living_expenses_used: float

    existing_debt_repayments: float
    maintenance_obligations: float

    discretionary_income: float

    proposed_installment: float
    remaining_after_new_credit: float

    affordability_pass: bool
    affordability_ratio: float

    status: str

    def to_dict(self):
        """Return the assessment result as a dictionary."""
        return asdict(self)


def minimum_expense_norm(gross_income: float) -> float:
    """
    Calculate the minimum monthly expense norm using the income bands
    applied under South Africa's affordability assessment framework.

    Parameters
    ----------
    gross_income : float
        Consumer's gross monthly income in Rand.

    Returns
    -------
    float
        Minimum monthly expense amount used for the affordability assessment.

    Notes
    -----
    Income bands:

    R0 - R800
        100% of income

    R800.01 - R6,250
        R800 + 6.75% of income above R800

    R6,250.01 - R25,000
        R1,167.88 + 9% of income above R6,250

    R25,000.01 - R50,000
        R2,855.38 + 8.2% of income above R25,000

    Above R50,000
        R4,905.38 + 6.75% of income above R50,000
    """

    if gross_income < 0:
        raise ValueError("Gross income cannot be negative.")

    if gross_income <= 800:
        expense = gross_income

    elif gross_income <= 6_250:
        expense = 800 + ((gross_income - 800) * 0.0675)

    elif gross_income <= 25_000:
        expense = 1_167.88 + ((gross_income - 6_250) * 0.09)

    elif gross_income <= 50_000:
        expense = 2_855.38 + ((gross_income - 25_000) * 0.082)

    else:
        expense = 4_905.38 + ((gross_income - 50_000) * 0.0675)

    return round(expense, 2)


def assess_affordability(
    gross_income: float,
    statutory_deductions: float,
    declared_living_expenses: float,
    existing_debt_repayments: float,
    maintenance_obligations: float,
    proposed_installment: float,
) -> AffordabilityResult:
    """
    Perform a FairCredit affordability pre-assessment.

    The assessment estimates whether the consumer appears to have
    sufficient discretionary income to accommodate a proposed new
    credit instalment.

    Parameters
    ----------
    gross_income : float
        Consumer's gross monthly income.

    statutory_deductions : float
        Monthly statutory deductions.

    declared_living_expenses : float
        Consumer's declared necessary monthly living expenses.

    existing_debt_repayments : float
        Existing monthly credit repayments.

    maintenance_obligations : float
        Maintenance and other committed monthly obligations.

    proposed_installment : float
        Estimated monthly repayment for the proposed new credit.

    Returns
    -------
    AffordabilityResult
        Structured result containing the affordability calculation.
    """

    values = {
        "gross_income": gross_income,
        "statutory_deductions": statutory_deductions,
        "declared_living_expenses": declared_living_expenses,
        "existing_debt_repayments": existing_debt_repayments,
        "maintenance_obligations": maintenance_obligations,
        "proposed_installment": proposed_installment,
    }

    # Negative financial values would make the affordability calculation
    # meaningless, so all user-provided monetary inputs are validated first.
    for name, value in values.items():
        if value < 0:
            raise ValueError(
                f"{name.replace('_', ' ').title()} cannot be negative."
            )

    # Net income represents income remaining after statutory deductions.
    net_income = gross_income - statutory_deductions

    if net_income < 0:
        raise ValueError(
            "Statutory deductions cannot exceed gross income."
        )

    regulatory_minimum = minimum_expense_norm(gross_income)

    # FairCredit uses the higher of the consumer's declared living expenses
    # and the regulatory minimum-expense norm.
    #
    # This prevents the assessment from becoming artificially favourable
    # because unrealistically low living expenses were entered.
    living_expenses_used = max(
        declared_living_expenses,
        regulatory_minimum,
    )

    # Discretionary income represents the amount remaining after necessary
    # expenses and existing financial obligations have been considered.
    discretionary_income = (
        net_income
        - living_expenses_used
        - existing_debt_repayments
        - maintenance_obligations
    )

    remaining_after_new_credit = (
        discretionary_income
        - proposed_installment
    )

    # The proposed repayment is considered affordable by this prototype
    # only when sufficient positive discretionary income remains available.
    affordability_pass = (
        discretionary_income > 0
        and discretionary_income >= proposed_installment
    )

    # This ratio indicates how much of the available discretionary income
    # would be consumed by the proposed repayment.
    #
    # A lower percentage indicates more financial breathing room.
    if discretionary_income > 0:
        affordability_ratio = (
            proposed_installment / discretionary_income
        )
    else:
        affordability_ratio = float("inf")

    # Translate the numerical outcome into a simple consumer-facing status.
    # These labels are FairCredit product labels and are not official
    # National Credit Regulator classifications.
    if not affordability_pass:
        status = "Not currently affordable"

    elif affordability_ratio <= 0.30:
        status = "Comfortable affordability"

    elif affordability_ratio <= 0.60:
        status = "Moderate affordability"

    else:
        status = "Tight affordability"

    return AffordabilityResult(
        gross_income=round(gross_income, 2),
        statutory_deductions=round(statutory_deductions, 2),
        net_income=round(net_income, 2),

        declared_living_expenses=round(
            declared_living_expenses, 2
        ),

        minimum_expense_norm=round(
            regulatory_minimum, 2
        ),

        living_expenses_used=round(
            living_expenses_used, 2
        ),

        existing_debt_repayments=round(
            existing_debt_repayments, 2
        ),

        maintenance_obligations=round(
            maintenance_obligations, 2
        ),

        discretionary_income=round(
            discretionary_income, 2
        ),

        proposed_installment=round(
            proposed_installment, 2
        ),

        remaining_after_new_credit=round(
            remaining_after_new_credit, 2
        ),

        affordability_pass=affordability_pass,

        affordability_ratio=round(
            affordability_ratio, 4
        ) if affordability_ratio != float("inf")
        else float("inf"),

        status=status,
    )
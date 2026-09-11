"""
FairCredit AI SA - What-If Simulator

This module allows users to explore how changes in their financial
position may affect both affordability and estimated credit risk.

The simulator is intended for educational and prototype purposes only.
It does not provide financial advice or guarantee any lending outcome.
"""

from copy import deepcopy

import pandas as pd

from src.affordability_engine import assess_affordability


def calculate_financial_ratios(profile: dict) -> dict:
    """
    Calculate the same engineered financial ratios used during
    FairCredit model training.

    These calculations must remain consistent with the modelling notebook
    so that predictions made in the application use the same feature logic.
    """

    profile = deepcopy(profile)

    net_income = max(profile["monthly_net_income"], 1)
    gross_income = max(profile["monthly_gross_income"], 1)

    profile["debt_to_income_ratio"] = (
        profile["existing_debt_repayments"] / net_income
    )

    profile["requested_credit_to_income_ratio"] = (
        profile["requested_credit_amount"] / (gross_income * 12)
    )

    profile["installment_to_income_ratio"] = (
        profile["proposed_installment"] / net_income
    )

    profile["expense_to_income_ratio"] = (
        profile["living_expenses_used"] / net_income
    )

    return profile
def predict_credit_risk(
    profile: dict,
    model,
    feature_names: list
) -> dict:
    """
    Estimate credit risk and convert it into a FairCredit readiness score.

    The risk probability comes from the trained Logistic Regression model.
    The readiness score is calculated as the inverse of estimated risk.

    This score is a FairCredit prototype indicator and is not an official
    South African credit score.
    """

    prepared_profile = calculate_financial_ratios(profile)

    model_input = pd.DataFrame(
        [{
            feature: prepared_profile[feature]
            for feature in feature_names
        }]
    )

    risk_probability = model.predict_proba(model_input)[0, 1]

    readiness_score = round(
        (1 - risk_probability) * 100
    )

    if risk_probability < 0.30:
        risk_level = "Lower Risk"

    elif risk_probability < 0.50:
        risk_level = "Moderate Risk"

    elif risk_probability < 0.70:
        risk_level = "Elevated Risk"

    else:
        risk_level = "Higher Risk"

    return {
        "risk_probability": risk_probability,
        "readiness_score": readiness_score,
        "risk_level": risk_level
    }
def simulate_scenario(
    original_profile: dict,
    model,
    feature_names: list,
    changes: dict
) -> dict:
    """
    Apply proposed financial changes and compare the consumer's
    original position with the simulated position.

    Parameters
    ----------
    original_profile : dict
        Current financial profile.

    model
        Trained FairCredit risk model.

    feature_names : list
        Features expected by the model.

    changes : dict
        Financial values to modify for the simulated scenario.

    Returns
    -------
    dict
        Comparison between the original and simulated financial position.
    """

    simulated_profile = deepcopy(original_profile)

    for field, value in changes.items():
        if field not in simulated_profile:
            raise KeyError(
                f"Unknown financial field: {field}"
            )

        simulated_profile[field] = value

    # Recalculate net income if gross income or deductions changed.
    simulated_profile["monthly_net_income"] = (
        simulated_profile["monthly_gross_income"]
        - simulated_profile["statutory_deductions"]
    )

    # Re-run the affordability assessment after the scenario changes.
    affordability = assess_affordability(
        gross_income=simulated_profile["monthly_gross_income"],
        statutory_deductions=simulated_profile["statutory_deductions"],
        declared_living_expenses=simulated_profile[
            "declared_living_expenses"
        ],
        existing_debt_repayments=simulated_profile[
            "existing_debt_repayments"
        ],
        maintenance_obligations=simulated_profile[
            "maintenance_obligations"
        ],
        proposed_installment=simulated_profile[
            "proposed_installment"
        ]
    )

    simulated_profile["living_expenses_used"] = (
        affordability.living_expenses_used
    )

    simulated_profile[
        "discretionary_income_before_new_credit"
    ] = affordability.discretionary_income

    risk_result = predict_credit_risk(
        simulated_profile,
        model,
        feature_names
    )

    return {
        "profile": simulated_profile,
        "affordability": affordability,
        "risk": risk_result
    }


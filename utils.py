# Utility functions for stress testing, rebalancing, drawdown, tax law changes, scoring
import numpy as np


def apply_stress_and_macro(
    pr_app,
    rental_app,
    sm_return,
    rental_rent_monthly,
    rental_vacancy,
    rental_prop_tax,
    rental_insurance,
    rental_maintenance,
    rate_schedule,
    stress_test,
    macro_scenario,
):
    # Stress Test
    if stress_test == "Interest Rate Spike":
        rate_schedule = {yr: rate + 0.02 for yr, rate in rate_schedule.items()}
    elif stress_test == "Market Crash":
        pr_app *= 0.5
        rental_app *= 0.5
        sm_return *= 0.5
    elif stress_test == "Rent Drop":
        rental_rent_monthly *= 0.7
    elif stress_test == "High Vacancy":
        rental_vacancy = min(1, rental_vacancy + 0.15)
    elif stress_test == "Combined Shock":
        rate_schedule = {yr: rate + 0.02 for yr, rate in rate_schedule.items()}
        pr_app *= 0.5
        rental_app *= 0.5
        sm_return *= 0.5
        rental_rent_monthly *= 0.7
        rental_vacancy = min(1, rental_vacancy + 0.15)
    # Macro Scenario
    if macro_scenario == "Recession":
        pr_app *= 0.7
        rental_app *= 0.7
        sm_return *= 0.7
        rental_rent_monthly *= 0.9
        rental_vacancy = min(1, rental_vacancy + 0.05)
    elif macro_scenario == "Inflation":
        rental_prop_tax *= 1.2
        rental_insurance *= 1.2
        rental_maintenance *= 1.2
        rate_schedule = {yr: rate + 0.01 for yr, rate in rate_schedule.items()}
    elif macro_scenario == "Housing Boom":
        pr_app *= 1.5
        rental_app *= 1.5
        rental_rent_monthly *= 1.2
    elif macro_scenario == "Housing Bust":
        pr_app *= 0.5
        rental_app *= 0.5
        rental_rent_monthly *= 0.8
        rental_vacancy = min(1, rental_vacancy + 0.10)
    return (
        pr_app,
        rental_app,
        sm_return,
        rental_rent_monthly,
        rental_vacancy,
        rental_prop_tax,
        rental_insurance,
        rental_maintenance,
        rate_schedule,
    )


def apply_rebalancing(s1_equity, s2_equity, s1_cashflow, s2_cashflow, rebalancing_action):
    if rebalancing_action == "Sell Rental Property":
        s1_equity = s1_equity[:5] + [s1_equity[5] for _ in range(len(s1_equity) - 5)]
        s1_cashflow = s1_cashflow[:5] + [0 for _ in range(len(s1_cashflow) - 5)]
    elif rebalancing_action == "Refinance PR":
        s1_cashflow = s1_cashflow[:5] + [c + 50_000 for c in s1_cashflow[5:]]
    elif rebalancing_action == "Increase Investment":
        s2_equity = s2_equity[:5] + [e * 1.1 for e in s2_equity[5:]]
    elif rebalancing_action == "Reduce Debt":
        s1_equity = s1_equity[:5] + [e + 25_000 for e in s1_equity[5:]]
        s2_equity = s2_equity[:5] + [e + 25_000 for e in s2_equity[5:]]
    return s1_equity, s2_equity, s1_cashflow, s2_cashflow


def apply_drawdown(s1_equity, s2_equity, s1_cashflow, s2_cashflow, drawdown_amount, years):
    if drawdown_amount > 0:
        s1_cashflow = [c - drawdown_amount for c in s1_cashflow]
        s2_cashflow = [c - drawdown_amount for c in s2_cashflow]
        s1_equity = [e - drawdown_amount * years for e in s1_equity]
        s2_equity = [e - drawdown_amount * years for e in s2_equity]
    return s1_equity, s2_equity, s1_cashflow, s2_cashflow


def apply_tax_change(s1_equity, s2_equity, future_tax_change):
    if future_tax_change == "Increase Capital Gains Tax":
        s1_equity = [e * 0.85 for e in s1_equity]
        s2_equity = [e * 0.85 for e in s2_equity]
    elif future_tax_change == "Increase Property Tax":
        s1_equity = [e - 5000 for e in s1_equity]
        s2_equity = [e - 5000 for e in s2_equity]
    elif future_tax_change == "Remove Mortgage Interest Deductibility":
        s2_equity = [e * 0.95 for e in s2_equity]
    return s1_equity, s2_equity


def score_scenarios(s1_equity, s2_equity, s1_cashflow, s2_cashflow, optimize_for, risk_tolerance, discipline):
    scores = {"Scenario 1": 0, "Scenario 2": 0}
    if "Net Worth" in optimize_for:
        scores["Scenario 1"] += np.mean(s1_equity)
        scores["Scenario 2"] += np.mean(s2_equity)
    if "Risk" in optimize_for:
        scores["Scenario 1"] -= int(np.std(s1_equity))
        scores["Scenario 2"] -= int(np.std(s2_equity))
    if "Liquidity" in optimize_for:
        scores["Scenario 1"] += np.sum(s1_cashflow)
        scores["Scenario 2"] += np.sum(s2_cashflow)
    if "Stress Resilience" in optimize_for:
        scores["Scenario 1"] += min(s1_equity)
        scores["Scenario 2"] += min(s2_equity)
    if "Lifestyle" in optimize_for:
        scores["Scenario 1"] += risk_tolerance * 10000 + discipline * 10000
        scores["Scenario 2"] += risk_tolerance * 10000 + discipline * 10000
    return scores

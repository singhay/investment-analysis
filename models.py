# Scenario modeling and financial calculation functions

from typing import Dict, List, Tuple
import numpy as np


def calculate_bc_tax(income: float) -> Tuple[float, float]:
    # Federal brackets (2025, approximate)
    fed_brackets = [0, 53359, 106717, 165430, 235675]
    fed_rates = [0.15, 0.205, 0.26, 0.29, 0.33]
    # BC brackets (2025, approximate)
    bc_brackets = [0, 45654, 91310, 104835, 127299, 172602, 240716]
    bc_rates = [0.0506, 0.077, 0.105, 0.1229, 0.147, 0.168, 0.205]

    def calc_tax(brackets, rates, income):
        tax = 0
        for i in range(1, len(brackets)):
            if income > brackets[i]:
                tax += (brackets[i] - brackets[i - 1]) * rates[i - 1]
            else:
                tax += (income - brackets[i - 1]) * rates[i - 1]
                break
        else:
            tax += (income - brackets[-1]) * rates[-1]
        # Marginal rate
        for i in range(len(brackets) - 1, 0, -1):
            if income > brackets[i]:
                return tax, rates[i]
        return tax, rates[0]

    fed_tax, fed_marginal = calc_tax(fed_brackets, fed_rates, income)
    bc_tax, bc_marginal = calc_tax(bc_brackets, bc_rates, income)
    total_tax = fed_tax + bc_tax
    marginal_rate = fed_marginal + bc_marginal
    return total_tax, marginal_rate


def mortgage_balance_schedule(principal: float, amort_years: int, rate_schedule: Dict[int, float]):
    balance = principal
    monthly_balances = []
    for y in range(1, amort_years + 1):
        applicable_years = [yr for yr in rate_schedule.keys() if yr <= y]
        rate = rate_schedule[max(applicable_years)] if applicable_years else list(rate_schedule.values())[0]
        r_month = rate / 12
        n_months = (amort_years - y + 1) * 12
        pmt = balance * r_month / (1 - (1 + r_month) ** -n_months)
        for m in range(12):
            interest = balance * r_month
            principal_paid = pmt - interest
            balance -= principal_paid
            monthly_balances.append(balance)
    return balance, monthly_balances


def scenario1_cashflow(
    pr_price,
    rental_price,
    down_pr1,
    rate_schedule,
    amort_years,
    rental_app,
    pr_app,
    heloc_delta,
    rental_rent_monthly,
    rental_vacancy,
    rental_prop_tax_list,
    rental_insurance_list,
    rental_maintenance_list,
    rental_purchase_year,
    pr_prop_tax_list,
    pr_insurance_list,
    pr_maintenance_list,
    capex_events=None,  # List of (year, amount)
    rent_growth=0.03,  # Annual rent growth, default 3%
):
    s1_equity_list = []
    cashflow_list = []
    if capex_events is None:
        capex_events = []
    capex_dict = {year: amount for year, amount in capex_events}

    pr_loan = pr_price * (1 - down_pr1)
    rental_down_payment = rental_price * 0.2
    rental_loan = rental_price - rental_down_payment
    # Get amortization tables for both properties
    _, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
    _, rental_monthly_balances = mortgage_balance_schedule(rental_loan, amort_years, rate_schedule)
    # Calculate yearly principal paid and interest paid
    pr_principal_paid = [
        (
            (
                pr_monthly_balances[min((i - 1) * 12, len(pr_monthly_balances) - 1)]
                - pr_monthly_balances[min(i * 12, len(pr_monthly_balances) - 1)]
            )
            if i > 0
            else (pr_loan - pr_monthly_balances[min(12, len(pr_monthly_balances) - 1)])
        )
        for i in range(amort_years)
    ]
    pr_interest_paid = [
        sum(
            [
                pr_monthly_balances[min(j, len(pr_monthly_balances) - 1)]
                * (rate_schedule[max([yr for yr in rate_schedule.keys() if yr <= (i + 1)], default=1)] / 12)
                for j in range(i * 12 if i > 0 else 0, min((i + 1) * 12, len(pr_monthly_balances)))
            ]
        )
        for i in range(amort_years)
    ]
    pr_total_payment = [pr_principal_paid[i] + pr_interest_paid[i] for i in range(amort_years)]
    rental_principal_paid = [
        (
            (
                rental_monthly_balances[min((i - 1) * 12, len(rental_monthly_balances) - 1)]
                - rental_monthly_balances[min(i * 12, len(rental_monthly_balances) - 1)]
            )
            if i > 0
            else (rental_loan - rental_monthly_balances[min(12, len(rental_monthly_balances) - 1)])
        )
        for i in range(amort_years)
    ]
    rental_interest_paid = [
        sum(
            [
                rental_monthly_balances[min(j, len(rental_monthly_balances) - 1)]
                * (rate_schedule[max([yr for yr in rate_schedule.keys() if yr <= (i + 1)], default=1)] / 12)
                for j in range(i * 12 if i > 0 else 0, min((i + 1) * 12, len(rental_monthly_balances)))
            ]
        )
        for i in range(amort_years)
    ]
    rental_total_payment = [rental_principal_paid[i] + rental_interest_paid[i] for i in range(amort_years)]

    # Calculate cashflow for each year
    for year in range(1, amort_years + 1):
        pr_idx = year - 1
        # Property value appreciation
        pr_future = pr_price * ((1 + pr_app) ** year)
        rental_future = rental_price * ((1 + rental_app) ** year)
        # Annual rent and expenses with variable rent growth
        effective_rent = rental_rent_monthly * ((1 + rent_growth) ** (year - 1))
        rent_income = effective_rent * 12 * (1 - rental_vacancy)
        pr_expenses = pr_prop_tax_list[pr_idx] + pr_insurance_list[pr_idx] + pr_maintenance_list[pr_idx]
        rental_expenses = rental_prop_tax_list[pr_idx] + rental_insurance_list[pr_idx] + rental_maintenance_list[pr_idx]
        expenses = pr_expenses + rental_expenses
        capex = capex_dict.get(year, 0)
        expenses += capex
        # Use amortization table values for payments
        pr_payment = pr_total_payment[pr_idx]
        rental_payment = rental_total_payment[pr_idx]
        net_cashflow = rent_income - expenses - pr_payment - rental_payment
        # Down payment/HELOC logic (unchanged)
        if rental_purchase_year > 0:
            months_paid = rental_purchase_year * 12
            principal_paid = (
                pr_loan - pr_monthly_balances[months_paid - 1] if months_paid <= len(pr_monthly_balances) else pr_loan
            )
        else:
            principal_paid = 0
        rental_down_payment = rental_price * 0.2
        heloc_used = min(principal_paid, rental_down_payment)
        cash_down_payment = rental_down_payment - heloc_used
        if year == rental_purchase_year:
            net_cashflow -= cash_down_payment
            net_cashflow -= heloc_used * (
                rate_schedule[max([yr for yr in rate_schedule.keys() if yr <= year], default=1)] + heloc_delta
            )
        elif year > rental_purchase_year and heloc_used > 0:
            net_cashflow -= heloc_used * (
                rate_schedule[max([yr for yr in rate_schedule.keys() if yr <= year], default=1)] + heloc_delta
            )
        cashflow_list.append(net_cashflow)
        equity = (
            pr_future
            - pr_monthly_balances[min(pr_idx * 12, len(pr_monthly_balances) - 1)]
            + (rental_future - rental_monthly_balances[min(pr_idx * 12, len(rental_monthly_balances) - 1)])
        )
        s1_equity_list.append(equity + sum(cashflow_list))

    return s1_equity_list, cashflow_list


def scenario2_cashflow(
    pr_price,
    sm_return,
    down_pr2,
    rate_schedule,
    amort_years,
    income_start,
    income_growth,
    pr_app,
    heloc_loan,
    heloc_delta,
    sm_principal,
    pr_prop_tax_list,
    pr_insurance_list,
    pr_maintenance_list,
    capex_events=None,  # List of (year, amount)
    rent_growth=0.03,  # Annual rent growth, default 3%
):
    s2_equity_list = []
    cashflow_list = []
    tax_savings_list = []
    if capex_events is None:
        capex_events = []
    capex_dict = {year: amount for year, amount in capex_events}

    # Initial PR loan
    pr_loan = pr_price * (1 - down_pr2)
    invest_principal = sm_principal

    for year in range(1, amort_years + 1):
        # PR appreciation
        pr_future = pr_price * ((1 + pr_app) ** year)

        # Investment growth
        invest_growth = invest_principal * ((1 + sm_return) ** year)

        # Annual income for marginal tax calculation
        income = income_start * ((1 + income_growth) ** year)
        # Calculate BC marginal tax rate for this income
        _, marginal_tax_rate = calculate_bc_tax(income)

        # Calculate base mortgage rate for this year
        applicable_years = [yr for yr in rate_schedule.keys() if yr <= year]
        mortgage_rate = rate_schedule[max(applicable_years)] if applicable_years else list(rate_schedule.values())[0]
        heloc_rate = mortgage_rate + heloc_delta

        # Interest on HELOC used for rental mortgage (tax-deductible)
        interest_payment = heloc_loan * heloc_rate
        tax_savings = interest_payment * marginal_tax_rate
        tax_savings_list.append(tax_savings)

        # Cash flow is the tax savings in SM minus CapEx, PR maintenance, and PR property tax for this year
        capex = capex_dict.get(year, 0)

        # Use PR expenses from sidebar
        pr_expenses = pr_prop_tax_list[year - 1] + pr_insurance_list[year - 1] + pr_maintenance_list[year - 1]
        cashflow_list.append(tax_savings - capex - pr_expenses)

        # Mortgage balance for PR at end of year
        pr_balance, _ = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)

        # Total equity including SM growth and cumulative cash flow
        s2_equity_list.append(pr_future - pr_balance + invest_growth + sum(cashflow_list))

    return s2_equity_list, cashflow_list, tax_savings_list

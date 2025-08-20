import pandas as pd
import streamlit as st
import plotly.express as px
from models import mortgage_balance_schedule


def amortization_table_pr(
    pr_loan, amort_years, rate_schedule, pr_prop_tax_list, pr_condo_fee, pr_insurance, pr_maintenance_list
):
    pr_interest_rate = rate_schedule[max(rate_schedule.keys())] if rate_schedule else 0.0395
    pr_monthly_rate = pr_interest_rate / 12
    _, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
    pr_years = range(1, amort_years + 1)
    pr_eoy_balances = [pr_monthly_balances[min(i * 12, len(pr_monthly_balances) - 1)] for i in range(amort_years)]
    pr_principal_paid = [
        pr_loan - pr_monthly_balances[min(i * 12, len(pr_monthly_balances) - 1)] for i in range(amort_years)
    ]
    pr_interest_paid = [
        pr_monthly_balances[min(i * 12, len(pr_monthly_balances) - 1)] * pr_monthly_rate * 12
        for i in range(amort_years)
    ]
    pr_total_monthly = [pr_interest_paid[i] + pr_principal_paid[i] for i in range(amort_years)]
    pr_expenses_col = [
        pr_prop_tax_list[i] + pr_condo_fee + pr_insurance + pr_maintenance_list[i] for i in range(amort_years)
    ]
    df = pd.DataFrame(
        {
            "Year": pr_years,
            "End-of-Year Balance": pr_eoy_balances,
            "Principal Paid": pr_principal_paid,
            "Interest Paid": pr_interest_paid,
            "Total Payment": pr_total_monthly,
            "Expenses": pr_expenses_col,
        }
    )
    st.dataframe(df, use_container_width=True)
    return df


def amortization_table_rental(
    rental_loan,
    amort_years,
    rate_schedule,
    rental_prop_tax_list,
    rental_insurance,
    rental_maintenance_list,
    rental_rent_monthly,
    rental_mgmt_fee,
    pr_loan,
    pr_monthly_balances,
):
    rental_interest_rate = rate_schedule[max(rate_schedule.keys())] if rate_schedule else 0.0395
    rental_monthly_rate = rental_interest_rate / 12
    _, rental_monthly_balances = mortgage_balance_schedule(rental_loan, amort_years, rate_schedule)
    rental_years = range(1, amort_years + 1)
    rental_eoy_balances = [
        rental_monthly_balances[min(i * 12, len(rental_monthly_balances) - 1)] for i in range(amort_years)
    ]
    rental_principal_paid = [
        rental_loan - rental_monthly_balances[min(i * 12, len(rental_monthly_balances) - 1)] for i in range(amort_years)
    ]
    rental_interest_paid = [
        rental_monthly_balances[min(i * 12, len(rental_monthly_balances) - 1)] * rental_monthly_rate * 12
        for i in range(amort_years)
    ]
    rental_total_monthly = [rental_interest_paid[i] + rental_principal_paid[i] for i in range(amort_years)]
    rental_expenses_col = [
        rental_prop_tax_list[i] + rental_insurance + rental_maintenance_list[i] + rental_rent_monthly * rental_mgmt_fee
        for i in range(amort_years)
    ]
    readvanceable_pr_principal = []
    rent_contribution = []
    for year in range(1, amort_years + 1):
        months_paid = year * 12
        principal_paid = pr_loan - pr_monthly_balances[min(months_paid - 1, len(pr_monthly_balances) - 1)]
        total_rental_payment = rental_loan / amort_years
        pr_contrib = min(principal_paid, total_rental_payment)
        rent_contrib = total_rental_payment - pr_contrib
        readvanceable_pr_principal.append(pr_contrib)
        rent_contribution.append(rent_contrib)
    df = pd.DataFrame(
        {
            "Year": rental_years,
            "End-of-Year Balance": rental_eoy_balances,
            "Principal Paid": rental_principal_paid,
            "Interest Paid": rental_interest_paid,
            "Total Payment": rental_total_monthly,
            "Expenses": rental_expenses_col,
            "Re-advanceable PR Principal": readvanceable_pr_principal,
            "Rent Contribution": rent_contribution,
        }
    )
    st.dataframe(df, use_container_width=True)
    return df


# Add more chart functions as needed...

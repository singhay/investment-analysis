# Save as app.py and run: streamlit run app.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import io

# --- Functions ---
def mortgage_balance_schedule(principal, amort_years, rate_schedule):
    balance = principal
    monthly_balances = []
    for y in range(1, amort_years+1):
        applicable_years = [yr for yr in rate_schedule.keys() if yr <= y]
        rate = rate_schedule[max(applicable_years)] if applicable_years else list(rate_schedule.values())[0]
        r_month = rate / 12
        n_months = (amort_years - y + 1) * 12
        pmt = balance * r_month / (1 - (1 + r_month)**-n_months)
        # Track end-of-year balance
        balance = balance * (1 + r_month)**12 - pmt * ((1 + r_month)**12 - 1) / r_month
        monthly_balances.append(balance)
    return balance, monthly_balances

def scenario1_cashflow(pr_price, rental_price, down_pr1, rate_schedule, amort_years,
                       rental_app, pr_app, rent_monthly, vacancy, prop_tax, condo_fee,
                       insurance, maintenance, mgmt_fee):
    s1_equity_list = []
    cashflow_list = []

    # Initial loan amounts
    pr_loan = pr_price * (1 - down_pr1)
    rental_loan = rental_price * 0.8  # assume 20% down for rental property

    for year in range(1, years+1):
        # Property value appreciation
        pr_future = pr_price * ((1 + pr_app)**year)
        rental_future = rental_price * ((1 + rental_app)**year)

        # Annual rent and expenses
        rent_income = rent_monthly * 12 * (1 - vacancy)
        expenses = prop_tax + condo_fee + insurance + maintenance + rent_income * mgmt_fee

        # Mortgage balances at start and end of year
        pr_balance_start, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
        rental_balance_start, rental_monthly_balances = mortgage_balance_schedule(rental_loan, amort_years, rate_schedule)

        # Approximate mortgage payments for the year (interest + principal)
        # Using change in balance method: payment = start_balance - end_balance + interest
        pr_rate = rate_schedule.get(min(rate_schedule.keys()), list(rate_schedule.values())[0])
        rental_rate = pr_rate  # assume same rate for simplicity
        pr_interest = pr_balance_start * pr_rate
        rental_interest = rental_balance_start * rental_rate

        pr_payment = pr_interest + (pr_loan / amort_years)  # principal + interest
        rental_payment = rental_interest + (rental_loan / amort_years)

        net_cashflow = rent_income - expenses - pr_payment - rental_payment
        cashflow_list.append(net_cashflow)

        # Equity calculation
        equity = pr_future - pr_balance_start + (rental_future - rental_balance_start)
        s1_equity_list.append(equity + sum(cashflow_list))

    return s1_equity_list, cashflow_list


def scenario2_cashflow(pr_price, sm_return, down_pr2, rate_schedule, amort_years,
                       income_start, income_growth, pr_app, annual_deductible_interest):
    s2_equity_list = []
    cashflow_list = []
    tax_savings_list = []

    # Initial PR loan
    pr_loan = pr_price * (1 - down_pr2)
    invest_principal = 250_000  # starting borrowed amount via SM
    marginal_tax_rate = 0.5  # assume 50% marginal tax rate for simplicity

    for year in range(1, years+1):
        # PR appreciation
        pr_future = pr_price * ((1 + pr_app)**year)

        # Investment growth
        invest_growth = invest_principal * ((1 + sm_return)**year)

        # Annual income for marginal tax calculation
        income = income_start * ((1 + income_growth)**year)

        # Interest on PR mortgage is tax deductible via SM
        pr_balance, _ = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
        interest_payment = pr_balance * annual_deductible_interest  # approximate annual interest
        tax_savings = interest_payment * marginal_tax_rate
        tax_savings_list.append(tax_savings)

        # Cash flow is the tax savings in SM
        cashflow_list.append(tax_savings)

        # Total equity including SM growth and cumulative cash flow
        s2_equity_list.append(pr_future - pr_balance + invest_growth + sum(cashflow_list))

    return s2_equity_list, cashflow_list, tax_savings_list



# --- Streamlit UI ---
st.title("BC Real Estate: PR vs SM Scenario Analysis with Cash Flow")
years = 10

# Inputs in Sidebar
sidebar = st.sidebar
sidebar.header("Input Variables")
pr_price = sidebar.number_input("Principal Residence Price", 500_000, 5_000_000, 1_300_000, step=50_000)
rental_price = sidebar.number_input("Rental Property Price", 500_000, 5_000_000, 1_000_000, step=50_000)
down_pr1 = sidebar.slider("PR Down Payment Scenario 1 (%)", 0, 50, 10)/100
down_pr2 = sidebar.slider("PR Down Payment Scenario 2 (%)", 0, 50, 20)/100
amort_years = sidebar.slider("Amortization (years)", 10, 30, 30)
pr_app = sidebar.slider("Principal Residence Appreciation (%)", 0, 10, 3)/100
rental_app = sidebar.slider("Rental Property Appreciation (%)", 0, 10, 5)/100
income_start = sidebar.number_input("Starting Income", 50_000, 1_000_000, 250_000, step=10_000)
income_growth = sidebar.slider("Income Growth (%)", 0, 10, 3)/100
annual_deductible_interest = sidebar.number_input("Annual Deductible Interest (SM)", 0, 100_000, 10_000, step=1_000)

# Principal Residence Maintenance Variables
sidebar.subheader("Principal Residence Expenses")
pr_prop_tax = sidebar.number_input("PR Annual Property Tax", 0, 50_000, 4_000, step=500)
pr_condo_fee = sidebar.number_input("PR Annual Condo Fee", 0, 50_000, 2_000, step=500)
pr_insurance = sidebar.number_input("PR Annual Insurance", 0, 50_000, 1_200, step=500)
pr_maintenance = sidebar.number_input("PR Annual Maintenance", 0, 50_000, 1_500, step=500)

# Rental / Operating Expenses Inputs
sidebar.subheader("Rental Property Expenses")
rent_monthly = sidebar.number_input("Monthly Rent", 0, 20_000, 4_000, step=100)
vacancy = sidebar.slider("Vacancy Rate (%)", 0, 20, 5)/100
prop_tax = sidebar.number_input("Rental Annual Property Tax", 0, 50_000, 5_000, step=500)
condo_fee = sidebar.number_input("Rental Annual Condo Fee", 0, 50_000, 3_000, step=500)
insurance = sidebar.number_input("Rental Annual Insurance", 0, 50_000, 1_500, step=500)
maintenance = sidebar.number_input("Rental Annual Maintenance", 0, 50_000, 2_000, step=500)
mgmt_fee = sidebar.slider("Property Management Fee (%)", 0, 10, 5)/100

# Rate schedule input
sidebar.markdown("### Mortgage Rate Schedule (Year: Rate %)")
rate_input = sidebar.text_area("Example: 1:3.95,3:4.5,5:5", "1:3.95,3:4.5,5:5")
rate_schedule = {}
try:
    for item in rate_input.split(','):
        yr, r = item.split(':')
        rate_schedule[int(yr)] = float(r)/100
except:
    sidebar.warning("Rate schedule input invalid, using default 3.95%")
    rate_schedule = {1: 0.0395}

# SM Return range for heatmap
sm_return = sidebar.slider("Smith Manoeuvre Return (%)", 0, 10, 5)/100


# --- Calculate Cash Flows ---
s1_equity, s1_cashflow = scenario1_cashflow(
    pr_price, rental_price, down_pr1, rate_schedule,
    amort_years, rental_app, pr_app,
    rent_monthly, vacancy, prop_tax, condo_fee,
    insurance, maintenance, mgmt_fee
)

s2_equity, s2_cashflow, tax_savings_list = scenario2_cashflow(
    pr_price, sm_return, down_pr2,
    rate_schedule, amort_years, income_start,
    income_growth, pr_app, annual_deductible_interest
)

# Display Summary in Main Pane
st.subheader("10-Year Projection Summary")
summary_df = pd.DataFrame({
    "Year": np.arange(1, years+1),
    "Scenario1 Equity ($)": s1_equity,
    "Scenario1 Cash Flow ($)": s1_cashflow,
    "Scenario2 Equity ($)": s2_equity,
    "Scenario2 Cash Flow ($)": s2_cashflow,
    "SM Tax Savings ($)": tax_savings_list
})
st.dataframe(summary_df, use_container_width=True)

# --- Sensitivity Table ---
st.subheader("Sensitivity Table with Cash Flow")
sm_range = np.linspace(0.04, 0.08, 5)
rental_range = np.linspace(0, 0.1, 5)
table_data = []
for r_app in rental_range:
    row = {"Rental Appreciation (%)": round(r_app*100,1)}
    for sm_ret in sm_range:
        s1_equity_list, _ = scenario1_cashflow(
            pr_price, rental_price, down_pr1, rate_schedule,
            amort_years, r_app, pr_app,
            rent_monthly, vacancy, prop_tax, condo_fee,
            insurance, maintenance, mgmt_fee
        )
        s2_equity_list, _, _ = scenario2_cashflow(
            pr_price, sm_ret, down_pr2,
            rate_schedule, amort_years, income_start,
            income_growth, pr_app, annual_deductible_interest
        )
        diff = s1_equity_list[-1] - s2_equity_list[-1]
        row[f"SM {round(sm_ret*100,1)}% Net Worth Diff"] = round(diff/1000,1)
    table_data.append(row)

df_sensitivity = pd.DataFrame(table_data)
st.dataframe(df_sensitivity, use_container_width=True)

# --- Interactive Heatmap ---
st.subheader("Interactive Net Worth Difference Heatmap")
net_diff = df_sensitivity[[col for col in df_sensitivity.columns if "Diff" in col]].to_numpy()
fig = px.imshow(
    net_diff,
    labels=dict(x="SM Return (%)", y="Rental Appreciation (%)", color="Net Worth Diff ($000)"),
    x=[round(x*100,1) for x in sm_range],
    y=[round(x*100,1) for x in rental_range],
    color_continuous_scale="RdYlGn"
)
st.plotly_chart(fig)

# --- Export to Excel ---
st.subheader("Export Data to Excel")
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    summary_df.to_excel(writer, index=False, sheet_name="10YearCashFlow")
    df_sensitivity.to_excel(writer, index=False, sheet_name="SensitivityTable")
st.download_button(
    label="Download Excel",
    data=output.getvalue(),
    file_name="RealEstate_CashFlow_Sensitivity.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
# --- End of Streamlit App ---
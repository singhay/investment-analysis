# Save as app.py and run: streamlit run app.py
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import io

# Import refactored modules
from models import mortgage_balance_schedule, scenario1_cashflow, scenario2_cashflow
from utils import apply_stress_and_macro, score_scenarios
from utils import apply_rebalancing, apply_drawdown, apply_tax_change

## --- Streamlit UI ---
st.set_page_config(page_title="Scenario Analysis", page_icon="💰", 
                   layout='wide', initial_sidebar_state='expanded', menu_items=None)
st.title("BC Real Estate: PR vs SM Scenario Analysis with Cash Flow")
st.markdown(
    """
### **Scenario 1: Principal Residence (10% Down Payment)**  
- Buy a principal residence with a 10% down payment and a rental property with the remaining cash for a 20% down payment.  
- Build equity through property appreciation and rental income.

Cons:
- Use a re-advanceable mortgage feature: as you pay down your principal residence mortgage over the amort_years. Once 20% equity is built (5y in our case), any principal that's paid-down amount becomes instantly available to help fund the rental property mortgage payment which in-turn becomes tax-deductible.
- But to start doing Smith Manoeuvre, we'll have to wait 5 amort_years (until we have enough equity).

### **Scenario 2: Principal Residence + Smith Manoeuvre (20% Down Payment)**  
- Buy a principal residence with a 20% down payment. 
- Benefit from tax-deductible interest and potential investment growth.
- Use the Smith Manoeuvre: take re-advanceable mortgage on the principals after the 20% equity to pay rental property mortgage.  

Cons:
- Will have to save money to buy a rental property in the future. Currently available 350k - 300k (PR 20%) = 50k, will need another 100k to be able to afford 750k property. 100k will take 2 amort_years to save at 50k/year.
- So this strategy involves waiting and potentially missing out on market opportunities.
- Rental property may appreciate in value during the waiting period making buying it more expensive / out of reach. In other words, loosing out on rental income + appreciation during the waiting period.

**Analysis Overview:**  
This tool projects your cash flow, equity, and net worth over 10 amort_years for both strategies.  
You can adjust key variables to see how each scenario performs, helping you compare the impact of different approaches and make informed decisions for your financial goals.
    """
)

st.title("Investment Scenario Analysis")
sidebar = st.sidebar
sidebar.header("Input Variables")
pr_price = sidebar.number_input("Principal Residence Price", 500_000, 2_000_000, 1_300_000, step=50_000)
rental_price = sidebar.number_input("Rental Property Price", 500_000, 1_000_000, 800_000, step=50_000)
down_pr1 = sidebar.slider("PR Down Payment Scenario 1 (%)", 0, 50, 10) / 100
down_pr2 = sidebar.slider("PR Down Payment Scenario 2 (%)", 0, 50, 20) / 100
amort_years = sidebar.slider("Amortization (amort_years)", 10, 30, 30)
pr_app = sidebar.slider("Principal Residence Appreciation (%)", 0, 10, 3) / 100
rental_app = sidebar.slider("Rental Property Appreciation (%)", 0, 10, 5) / 100
# income_start = sidebar.number_input("Starting Income", 50_000, 1_000_000, 250_000, step=10_000)
# income_growth = sidebar.slider("Income Growth (%)", 0, 10, 3) / 100
income_start, income_growth = 250_000, 0.03
heloc_loan = sidebar.number_input("HELOC Loan for Rental Mortgage ($)", 0, 1_000_000, 250_000, step=10_000)
# heloc_rate = sidebar.slider("HELOC Interest Rate (%)", 0.0, 10.0, 6.0) / 100
heloc_delta = sidebar.slider("HELOC Rate Delta (%)", 0.0, 5.0, 1.0, step=0.1) / 100
sm_principal = sidebar.number_input("SM Initial Principal ($)", 0, 1_000_000, 250_000, step=10_000)
marginal_tax_rate = sidebar.slider("Marginal Tax Rate (%)", 0, 100, 50) / 100

# Principal Residence Maintenance Variables
sidebar.subheader("Principal Residence Expenses")
pr_prop_tax_base = sidebar.number_input("PR Base Property Tax ($)", 0, 50_000, 4_000, step=500)
pr_prop_tax_yoy_increase = sidebar.slider("PR Property Tax YoY Increase (%)", 0, 10, 2, step=1) / 100
pr_insurance_base = sidebar.number_input("PR Base Annual Insurance ($)", 0, 10_000, 1_200, step=500)
pr_insurance_yoy_increase = sidebar.slider("PR Insurance YoY Increase (%)", 0, 10, 2, step=1) / 100
pr_maintenance_base = sidebar.number_input("PR Annual Maintenance ($)", 0, 12_000, 2_000, step=500)
pr_maintenance_yoy_increase = sidebar.slider("PR Maintenance YoY Increase (%)", 0, 10, 2, step=1) / 100

# Rental / Operating Expenses Inputs
sidebar.subheader("Rental Property Expenses")
rental_rent_monthly = sidebar.number_input("Monthly Rent", 0, 20_000, 4_000, step=100)
rental_vacancy = sidebar.slider("Vacancy Rate (%)", 0, 20, 5, step=1) / 100
rental_prop_tax_base = sidebar.number_input("Rental Base Property Tax ($)", 0, 50_000, 5_000, step=500)
rental_prop_tax_yoy_increase = sidebar.slider("Rental Property Tax YoY Increase (%)", 0, 10, 2, step=1) / 100
rental_insurance_base = sidebar.number_input("Rental Base Annual Insurance ($)", 0, 50_000, 1_500, step=500)
rental_insurance_yoy_increase = sidebar.slider("Rental Insurance YoY Increase (%)", 0, 10, 2, step=1) / 100
rental_maintenance_base = sidebar.number_input("Rental Base Maintenance ($)", 0, 50_000, 2_000, step=500)
rental_maintenance_yoy_increase = sidebar.slider("Rental Maintenance YoY Increase (%)", 0, 10, 2, step=1) / 100

# Rental Purchase Timing
sidebar.subheader("Rental Purchase Timing")
rental_purchase_year = sidebar.slider("Year of Rental Purchase", 0, 30, 0)

# Rate schedule input
sidebar.markdown("### Mortgage Rate Schedule (Year: Rate %)")
rate_input = sidebar.text_area("Example: 1:3.95,3:3.45,5:3.25", "1:3.95,3:3.45,5:3.25")
rate_schedule = {}
try:
    for item in rate_input.split(","):
        if ":" not in item:
            continue
        yr, r = item.split(":")
        yr = int(yr.strip())
        r = float(r.strip()) / 100
        if yr > 0 and 0 < r < 1:
            rate_schedule[yr] = r
except Exception as e:
    sidebar.warning(f"Rate schedule input invalid, using default 3.95%. Error: {e}")
    rate_schedule = {1: 0.0395}
if not rate_schedule:
    rate_schedule = {1: 0.0395}

# SM Return range for heatmap
sm_return = sidebar.slider("Smith Manoeuvre Return (%)", 0, 10, 5) / 100


# --- Future-Proofing & Stress Testing ---
sidebar.header("Future-Proofing & Stress Testing")

# 1. Stress Testing
stress_test = sidebar.selectbox(
    "Stress Test Scenario",
    ["None", "Interest Rate Spike", "Market Crash", "Rent Drop", "High Vacancy", "Combined Shock"],
)

# 2. Scenario Narratives
macro_scenario = sidebar.selectbox(
    "Macroeconomic Scenario", ["Base Case", "Recession", "Inflation", "Housing Boom", "Housing Bust"]
)

# 3. Dynamic Rebalancing
rebalancing_action = sidebar.selectbox(
    "Mid-Course Correction", ["None", "Sell Rental Property", "Refinance PR", "Increase Investment", "Reduce Debt"]
)

# 4. Drawdown Analysis
drawdown_amount = sidebar.number_input("Annual Drawdown ($, for emergencies/retirement)", 0, 500_000, 0, step=10_000)

# 5. Tax Law Change Simulation
future_tax_change = sidebar.selectbox(
    "Future Tax Law Change",
    ["None", "Increase Capital Gains Tax", "Increase Property Tax", "Remove Mortgage Interest Deductibility"],
)

# 6. Multi-Objective Optimization
optimize_for = sidebar.multiselect(
    "Optimize For", ["Net Worth", "Risk", "Liquidity", "Stress Resilience", "Lifestyle"], default=["Net Worth"]
)

# 7. Decision Tree Visualization (scaffold)
# Will be implemented as a chart in the main pane

# 8. Behavioral Factors
risk_tolerance = sidebar.slider("Risk Tolerance (1=Low, 10=High)", 1, 10, 5)
discipline = sidebar.slider("Investment Discipline (1=Low, 10=High)", 1, 10, 7)


# --- Apply Stress Test & Macro Scenario Adjustments ---


# --- Monte Carlo with Correlations (scaffold) ---
# For simplicity, not implemented in main simulation yet


# --- Calculate Cash Flows ---
# Calculate maintenance and property tax for each year
pr_maintenance_list = [pr_maintenance_base * ((1 + pr_maintenance_yoy_increase) ** i) for i in range(amort_years)]
rental_maintenance_list = [
    rental_maintenance_base * ((1 + rental_maintenance_yoy_increase) ** i) for i in range(amort_years)
]
pr_prop_tax_list = [pr_prop_tax_base * ((1 + pr_prop_tax_yoy_increase) ** i) for i in range(amort_years)]
rental_prop_tax_list = [rental_prop_tax_base * ((1 + rental_prop_tax_yoy_increase) ** i) for i in range(amort_years)]
pr_insurance_list = [pr_insurance_base * ((1 + pr_insurance_yoy_increase) ** i) for i in range(amort_years)]
rental_insurance_list = [rental_insurance_base * ((1 + rental_insurance_yoy_increase) ** i) for i in range(amort_years)]

s1_equity, s1_cashflow = scenario1_cashflow(
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
)

s2_equity, s2_cashflow, tax_savings_list = scenario2_cashflow(
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
)

# --- Apply Dynamic Rebalancing ---
s1_equity, s2_equity, s1_cashflow, s2_cashflow = apply_rebalancing(
    s1_equity, s2_equity, s1_cashflow, s2_cashflow, rebalancing_action
)

# --- Apply Drawdown Analysis ---
s1_equity, s2_equity, s1_cashflow, s2_cashflow = apply_drawdown(
    s1_equity, s2_equity, s1_cashflow, s2_cashflow, drawdown_amount, amort_years
)

# --- Apply Tax Law Change ---
s1_equity, s2_equity = apply_tax_change(s1_equity, s2_equity, future_tax_change)

# Display Summary in Main Pane
st.subheader(f"{amort_years}-Year Projection Summary")
summary_df = pd.DataFrame(
    {
        "Year": np.arange(1, amort_years + 1),
        "Scenario1 Equity ($)": s1_equity,
        "Scenario1 Cash Flow ($)": s1_cashflow,
        "Scenario2 Equity ($)": s2_equity,
        "Scenario2 Cash Flow ($)": s2_cashflow,
        "SM Tax Savings ($)": tax_savings_list,
    }
)
st.dataframe(summary_df, use_container_width=True)

# --- Net Worth Chart ---
st.subheader("Net Worth Over Time: Scenario 1 vs Scenario 2")
fig_networth = px.line(
    summary_df,
    x="Year",
    y=["Scenario1 Equity ($)", "Scenario2 Equity ($)"],
    labels={"value": "Net Worth ($)", "variable": "Scenario"},
    title="Net Worth Over Time",
)
st.plotly_chart(fig_networth, use_container_width=True)

# --- Cash Flow Over Time ---
st.subheader("Annual Cash Flow Over Time")
fig_cashflow = px.line(
    summary_df,
    x="Year",
    y=["Scenario1 Cash Flow ($)", "Scenario2 Cash Flow ($)"],
    labels={"value": "Annual Cash Flow ($)", "variable": "Scenario"},
    title="Annual Cash Flow Over Time",
)
st.plotly_chart(fig_cashflow, use_container_width=True)

# --- Cumulative Cash Flow ---
st.subheader("Cumulative Cash Flow Over Time")
cum_cashflow_df = pd.DataFrame(
    {
        "Year": summary_df["Year"],
        "Scenario 1 Cumulative Cash Flow": np.cumsum(summary_df["Scenario1 Cash Flow ($)"]),
        "Scenario 2 Cumulative Cash Flow": np.cumsum(summary_df["Scenario2 Cash Flow ($)"]),
    }
)
fig_cumcash = px.line(
    cum_cashflow_df,
    x="Year",
    y=["Scenario 1 Cumulative Cash Flow", "Scenario 2 Cumulative Cash Flow"],
    labels={"value": "Cumulative Cash Flow ($)", "variable": "Scenario"},
    title="Cumulative Cash Flow Over Time",
)
st.plotly_chart(fig_cumcash, use_container_width=True)

# --- Tax Savings Over Time (Smith Manoeuvre) ---
st.subheader("Total Tax Saved Per Year Using Smith Manoeuvre")
fig_tax_saved = px.line(
    x=np.arange(1, amort_years + 1),
    y=tax_savings_list,
    labels={"x": "Year", "y": "Tax Saved ($)"},
    title="Total Tax Saved Per Year Using Smith Manoeuvre",
)
st.plotly_chart(fig_tax_saved, use_container_width=True)

# --- HELOC Balance Visualization ---
from models import scenario2_cashflow
# Re-run scenario2_cashflow to get heloc_balances
def get_heloc_balances(pr_price, sm_return, down_pr2, amort_years, rate_schedule, income_start, income_growth, pr_app, heloc_loan, heloc_delta, sm_principal, pr_prop_tax_list, pr_insurance_list, pr_maintenance_list):
    s2_equity_list, cashflow_list, tax_savings_list = scenario2_cashflow(
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
    )
    pr_loan = pr_price * (1 - down_pr2)
    _, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
    heloc_balances = []
    for year in range(1, amort_years + 1):
        pr_principal_paid = (
            pr_monthly_balances[min((year - 2) * 12, len(pr_monthly_balances) - 1)] - pr_monthly_balances[min((year - 1) * 12, len(pr_monthly_balances) - 1)]
        ) if year > 1 else (pr_loan - pr_monthly_balances[min(12, len(pr_monthly_balances) - 1)])
        heloc_balance = heloc_balances[-1] + pr_principal_paid if heloc_balances else pr_principal_paid
        heloc_balances.append(heloc_balance)
    return heloc_balances

heloc_balances = get_heloc_balances(
    pr_price=pr_price,
    sm_return=sm_return,
    down_pr2=down_pr2,
    amort_years=amort_years,
    rate_schedule=rate_schedule,
    income_start=income_start,
    income_growth=income_growth,
    pr_app=pr_app,
    heloc_loan=heloc_loan,
    heloc_delta=heloc_delta,
    sm_principal=sm_principal,
    pr_prop_tax_list=pr_prop_tax_list,
    pr_insurance_list=pr_insurance_list,
    pr_maintenance_list=pr_maintenance_list,
)
st.subheader("HELOC Balance Over Time (Smith Manoeuvre)")
years = np.arange(1, amort_years + 1)
# Calculate mortgage principal balance for each year
pr_loan = pr_price * (1 - down_pr2)
_, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
mortgage_principal_balances = [pr_monthly_balances[min(int(year) * 12, len(pr_monthly_balances) - 1)] for year in years]

fig_heloc = px.line(
    x=years,
    y=[heloc_balances, mortgage_principal_balances],
    labels={"x": "Year", "value": "Balance ($)", "variable": "Type"},
    title="HELOC vs Mortgage Principal Balance Over Time",
)
fig_heloc.update_traces(mode="lines")
fig_heloc.data[0].name = "HELOC Balance"
fig_heloc.data[1].name = "Mortgage Principal Balance"
st.plotly_chart(fig_heloc, use_container_width=True)

# --- Scenario Comparison Table ---
st.subheader("Scenario Comparison Table")
comparison_data = {
    "Metric": ["Final Net Worth", "Total Cash Flow", "Total Tax Savings"],
    "Scenario 1": [s1_equity[-1], np.sum(s1_cashflow), 0],
    "Scenario 2": [s2_equity[-1], np.sum(s2_cashflow), np.sum(tax_savings_list)],
}
comparison_df = pd.DataFrame(comparison_data)
st.dataframe(comparison_df, use_container_width=True)

# --- Sensitivity Table ---
st.subheader("Sensitivity Table with Cash Flow")
sm_range = np.linspace(0.04, 0.08, 5)
rental_range = np.linspace(0, 0.1, 5)
table_data = []
for r_app in rental_range:
    row = {"Rental Appreciation (%)": round(r_app * 100, 1)}
    for sm_ret in sm_range:
        s1_equity_list, _ = scenario1_cashflow(
            pr_price,
            rental_price,
            down_pr1,
            rate_schedule,
            amort_years,
            r_app,
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
        )
        s2_equity_list, _, _ = scenario2_cashflow(
            pr_price,
            sm_ret,
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
        )
        diff = s1_equity_list[-1] - s2_equity_list[-1]
        row[f"SM {round(sm_ret*100, 1)}% Net Worth Diff"] = round(diff / 1000, 1)
    table_data.append(row)

df_sensitivity = pd.DataFrame(table_data)
st.dataframe(df_sensitivity, use_container_width=True)

# --- Interactive Parameter Sensitivity ---
st.subheader("Interactive Sensitivity: Rental Appreciation vs SM Return")
net_diff = df_sensitivity[[col for col in df_sensitivity.columns if "Diff" in col]].to_numpy()
fig5 = px.imshow(
    net_diff,
    labels=dict(x="SM Return (%)", y="Rental Appreciation (%)", color="Net Worth Diff ($000)"),
    x=[round(x * 100, 1) for x in sm_range],
    y=[round(x * 100, 1) for x in rental_range],
    color_continuous_scale="RdYlGn",
)
st.plotly_chart(fig5)

# --- Export to Excel ---
st.subheader("Export Data to Excel")
output = io.BytesIO()
with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    summary_df.to_excel(writer, index=False, sheet_name="10YearCashFlow")
    df_sensitivity.to_excel(writer, index=False, sheet_name="SensitivityTable")
st.download_button(
    label="Download Excel",
    data=output.getvalue(),
    file_name="RealEstate_CashFlow_Sensitivity.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# --- Monte Carlo Simulation Panel ---
st.subheader("Monte Carlo Simulation: Net Worth Distribution")
num_simulations = st.slider("Number of Simulations", 100, 5000, 100, step=100)

# Sliders for appreciation and growth means and std devs
pr_app_mean = st.slider("PR Appreciation Mean (%)", 0, 10, 3, step=1) / 100
pr_app_std = st.slider("PR Appreciation Std Dev (%)", 0, 10, 2, step=1) / 100
prop_tax_mean = st.slider("Property Tax Mean ($)", 0, 10000, 5000, step=100)
prop_tax_std = st.slider("Property Tax Std Dev ($)", 0, 5000, 500, step=100)
pr_maintenance_mean = st.slider("PR Maintenance Mean ($)", 0, 10000, 3000, step=100)
pr_maintenance_std = st.slider("PR Maintenance Std Dev ($)", 0, 5000, 300, step=50)
pr_insurance_mean = st.slider("PR Insurance Mean ($)", 0, 5000, 1500, step=100)
pr_insurance_std = st.slider("PR Insurance Std Dev ($)", 0, 2000, 200, step=50)

rental_app_mean = st.slider("Rental Appreciation Mean (%)", 0, 10, 5, step=1) / 100
rental_app_std = st.slider("Rental Appreciation Std Dev (%)", 0, 10, 3, step=1) / 100
rental_maintenance_mean = st.slider("Rental Maintenance Mean ($)", 0, 5000, 2000, step=100)
rental_maintenance_std = st.slider("Rental Maintenance Std Dev ($)", 0, 2000, 300, step=50)
rental_insurance_mean = st.slider("Rental Insurance Mean ($)", 0, 5000, 1500, step=100)
rental_insurance_std = st.slider("Rental Insurance Std Dev ($)", 0, 2000, 200, step=50)

rent_growth_mean = st.slider("Rent Growth Mean (%)", 0, 10, 3, step=1) / 100
rent_growth_std = st.slider("Rent Growth Std Dev (%)", 0, 10, 2, step=1) / 100
vacancy_mean = st.slider("Vacancy Rate Mean (%)", 0, 20, 5, step=1) / 100
vacancy_std = st.slider("Vacancy Rate Std Dev (%)", 0, 10, 2, step=1) / 100

sm_return_mean = st.slider("SM Return Mean (%)", 0, 10, 5, step=1) / 100
sm_return_std = st.slider("SM Return Std Dev (%)", 0, 10, 4, step=1) / 100

income_start_mean = st.slider("Starting Income Mean ($)", 0, 1_000_000, 250_000, step=10_000)
income_start_std = st.slider("Starting Income Std Dev ($)", 0, 100_000, 20_000, step=5_000)
income_growth_mean = st.slider("Income Growth Mean (%)", 0, 10, 3, step=1) / 100
income_growth_std = st.slider("Income Growth Std Dev (%)", 0, 10, 2, step=1) / 100

mortgage_rate_mean = st.slider("Mortgage Rate Mean (%)", 0, 10, 4, step=1) / 100
mortgage_rate_std = st.slider("Mortgage Rate Std Dev (%)", 0, 10, 1, step=1) / 100
heloc_delta_mean = st.slider("HELOC Rate Delta Mean (%)", 0, 10, 1, step=1) / 100
heloc_delta_std = st.slider("HELOC Rate Delta Std Dev (%)", 0, 10, 0, step=1) / 100

# Correlation matrix for key variables (simplified)
cor_matrix = np.array([[1.0, 0.6, 0.5], [0.6, 1.0, 0.4], [0.5, 0.4, 1.0]])  # pr_app, rental_app, sm_return


# Store all simulation results and variables for chart
mc_results = []
for _ in range(num_simulations):
    # Correlated random draws for pr_app, rental_app, sm_return
    means = [pr_app_mean, rental_app_mean, sm_return_mean]
    stds = [pr_app_std, rental_app_std, sm_return_std]
    cov = np.outer(stds, stds) * cor_matrix
    pr_app_sim, rental_app_sim, sm_return_sim = np.random.multivariate_normal(means, cov, amort_years).T

    # Simulate other variables
    rent_monthly_sim = np.random.normal(rental_rent_monthly, rent_growth_std)
    rental_vacancy_sim = np.random.normal(rental_vacancy, vacancy_std)
    rental_prop_tax_sim = np.random.normal(rental_prop_tax_base, rental_prop_tax_base * rental_prop_tax_yoy_increase)
    rental_insurance_sim = np.random.normal(
        rental_insurance_base, rental_insurance_base * rental_insurance_yoy_increase
    )
    rental_maintenance_sim = np.random.normal(
        rental_maintenance_base, rental_maintenance_base * rental_maintenance_yoy_increase
    )
    rate_schedule_sim = rate_schedule.copy()
    income_growth_sim = np.random.normal(income_growth, income_growth_std)
    income_start_sim = np.random.normal(income_start, income_start_std)
    heloc_delta_sim = np.random.normal(heloc_delta, heloc_delta_std)

    pr_maintenance_base_sim = np.random.normal(pr_maintenance_mean, pr_maintenance_std)
    pr_maintenance_yoy_increase_sim = np.random.normal(pr_maintenance_yoy_increase, rent_growth_std)
    pr_insurance_base_sim = np.random.normal(pr_insurance_mean, pr_insurance_std)
    pr_insurance_yoy_increase_sim = np.random.normal(pr_insurance_yoy_increase, rent_growth_std)
    pr_prop_tax_base_sim = np.random.normal(pr_prop_tax_base, prop_tax_std)
    rental_prop_tax_base_sim = np.random.normal(rental_prop_tax_base, prop_tax_std)
    pr_prop_tax_yoy_increase_sim = np.random.normal(pr_prop_tax_yoy_increase, rent_growth_std)
    pr_prop_tax_list_sim = [
        pr_prop_tax_base_sim * ((1 + pr_prop_tax_yoy_increase_sim) ** i) for i in range(amort_years)
    ]
    pr_maintenance_list_sim = [
        pr_maintenance_base_sim * ((1 + pr_maintenance_yoy_increase_sim) ** i) for i in range(amort_years)
    ]
    pr_insurance_list_sim = [
        pr_insurance_base_sim * ((1 + pr_insurance_yoy_increase_sim) ** i) for i in range(amort_years)
    ]

    rental_maintenance_base_sim = np.random.normal(rental_maintenance_base, rental_maintenance_std)
    rental_maintenance_yoy_increase_sim = np.random.normal(rental_maintenance_yoy_increase, rent_growth_std)
    rental_insurance_base_sim = np.random.normal(rental_insurance_base, rental_insurance_std)
    rental_insurance_yoy_increase_sim = np.random.normal(rental_insurance_yoy_increase, rent_growth_std)
    rental_maintenance_base_sim = np.random.normal(rental_maintenance_base, rental_maintenance_std)
    rental_maintenance_yoy_increase_sim = np.random.normal(rental_maintenance_yoy_increase, rent_growth_std)
    rental_prop_tax_yoy_increase_sim = np.random.normal(rental_prop_tax_yoy_increase, rent_growth_std)
    rental_prop_tax_list_sim = [
        rental_prop_tax_base_sim * ((1 + rental_prop_tax_yoy_increase_sim) ** i) for i in range(amort_years)
    ]
    rental_insurance_list_sim = [
        rental_insurance_base_sim * ((1 + rental_insurance_yoy_increase_sim) ** i) for i in range(amort_years)
    ]
    rental_maintenance_list_sim = [
        rental_maintenance_base_sim * ((1 + rental_maintenance_yoy_increase_sim) ** i) for i in range(amort_years)
    ]
    rental_maintenance_list_sim = [
        rental_maintenance_base_sim * ((1 + rental_maintenance_yoy_increase_sim) ** i) for i in range(amort_years)
    ]

    # Apply stress/macro to each simulation
    (
        adj_pr_app,
        adj_rental_app,
        adj_sm_return,
        adj_rent_monthly,
        adj_vacancy,
        adj_prop_tax,
        adj_insurance,
        adj_maintenance,
        adj_rate_schedule,
    ) = apply_stress_and_macro(
        pr_app_sim.mean(),
        rental_app_sim.mean(),
        sm_return_sim.mean(),
        rent_monthly_sim,
        rental_vacancy_sim,
        rental_prop_tax_sim,
        rental_insurance_sim,
        rental_maintenance_sim,
        rate_schedule_sim,
        stress_test,
        macro_scenario,
    )

    s1_equity_sim, _ = scenario1_cashflow(
        pr_price,
        rental_price,
        down_pr1,
        rate_schedule_sim,
        amort_years,
        adj_rental_app,
        adj_pr_app,
        heloc_delta,
        adj_rent_monthly,
        adj_vacancy,
        rental_prop_tax_list_sim,
        rental_insurance_list_sim,
        rental_maintenance_list_sim,
        rental_purchase_year,
        pr_prop_tax_list_sim,
        pr_insurance_list_sim,
        pr_maintenance_list_sim,
    )
    s2_equity_sim, _, _ = scenario2_cashflow(
        pr_price,
        adj_sm_return,
        down_pr2,
        rate_schedule_sim,
        amort_years,
        income_start_sim,
        income_growth_sim,
        adj_pr_app,
        heloc_loan,
        heloc_delta_sim,
        sm_principal,
        pr_prop_tax_list_sim,
        pr_insurance_list_sim,
        pr_maintenance_list_sim,
    )
    # Store results for chart
    mc_results.append(
        {
            "s1_equity_sim": s1_equity_sim,
            "s2_equity_sim": s2_equity_sim,
            "pr_app_sim": adj_pr_app,
            "rental_app_sim": adj_rental_app,
            "sm_return_sim": adj_sm_return,
            "rent_monthly_sim": rent_monthly_sim,
            "vacancy_sim": rental_vacancy_sim,
            "prop_tax_sim": rental_prop_tax_sim,
            "insurance_sim": rental_insurance_sim,
            "maintenance_sim": rental_maintenance_sim,
            "mortgage_rate_sim": np.mean(list(rate_schedule_sim.values())),
            "income_growth_sim": income_growth_sim,
            "income_start_sim": income_start_sim,
            "heloc_delta_sim": heloc_delta_sim,
        }
    )


# Extract final net worth arrays from mc_results
final_networth_s1 = [r["s1_equity_sim"][-1] for r in mc_results]
final_networth_s2 = [r["s2_equity_sim"][-1] for r in mc_results]

# Histogram of final net worth
fig_mc = px.histogram(
    pd.DataFrame({"Scenario 1 Final Net Worth": final_networth_s1, "Scenario 2 Final Net Worth": final_networth_s2}),
    barmode="overlay",
    nbins=30,
    labels={"value": "Final Net Worth ($)", "variable": "Scenario"},
    title="Monte Carlo Simulation: Net Worth Distribution",
)
fig_mc.update_traces(opacity=0.6)
st.plotly_chart(fig_mc, use_container_width=True)

# Line chart of mean net worth over amort_years

# Prepare DataFrame for all paths

# Store all simulation variables for hover
mc_vars_s1 = []


years_range = np.arange(1, amort_years + 1)
df_paths = pd.DataFrame()
if "mc_results" in locals():
    for i, result in enumerate(mc_results):
        # Scenario 1
        df1 = pd.DataFrame(
            {
                "Year": years_range,
                "Net Worth": result["s1_equity_sim"],
                "Scenario": f"Scenario 1 (Sim {i+1})",
                **{k: [v] * amort_years for k, v in result.items() if k not in ["s1_equity_sim", "s2_equity_sim"]},
            }
        )
        df_paths = pd.concat([df_paths, df1], ignore_index=True)
        # Scenario 2
        df2 = pd.DataFrame(
            {
                "Year": years_range,
                "Net Worth": result["s2_equity_sim"],
                "Scenario": f"Scenario 2 (Sim {i+1})",
                **{k: [v] * amort_years for k, v in result.items() if k not in ["s1_equity_sim", "s2_equity_sim"]},
            }
        )
        df_paths = pd.concat([df_paths, df2], ignore_index=True)

    # Add mean lines (no hover vars)
    mean_networth_s1 = np.mean([r["s1_equity_sim"] for r in mc_results], axis=0)
    mean_networth_s2 = np.mean([r["s2_equity_sim"] for r in mc_results], axis=0)
    df_paths = pd.concat(
        [
            df_paths,
            pd.DataFrame({"Year": years_range, "Net Worth": mean_networth_s1, "Scenario": "Scenario 1 Mean"}),
            pd.DataFrame({"Year": years_range, "Net Worth": mean_networth_s2, "Scenario": "Scenario 2 Mean"}),
        ],
        ignore_index=True,
    )
    fig_mc_line = px.line(
        df_paths,
        x="Year",
        y="Net Worth",
        color="Scenario",
        labels={"Net Worth": "Net Worth ($)", "Scenario": "Simulation"},
        title="Monte Carlo Simulation: Net Worth Paths and Mean Over Time",
        line_group="Scenario",
        hover_name="Scenario",
        hover_data=[
            "pr_app_sim",
            "rental_app_sim",
            "sm_return_sim",
            "rent_monthly_sim",
            "vacancy_sim",
            "prop_tax_sim",
            "insurance_sim",
            "maintenance_sim",
            "mortgage_rate_sim",
            "income_growth_sim",
            "income_start_sim",
            "heloc_delta_sim",
        ],
    )
    # Make mean lines thicker
    fig_mc_line.update_traces(line=dict(width=1), opacity=0.15, selector=lambda trace: "Mean" not in trace.name)
    fig_mc_line.update_traces(line=dict(width=4), opacity=1, selector=lambda trace: "Mean" in trace.name)
    st.plotly_chart(fig_mc_line, use_container_width=True)
    st.write(
        f"Scenario 1 Final Net Worth: Mean = {np.mean(final_networth_s1):,.0f}, Std = {np.std(final_networth_s1):,.0f}"
        f" | PR appreciation: {np.mean([r['pr_app_sim'] for r in mc_results]):.2%}, "
        f"Rental appreciation: {np.mean([r['rental_app_sim'] for r in mc_results]):.2%}, "
        f"SM return: {np.mean([r['sm_return_sim'] for r in mc_results]):.2%}, "
        f"rent monthly: {np.mean([r['rent_monthly_sim'] for r in mc_results]):,.0f}, "
        f"vacancy: {np.mean([r['vacancy_sim'] for r in mc_results]):.2%}, "
        f"prop tax: {np.mean([r['prop_tax_sim'] for r in mc_results]):,.0f}, "
        f"insurance: {np.mean([r['insurance_sim'] for r in mc_results]):,.0f}, "
        f"maintenance: {np.mean([r['maintenance_sim'] for r in mc_results]):,.0f}, "
        f"mortgage rate: {np.mean([r['mortgage_rate_sim'] for r in mc_results]):.2%}, "
        f"income growth: {np.mean([r['income_growth_sim'] for r in mc_results]):.2%}, "
        f"income_start: {np.mean([r['income_start_sim'] for r in mc_results]):,.0f}, "
        f"heloc_delta: {np.mean([r['heloc_delta_sim'] for r in mc_results]):.2%}"
    )
    st.write(
        f"Scenario 2 Final Net Worth: Mean = {np.mean(final_networth_s2):,.0f}, Std = {np.std(final_networth_s2):,.0f}"
        f" | pr appreciation: {np.mean([r['pr_app_sim'] for r in mc_results]):.2%}, "
        f"rental appreciation: {np.mean([r['rental_app_sim'] for r in mc_results]):.2%}, "
        f"SM return: {np.mean([r['sm_return_sim'] for r in mc_results]):.2%}, "
        f"rent_monthly: {np.mean([r['rent_monthly_sim'] for r in mc_results]):,.0f}, "
        f"vacancy: {np.mean([r['vacancy_sim'] for r in mc_results]):.2%}, "
        f"prop_tax: {np.mean([r['prop_tax_sim'] for r in mc_results]):,.0f}, "
        f"insurance: {np.mean([r['insurance_sim'] for r in mc_results]):,.0f}, "
        f"maintenance: {np.mean([r['maintenance_sim'] for r in mc_results]):,.0f}, "
        f"mortgage rate: {np.mean([r['mortgage_rate_sim'] for r in mc_results]):.2%}, "
        f"income growth: {np.mean([r['income_growth_sim'] for r in mc_results]):.2%}, "
        f"income start: {np.mean([r['income_start_sim'] for r in mc_results]):,.0f}, "
        f"heloc delta: {np.mean([r['heloc_delta_sim'] for r in mc_results]):.2%}"
    )

# --- Amortization Table: Principal Residence ---
st.subheader("Amortization Table: Principal Residence")
pr_loan = pr_price * (1 - down_pr1)
pr_interest_rate = rate_schedule[max(rate_schedule.keys())] if rate_schedule else 0.0395
pr_monthly_rate = pr_interest_rate / 12
pr_n_months = amort_years * 12
pr_monthly_payment = pr_loan * pr_monthly_rate / (1 - (1 + pr_monthly_rate) ** -pr_n_months)
# Get monthly balances for PR
_, pr_monthly_balances = mortgage_balance_schedule(pr_loan, amort_years, rate_schedule)
pr_years = np.arange(1, amort_years + 1)
pr_eoy_balances = [pr_monthly_balances[min(i * 12, len(pr_monthly_balances) - 1)] for i in range(amort_years)]
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
            pr_monthly_balances[min(j, len(pr_monthly_balances) - 1)] * pr_monthly_rate
            for j in range(i * 12 if i > 0 else 0, min((i + 1) * 12, len(pr_monthly_balances)))
        ]
    )
    for i in range(amort_years)
]
pr_total_monthly = [pr_monthly_payment * 12 for _ in range(amort_years)]
pr_expenses_col = [pr_prop_tax_list[i] + pr_insurance_list[i] + pr_maintenance_list[i] for i in range(amort_years)]
pr_amort_df = pd.DataFrame(
    {
        "Year": pr_years,
        "End-of-Year Balance": pr_eoy_balances,
        "Principal Paid": pr_principal_paid,
        "Interest Paid": pr_interest_paid,
        "Total Payment": pr_total_monthly,
        "Expenses": pr_expenses_col,
    }
)
st.dataframe(pr_amort_df, use_container_width=True)

# --- Amortization Table: Rental Property ---
st.subheader("Amortization Table: Rental Property")
rental_down_payment = rental_price * 0.2
rental_loan = rental_price - rental_down_payment
rental_interest_rate = pr_interest_rate  # Assume same rate for simplicity
rental_monthly_rate = rental_interest_rate / 12
rental_n_months = amort_years * 12
rental_monthly_payment = rental_loan * rental_monthly_rate / (1 - (1 + rental_monthly_rate) ** -rental_n_months)
# Get monthly balances for Rental
_, rental_monthly_balances = mortgage_balance_schedule(rental_loan, amort_years, rate_schedule)
rental_years = np.arange(1, amort_years + 1)
rental_eoy_balances = [
    rental_monthly_balances[min(i * 12, len(rental_monthly_balances) - 1)] for i in range(amort_years)
]
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
            rental_monthly_balances[min(j, len(rental_monthly_balances) - 1)] * rental_monthly_rate
            for j in range(i * 12 if i > 0 else 0, min((i + 1) * 12, len(rental_monthly_balances)))
        ]
    )
    for i in range(amort_years)
]
rental_total_monthly = [rental_monthly_payment * 12 for _ in range(amort_years)]
rental_expenses_col = [
    rental_prop_tax_list[i] + rental_insurance_list[i] + rental_maintenance_list[i] for i in range(amort_years)
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
rental_amort_df = pd.DataFrame(
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
st.dataframe(rental_amort_df, use_container_width=True)

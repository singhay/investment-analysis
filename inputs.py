import streamlit as st


def get_sidebar_inputs():
    sidebar = st.sidebar
    sidebar.header("Input Variables")
    pr_price = sidebar.number_input("Principal Residence Price", 500_000, 2_000_000, 1_300_000, step=50_000)
    rental_price = sidebar.number_input("Rental Property Price", 500_000, 1_000_000, 800_000, step=50_000)
    down_pr1 = sidebar.slider("PR Down Payment Scenario 1 (%)", 0, 50, 10) / 100
    down_pr2 = sidebar.slider("PR Down Payment Scenario 2 (%)", 0, 50, 20) / 100
    amort_years = sidebar.slider("Amortization (years)", 10, 30, 30)
    pr_app = sidebar.slider("Principal Residence Appreciation (%)", 0, 10, 3) / 100
    rental_app = sidebar.slider("Rental Property Appreciation (%)", 0, 10, 5) / 100
    income_start = 250_000
    income_growth = 0.03
    heloc_loan = sidebar.number_input("HELOC Loan for Rental Mortgage ($)", 0, 1_000_000, 250_000, step=10_000)
    heloc_delta = sidebar.slider("HELOC Rate Delta (%)", 0.0, 5.0, 1.0, step=0.1) / 100
    sm_principal = sidebar.number_input("SM Initial Principal ($)", 0, 1_000_000, 250_000, step=10_000)
    marginal_tax_rate = sidebar.slider("Marginal Tax Rate (%)", 0, 100, 50) / 100

    # Principal Residence Maintenance Variables
    sidebar.subheader("Principal Residence Expenses")
    pr_prop_tax_base = sidebar.number_input("PR Base Property Tax ($)", 0, 50_000, 4_000, step=500)
    pr_prop_tax_yoy_increase = sidebar.slider("PR Property Tax YoY Increase (%)", 0, 10, 2, step=1) / 100
    pr_insurance = sidebar.number_input("PR Annual Insurance", 0, 10_000, 1_200, step=500)
    pr_maintenance_base = sidebar.number_input("PR Annual Maintenance ($)", 0, 12_000, 2_000, step=500)
    pr_maintenance_yoy_increase = sidebar.slider("PR Maintenance YoY Increase (%)", 0, 10, 2, step=1) / 100

    # Rental / Operating Expenses Inputs
    sidebar.subheader("Rental Property Expenses")
    rental_rent_monthly = sidebar.number_input("Monthly Rent", 0, 20_000, 4_000, step=100)
    rental_vacancy = sidebar.slider("Vacancy Rate (%)", 0, 20, 5, step=1) / 100
    rental_prop_tax_base = sidebar.number_input("Rental Base Property Tax ($)", 0, 50_000, 5_000, step=500)
    rental_prop_tax_yoy_increase = sidebar.slider("Rental Property Tax YoY Increase (%)", 0, 10, 2, step=1) / 100
    rental_insurance = sidebar.number_input("Rental Annual Insurance", 0, 50_000, 1_500, step=500)
    rental_maintenance_base = sidebar.number_input("Rental Base Maintenance ($)", 0, 50_000, 2_000, step=500)
    rental_maintenance_yoy_increase = sidebar.slider("Rental Maintenance YoY Increase (%)", 0, 10, 2, step=1) / 100
    rental_mgmt_fee = sidebar.slider("Property Management Fee (%)", 0, 10, 5, step=1) / 100

    # --- Future-Proofing & Stress Testing ---
    sidebar.header("Future-Proofing & Stress Testing")
    stress_test = sidebar.selectbox(
        "Stress Test Scenario",
        ["None", "Interest Rate Spike", "Market Crash", "Rent Drop", "High Vacancy", "Combined Shock"],
    )
    macro_scenario = sidebar.selectbox(
        "Macroeconomic Scenario", ["Base Case", "Recession", "Inflation", "Housing Boom", "Housing Bust"]
    )
    rebalancing_action = sidebar.selectbox(
        "Mid-Course Correction", ["None", "Sell Rental Property", "Refinance PR", "Increase Investment", "Reduce Debt"]
    )
    drawdown_amount = sidebar.number_input(
        "Annual Drawdown ($, for emergencies/retirement)", 0, 500_000, 0, step=10_000
    )
    future_tax_change = sidebar.selectbox(
        "Future Tax Law Change",
        ["None", "Increase Capital Gains Tax", "Increase Property Tax", "Remove Mortgage Interest Deductibility"],
    )
    optimize_for = sidebar.multiselect(
        "Optimize For", ["Net Worth", "Risk", "Liquidity", "Stress Resilience", "Lifestyle"], default=["Net Worth"]
    )
    risk_tolerance = sidebar.slider("Risk Tolerance (1=Low, 10=High)", 1, 10, 5)
    discipline = sidebar.slider("Investment Discipline (1=Low, 10=High)", 1, 10, 7)

    # Rental Purchase Timing
    sidebar.subheader("Rental Purchase Timing")
    rental_purchase_year = sidebar.slider("Year of Rental Purchase", 0, 30, 0)

    # Rate schedule input
    sidebar.markdown("### Mortgage Rate Schedule (Year: Rate %)")
    rate_input = sidebar.text_area("Example: 1:3.95,3:4.5,5:5", "1:3.95,3:4.5,5:5")
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

    return {
        "pr_price": pr_price,
        "rental_price": rental_price,
        "down_pr1": down_pr1,
        "down_pr2": down_pr2,
        "amort_years": amort_years,
        "pr_app": pr_app,
        "rental_app": rental_app,
        "income_start": income_start,
        "income_growth": income_growth,
        "heloc_loan": heloc_loan,
        "heloc_delta": heloc_delta,
        "sm_principal": sm_principal,
        "marginal_tax_rate": marginal_tax_rate,
        "pr_prop_tax_base": pr_prop_tax_base,
        "pr_prop_tax_yoy_increase": pr_prop_tax_yoy_increase,
        "pr_insurance": pr_insurance,
        "pr_maintenance_base": pr_maintenance_base,
        "pr_maintenance_yoy_increase": pr_maintenance_yoy_increase,
        "rental_rent_monthly": rental_rent_monthly,
        "rental_vacancy": rental_vacancy,
        "rental_prop_tax_base": rental_prop_tax_base,
        "rental_prop_tax_yoy_increase": rental_prop_tax_yoy_increase,
        "rental_insurance": rental_insurance,
        "rental_maintenance_base": rental_maintenance_base,
        "rental_maintenance_yoy_increase": rental_maintenance_yoy_increase,
        "rental_mgmt_fee": rental_mgmt_fee,
        "stress_test": stress_test,
        "macro_scenario": macro_scenario,
        "rebalancing_action": rebalancing_action,
        "drawdown_amount": drawdown_amount,
        "future_tax_change": future_tax_change,
        "optimize_for": optimize_for,
        "risk_tolerance": risk_tolerance,
        "discipline": discipline,
        "rental_purchase_year": rental_purchase_year,
        "rate_schedule": rate_schedule,
        "sm_return": sm_return,
    }

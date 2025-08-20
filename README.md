# BC Real Estate Investment Analysis App

## Overview
This Streamlit-based application provides a comprehensive scenario analysis and Monte Carlo simulation toolkit for real estate investment decisions in British Columbia, Canada. It models the financial outcomes of owning a principal residence (PR) versus leveraging the Smith Manoeuvre (SM) to invest in a rental property, incorporating stress testing, macroeconomic scenarios, dynamic rebalancing, tax law changes, and multi-objective optimization.

## Features
- **Interactive UI:** All key variables (property prices, down payments, appreciation rates, expenses, etc.) are adjustable via sidebar controls.
- **Scenario Modeling:** Compare PR-only and PR+SM rental scenarios with detailed cash flow and equity projections.
- **Stress Testing & Macro Scenarios:** Simulate interest rate spikes, market crashes, rent drops, high vacancy, and macroeconomic shifts (recession, inflation, boom/bust).
- **Dynamic Rebalancing:** Model mid-course corrections (sell rental, refinance PR, increase investment, reduce debt).
- **Drawdown Analysis:** Simulate emergency/retirement withdrawals.
- **Tax Law Change Simulation:** Model impacts of future tax changes (capital gains, property tax, mortgage interest deductibility).
- **Multi-Objective Optimization:** Score scenarios for net worth, risk, liquidity, resilience, and lifestyle.
- **Monte Carlo Simulation:** Run thousands of correlated simulations to visualize net worth distributions and sensitivity to key variables.
- **Export:** Download all results and sensitivity tables to Excel.

## Code Structure
- `app.py`: Main Streamlit app, UI, scenario orchestration, charts, and simulation logic.
- `models.py`: Core financial models and scenario cashflow calculations.
- `utils.py`: Utility functions for stress/macro adjustment, rebalancing, drawdown, tax change, and scoring.
- `config.py`: Default parameters and constants.
- `simulation.py`: (Scaffold) Monte Carlo and sensitivity analysis logic.

## How It Works
1. **User Inputs:** Set all variables in the sidebar (property prices, rates, expenses, etc.).
2. **Scenario Calculation:**
   - `scenario1_cashflow`: Models PR + rental property cash flow and equity.
   - `scenario2_cashflow`: Models PR + SM investment cash flow and equity.
3. **Adjustments:**
   - `apply_stress_and_macro`: Modifies variables for stress/macro scenarios.
   - `apply_rebalancing`, `apply_drawdown`, `apply_tax_change`: Apply mid-course corrections, withdrawals, and tax law changes.
4. **Visualization:**
   - Interactive charts for net worth, cash flow, cumulative cash flow, and tax savings.
   - Sensitivity tables and heatmaps for key variable impacts.
   - Monte Carlo simulation panel for distribution analysis.
5. **Export:**
   - Download all results to Excel for further analysis.

## Sample Scenarios
### Scenario 1: Base Case
- PR Price: $1,300,000
- Rental Price: $1,000,000
- Down Payment: 20% PR, 20% Rental
- PR Appreciation: 3%/yr
- Rental Appreciation: 5%/yr
- No stress/macro shocks
- Result: Steady equity growth, positive cash flow, moderate risk.

### Scenario 2: Stress Test
- Same as above, but with "Interest Rate Spike" and "Recession" selected.
- Result: Lower appreciation, higher mortgage costs, reduced cash flow, increased risk.

### Scenario 3: Drawdown & Tax Change
- Add $50,000 annual drawdown and "Increase Capital Gains Tax".
- Result: Reduced net worth, lower cash flow, higher tax impact.

### Scenario 4: Monte Carlo Simulation
- Run 1,000 simulations with variable appreciation, rent, vacancy, and expenses.
- Result: Distribution of final net worth, mean/stddev, and sensitivity to key variables.

## How to Run
1. Install dependencies:
   ```bash
   pip install streamlit pandas numpy plotly xlsxwriter
   ```
2. Start the app:
   ```bash
   streamlit run app.py
   ```
3. Adjust sidebar inputs and explore results.

## Extending the App
- Add new macro scenarios or stress tests in `utils.py`.
- Expand financial models in `models.py`.
- Implement advanced Monte Carlo logic in `simulation.py`.
- Add more export formats or charts as needed.

## License
MIT

## Authors
- Ayush Singh
- GitHub Copilot

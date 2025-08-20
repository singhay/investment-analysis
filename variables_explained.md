# Real Estate Analysis Variables & Thesis

This document explains the key variables used in the BC Real Estate: PR vs SM Scenario Analysis app, and the thesis behind the comparison.

1. **Principal Residence + Rental Property**: Traditional approach of buying a home and a rental property, building equity through appreciation and rental income. In scenario 1, principal given bi-weekly instantly becomes available via re-advanceable feature and get's used to pay part of the down payment of the rental.
2. **Principal Residence + Smith Manoeuvre**: Buy a home and use the Smith Manoeuvre to invest borrowed funds in a rental property, leveraging tax-deductible interest and investment growth.  

The analysis projects cash flow, equity, and net worth over 10 years, helping users understand the impact of different variables and choose the strategy that best fits their financial goals.

## Variables

### Principal Residence Price (`pr_price`)
The purchase price of the home you plan to live in.

### Rental Property Price (`rental_price`)
The purchase price of the investment property you plan to rent out.

### Down Payment (`down_pr1`, `down_pr2`)
The percentage of the property price paid upfront for the principal residence in each scenario.

### Amortization (`amort_years`)
The total number of years over which the mortgage is paid off.

### Appreciation Rates (`pr_app`, `rental_app`)
Expected annual increase in property values for principal residence and rental property.

### Income (`income_start`, `income_growth`)
Your starting annual income and expected annual growth rate.

### Annual Deductible Interest (`annual_deductible_interest`)
The portion of mortgage interest that is tax-deductible under the Smith Manoeuvre.

### SM Initial Principal (`sm_principal`)
The amount borrowed to invest using the Smith Manoeuvre.

### Marginal Tax Rate (`marginal_tax_rate`)
Your tax rate applied to deductible interest for tax savings.

### Rental Variables
- **Monthly Rent (`rent_monthly`)**: Expected monthly rent from the investment property.
- **Vacancy Rate (`vacancy`)**: Percentage of time the property is vacant.
- **Property Tax, Condo Fee, Insurance, Maintenance, Management Fee**: Annual costs associated with owning and operating the rental property.

### Mortgage Rate Schedule (`rate_schedule`)
A mapping of year to mortgage interest rate, allowing for rate changes over time.

### Smith Manoeuvre Return (`sm_return`)
Expected annual return on investments made using borrowed funds.

### MC Simulation parameters
```
PR Appreciation: mean 3%, std 2%
Rental Appreciation: mean 5%, std 3%
SM Return: mean 5%, std 4%
Rent Growth: mean 3%, std 2%
Vacancy Rate: mean 5%, std 2%
Property Tax: mean $5,000, std $500
Condo Fee: mean $3,000, std $300
Insurance: mean $1,500, std $200
Maintenance: mean $2,000, std $300
Management Fee: mean 5%, std 1%
Mortgage Rate: mean 4%, std 1%
Income Growth: mean 3%, std 2%
Starting Income: mean $250,000, std $20,000
HELOC Rate Delta: mean 1%, std 0.2%
```
The Monte Carlo simulation samples correlated variables (PR appreciation, rental appreciation, SM return) with realistic correlations. This makes your scenario analysis more robust and future-proof. 


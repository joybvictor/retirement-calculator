#!/usr/bin/env python3
"""
Comprehensive US Retirement Calculator - Needs-Based Withdrawals
Calculate exactly what you need to withdraw (not arbitrary 4% rule)
Includes expenses, home value, year-by-year to 80, comparison to 4% rule
by Joy Victor
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Tuple

# RMD Table (IRS Uniform Lifetime Table)
RMD_TABLE = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
    80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2
}

def calculate_account_growth(current_balance: float, years: int, 
                            contribution: float, rate: float) -> float:
    """Calculate account growth with annual contributions"""
    balance = current_balance
    annual_rate = rate / 100
    
    for _ in range(years):
        balance = balance * (1 + annual_rate) + contribution
    return balance

def get_social_security_multiplier(claim_age: int, fra: int) -> float:
    """Calculate Social Security adjustment based on claiming age"""
    if claim_age == 62:
        return 0.70 if fra == 67 else 0.75
    elif claim_age == 65:
        return 0.867 if fra == 67 else 0.933
    elif claim_age == fra:
        return 1.0
    elif claim_age == 70:
        years_delayed = 70 - fra
        return 1.0 + (years_delayed * 0.08)
    return 1.0

def get_pension_multiplier(retirement_age: int) -> float:
    """Calculate pension adjustment based on retirement age"""
    if retirement_age == 62:
        return 0.80
    elif retirement_age == 65:
        return 0.93
    elif retirement_age >= 67:
        return 1.0
    return 1.0

def calculate_rmd(balance: float, age: int) -> float:
    """Calculate Required Minimum Distribution"""
    if age < 73:
        return 0
    divisor = RMD_TABLE.get(age, 20.2)
    return balance / divisor

def calculate_medicare_costs(age: int, gross_income: float) -> float:
    """Calculate Medicare and healthcare costs"""
    if age < 65:
        return 0
    
    part_b = 174.70 * 12
    
    if gross_income > 500000:
        part_b += 419.30 * 12
    elif gross_income > 395000:
        part_b += 349.90 * 12
    elif gross_income > 296000:
        part_b += 280.50 * 12
    elif gross_income > 197000:
        part_b += 209.90 * 12
    elif gross_income > 103000:
        part_b += 69.90 * 12
    
    part_d = 55 * 12
    out_of_pocket = 2000
    
    return part_b + part_d + out_of_pocket

def get_standard_deduction(age: int) -> float:
    """Get standard deduction for single filer"""
    standard_deduction = 14600
    if age >= 65:
        standard_deduction += 1950
    return standard_deduction

def calculate_taxes(withdrawal_401k: float, withdrawal_trad_ira: float,
                   withdrawal_taxable: float, pension_income: float,
                   ss_income: float, age: int, federal_rate: float,
                   state_rate: float) -> Dict[str, float]:
    """Calculate taxes on retirement income"""
    federal = federal_rate / 100
    state = state_rate / 100
    
    total_withdrawals = withdrawal_401k + withdrawal_trad_ira
    taxable_gains = withdrawal_taxable * 0.5 * 0.15
    
    combined_income = total_withdrawals + pension_income + (ss_income * 0.5) + (withdrawal_taxable * 0.5)
    
    if combined_income > 34000:
        ss_taxable_percent = 0.85
    elif combined_income > 25000:
        ss_taxable_percent = 0.50
    else:
        ss_taxable_percent = 0
    
    taxable_ss = ss_income * ss_taxable_percent
    total_taxable_income = total_withdrawals + pension_income + taxable_ss
    
    standard_deduction = get_standard_deduction(age)
    adjusted_gross_income = max(0, total_taxable_income - standard_deduction)
    
    federal_tax = adjusted_gross_income * federal
    state_tax = adjusted_gross_income * state
    total_tax = federal_tax + state_tax + taxable_gains
    
    return {
        'standard_deduction': standard_deduction,
        'adjusted_gross_income': adjusted_gross_income,
        'total_tax': total_tax,
        'capital_gains_tax': taxable_gains,
        'effective_rate': total_tax / (total_withdrawals + withdrawal_taxable + pension_income + ss_income) if (total_withdrawals + withdrawal_taxable + pension_income + ss_income) > 0 else 0
    }

def calculate_needed_withdrawal(annual_expenses: float, pension_annual: float, 
                               ss_annual: float, age: int, federal_rate: float,
                               state_rate: float, include_medicare: bool,
                               total_balance: float) -> Tuple[float, float, float]:
    """
    Calculate exactly how much needs to be withdrawn to cover expenses.
    Returns: (withdrawal_needed, medicare_costs, taxes)
    """
    # Calculate Medicare costs with initial estimate
    medicare_costs = 0
    if include_medicare and age >= 65:
        estimated_gross = pension_annual + ss_annual + annual_expenses
        medicare_costs = calculate_medicare_costs(age, estimated_gross)
    
    # Guaranteed income
    guaranteed = pension_annual + ss_annual
    
    # Gap to cover (expenses + medicare - guaranteed income)
    gap = annual_expenses + medicare_costs - guaranteed
    
    if gap <= 0:
        # Guaranteed income covers everything! But check RMD
        rmd = calculate_rmd(total_balance, age)
        if rmd > 0:
            # Recalculate medicare with RMD income
            if include_medicare and age >= 65:
                actual_gross = rmd + pension_annual + ss_annual
                medicare_costs = calculate_medicare_costs(age, actual_gross)
            # Calculate taxes on RMD
            withdrawal_401k = rmd * 0.6
            withdrawal_trad_ira = rmd * 0.2
            withdrawal_taxable = rmd * 0.2
            taxes = calculate_taxes(
                withdrawal_401k, withdrawal_trad_ira, withdrawal_taxable,
                pension_annual, ss_annual,
                age, federal_rate, state_rate
            )
            return rmd, medicare_costs, taxes['total_tax']
        return 0, medicare_costs, 0
    
    # Iterative calculation (taxes depend on withdrawal amount)
    estimated_withdrawal = gap
    
    for iteration in range(10):  # Converge on correct amount
        # Proportional split across accounts
        withdrawal_401k = estimated_withdrawal * 0.6
        withdrawal_trad_ira = estimated_withdrawal * 0.2
        withdrawal_taxable = estimated_withdrawal * 0.2
        
        # Calculate taxes
        taxes = calculate_taxes(
            withdrawal_401k, withdrawal_trad_ira, withdrawal_taxable,
            pension_annual, ss_annual,
            age, federal_rate, state_rate
        )
        
        # Total need = gap + taxes
        total_need = gap + taxes['total_tax']
        
        # Check convergence
        if abs(total_need - estimated_withdrawal) < 50:
            break
        
        estimated_withdrawal = total_need
    
    # Check RMD requirement
    rmd = calculate_rmd(total_balance, age)
    final_withdrawal = max(estimated_withdrawal, rmd)
    
    # Recalculate with final withdrawal amount
    withdrawal_401k = final_withdrawal * 0.6
    withdrawal_trad_ira = final_withdrawal * 0.2
    withdrawal_taxable = final_withdrawal * 0.2
    
    final_taxes = calculate_taxes(
        withdrawal_401k, withdrawal_trad_ira, withdrawal_taxable,
        pension_annual, ss_annual,
        age, federal_rate, state_rate
    )
    
    # Recalculate Medicare with actual income
    if include_medicare and age >= 65:
        actual_gross = final_withdrawal + pension_annual + ss_annual
        medicare_costs = calculate_medicare_costs(age, actual_gross)
    
    return final_withdrawal, medicare_costs, final_taxes['total_tax']

def calculate_retirement_expenses(current_monthly_expenses: float, 
                                 retirement_age: int, current_age: int,
                                 expense_percentage: float, inflation_rate: float) -> float:
    """Calculate inflation-adjusted retirement expenses"""
    years_until_retirement = retirement_age - current_age
    inflation = inflation_rate / 100
    
    expenses_at_retirement = current_monthly_expenses * ((1 + inflation) ** years_until_retirement)
    adjusted_expenses = expenses_at_retirement * (expense_percentage / 100)
    
    return adjusted_expenses

def calculate_home_value(current_value: float, years: int, appreciation_rate: float) -> float:
    """Calculate home value at retirement"""
    if current_value == 0:
        return 0
    annual_rate = appreciation_rate / 100
    future_value = current_value * ((1 + annual_rate) ** years)
    return future_value

def generate_amortization_schedule(starting_401k: float, starting_trad_ira: float,
                                  starting_roth_ira: float, starting_taxable: float,
                                  return_rate: float, pension_income: float, ss_income: float,
                                  retirement_age: int, federal_rate: float,
                                  state_rate: float, inflation_rate: float,
                                  include_medicare: bool, monthly_expenses: float,
                                  years: int = 18) -> List[Dict]:
    """Generate year-by-year schedule with needs-based withdrawals"""
    schedule = []
    
    balance_401k = starting_401k
    balance_trad_ira = starting_trad_ira
    balance_roth_ira = starting_roth_ira
    balance_taxable = starting_taxable
    
    annual_return = return_rate / 100
    inflation = inflation_rate / 100
    
    adjusted_pension = pension_income * 12
    adjusted_ss = ss_income * 12
    annual_expenses = monthly_expenses * 12
    
    for year in range(1, years + 1):
        total_balance = balance_401k + balance_trad_ira + balance_roth_ira + balance_taxable
        
        if total_balance <= 0:
            break
            
        current_age = retirement_age + year - 1
        
        # Beginning balances
        total_begin = total_balance
        
        # Calculate investment growth
        growth_401k = balance_401k * annual_return
        growth_trad_ira = balance_trad_ira * annual_return
        growth_roth_ira = balance_roth_ira * annual_return
        growth_taxable = balance_taxable * annual_return
        total_growth = growth_401k + growth_trad_ira + growth_roth_ira + growth_taxable
        
        # Calculate needed withdrawal
        needed_withdrawal, medicare_costs, taxes = calculate_needed_withdrawal(
            annual_expenses,
            adjusted_pension,
            adjusted_ss,
            current_age,
            federal_rate,
            state_rate,
            include_medicare,
            total_balance
        )
        
        # Calculate 4% rule for comparison
        four_percent_withdrawal = total_balance * 0.04
        
        # Split withdrawal proportionally
        if total_balance > 0:
            pct_401k = balance_401k / total_balance
            pct_trad_ira = balance_trad_ira / total_balance
            pct_roth = balance_roth_ira / total_balance
            pct_taxable = balance_taxable / total_balance
            
            withdrawal_401k = needed_withdrawal * pct_401k
            withdrawal_trad_ira = needed_withdrawal * pct_trad_ira
            withdrawal_roth = needed_withdrawal * pct_roth
            withdrawal_taxable_acct = needed_withdrawal * pct_taxable
        else:
            withdrawal_401k = withdrawal_trad_ira = withdrawal_roth = withdrawal_taxable_acct = 0
        
        # Cap withdrawals at available balance + growth
        withdrawal_401k = min(withdrawal_401k, balance_401k + growth_401k)
        withdrawal_trad_ira = min(withdrawal_trad_ira, balance_trad_ira + growth_trad_ira)
        withdrawal_roth = min(withdrawal_roth, balance_roth_ira + growth_roth_ira)
        withdrawal_taxable_acct = min(withdrawal_taxable_acct, balance_taxable + growth_taxable)
        
        total_withdrawal = withdrawal_401k + withdrawal_trad_ira + withdrawal_roth + withdrawal_taxable_acct
        
        # Calculate ending balances
        end_401k = max(0, balance_401k + growth_401k - withdrawal_401k)
        end_trad_ira = max(0, balance_trad_ira + growth_trad_ira - withdrawal_trad_ira)
        end_roth_ira = max(0, balance_roth_ira + growth_roth_ira - withdrawal_roth)
        end_taxable = max(0, balance_taxable + growth_taxable - withdrawal_taxable_acct)
        total_end = end_401k + end_trad_ira + end_roth_ira + end_taxable
        
        # Calculate income
        gross_income = total_withdrawal + adjusted_pension + adjusted_ss
        net_income = gross_income - taxes - medicare_costs
        surplus_shortfall = net_income - annual_expenses
        
        # Check RMD
        rmd_required = calculate_rmd(total_balance, current_age)
        
        # Calculate savings vs 4% rule
        savings_vs_4pct = four_percent_withdrawal - needed_withdrawal
        
        schedule.append({
            'Year': year,
            'Age': current_age,
            'Total Start': total_begin,
            'Total Growth': total_growth,
            'Needed Withdrawal': needed_withdrawal,
            '4% Would Be': four_percent_withdrawal,
            'Savings vs 4%': savings_vs_4pct,
            'RMD Required': 'Yes' if rmd_required > 0 else 'No',
            'Pension': adjusted_pension,
            'Social Security': adjusted_ss,
            'Gross Income': gross_income,
            'Taxes': taxes,
            'Medicare': medicare_costs,
            'Net Income': net_income,
            'Annual Expenses': annual_expenses,
            'Surplus/Shortfall': surplus_shortfall,
            'Total End': total_end
        })
        
        # Update balances
        balance_401k = end_401k
        balance_trad_ira = end_trad_ira
        balance_roth_ira = end_roth_ira
        balance_taxable = end_taxable
        
        # Adjust for inflation
        adjusted_pension *= (1 + inflation)
        adjusted_ss *= (1 + inflation)
        annual_expenses *= (1 + inflation)
    
    return schedule

def calculate_projection(current_age: int, 
                        current_401k: float, annual_401k_contribution: float,
                        current_trad_ira: float, annual_trad_ira_contribution: float,
                        current_roth_ira: float, annual_roth_ira_contribution: float,
                        current_taxable: float, annual_taxable_contribution: float,
                        return_rate: float, pension_full: float, ss_full: float,
                        full_retirement_age: int, federal_tax: float, state_tax: float,
                        inflation_rate: float, include_medicare: bool,
                        current_monthly_expenses: float, retirement_expense_pct: float,
                        current_home_value: float,
                        retirement_age: int) -> Dict:
    """Calculate projection for a specific retirement age"""
    years_until_retirement = retirement_age - current_age
    
    if years_until_retirement <= 0:
        return None
    
    # Project account growth
    projected_401k = calculate_account_growth(current_401k, years_until_retirement, annual_401k_contribution, return_rate)
    projected_trad_ira = calculate_account_growth(current_trad_ira, years_until_retirement, annual_trad_ira_contribution, return_rate)
    projected_roth_ira = calculate_account_growth(current_roth_ira, years_until_retirement, annual_roth_ira_contribution, return_rate)
    projected_taxable = calculate_account_growth(current_taxable, years_until_retirement, annual_taxable_contribution, return_rate)
    
    projected_home_value = calculate_home_value(current_home_value, years_until_retirement, inflation_rate)
    
    monthly_retirement_expenses = calculate_retirement_expenses(
        current_monthly_expenses, retirement_age, current_age, 
        retirement_expense_pct, inflation_rate
    )
    
    total_retirement_assets = projected_401k + projected_trad_ira + projected_roth_ira + projected_taxable
    total_net_worth = total_retirement_assets + projected_home_value
    
    ss_multiplier = get_social_security_multiplier(retirement_age, full_retirement_age)
    pension_multiplier = get_pension_multiplier(retirement_age)
    
    adjusted_ss = ss_full * ss_multiplier
    adjusted_pension = pension_full * pension_multiplier
    
    # Calculate needed withdrawal
    annual_expenses = monthly_retirement_expenses * 12
    needed_withdrawal, medicare_costs, taxes = calculate_needed_withdrawal(
        annual_expenses,
        adjusted_pension * 12,
        adjusted_ss * 12,
        retirement_age,
        federal_tax,
        state_tax,
        include_medicare,
        total_retirement_assets
    )
    
    # Calculate 4% rule for comparison
    four_percent_withdrawal = total_retirement_assets * 0.04
    savings_vs_4pct = four_percent_withdrawal - needed_withdrawal
    
    total_annual_income = needed_withdrawal + (adjusted_pension * 12) + (adjusted_ss * 12)
    net_annual_income = total_annual_income - taxes - medicare_costs
    net_monthly_income = net_annual_income / 12
    
    expense_coverage_ratio = (net_annual_income / annual_expenses * 100) if annual_expenses > 0 else 0
    monthly_surplus_shortfall = net_monthly_income - monthly_retirement_expenses
    
    target_age = 80
    years_to_project = min(target_age - retirement_age, 30)
    
    amortization = generate_amortization_schedule(
        projected_401k, projected_trad_ira, projected_roth_ira, projected_taxable,
        return_rate, adjusted_pension, adjusted_ss,
        retirement_age, federal_tax, state_tax, inflation_rate,
        include_medicare, monthly_retirement_expenses, years_to_project
    )
    
    return {
        'age': retirement_age,
        'projected_401k': projected_401k,
        'projected_trad_ira': projected_trad_ira,
        'projected_roth_ira': projected_roth_ira,
        'projected_taxable': projected_taxable,
        'total_retirement_assets': total_retirement_assets,
        'projected_home_value': projected_home_value,
        'total_net_worth': total_net_worth,
        'pension': adjusted_pension,
        'pension_multiplier': pension_multiplier,
        'social_security': adjusted_ss,
        'ss_multiplier': ss_multiplier,
        'needed_withdrawal': needed_withdrawal,
        'four_percent_withdrawal': four_percent_withdrawal,
        'savings_vs_4pct': savings_vs_4pct,
        'total_annual_income': total_annual_income,
        'taxes': taxes,
        'medicare_costs': medicare_costs,
        'net_annual_income': net_annual_income,
        'net_monthly_income': net_monthly_income,
        'monthly_retirement_expenses': monthly_retirement_expenses,
        'annual_expenses': annual_expenses,
        'expense_coverage_ratio': expense_coverage_ratio,
        'monthly_surplus_shortfall': monthly_surplus_shortfall,
        'years_until_retirement': years_until_retirement,
        'amortization': amortization
    }

def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.0f}"

def reset_inputs():
    """Reset to defaults - 35-year-old professional"""
    st.session_state.current_age = 35
    st.session_state.current_401k = 75000.0
    st.session_state.annual_401k_contribution = 15000.0
    st.session_state.current_trad_ira = 15000.0
    st.session_state.annual_trad_ira_contribution = 6500.0
    st.session_state.current_roth_ira = 25000.0
    st.session_state.annual_roth_ira_contribution = 6500.0
    st.session_state.current_taxable = 20000.0
    st.session_state.annual_taxable_contribution = 5000.0
    st.session_state.return_rate = 7.0
    st.session_state.full_retirement_age = 67
    st.session_state.pension_full = 1500.0
    st.session_state.ss_full = 2200.0
    st.session_state.federal_tax = 22
    st.session_state.state_tax = 5.0
    st.session_state.inflation_rate = 3.0
    st.session_state.include_medicare = True
    st.session_state.current_monthly_expenses = 4500.0
    st.session_state.retirement_expense_pct = 80.0
    st.session_state.current_home_value = 350000.0

def initialize_defaults():
    """Initialize default values if not already set"""
    if 'current_age' not in st.session_state:
        reset_inputs()

def main():
    """Main Streamlit app"""
    st.set_page_config(page_title="Retirement Calculator", page_icon="💰", layout="wide")
    
    initialize_defaults()
    
    st.title("💰 Comprehensive US Retirement Calculator")
    st.markdown("""
    **Smart Withdrawal Strategy:** Calculates exactly how much you need to withdraw (not arbitrary 4% rule) to cover expenses, taxes, and Medicare.
    Includes 401(k), IRAs, taxable accounts (stocks, bonds, gold), home value, and year-by-year breakdown to age 80.
    
    **Default: 35-year-old professional** | [Click "Clear All Values" to reset]
    """)
    
    # Sidebar
    st.sidebar.header("📝 Your Information")
    
    if st.sidebar.button("🔄 Clear All Values", use_container_width=True):
        reset_inputs()
        st.rerun()
    
    with st.sidebar:
        st.subheader("Basic Information")
        current_age = st.number_input("Current Age", min_value=18, max_value=70, 
                                     step=1, key='current_age')
        
        st.subheader("401(k) Account")
        current_401k = st.number_input("Current 401(k) Balance ($)", min_value=0.0, 
                                      step=10000.0, key='current_401k')
        annual_401k_contribution = st.number_input("Annual 401(k) Contribution ($)", min_value=0.0, 
                                                  step=1000.0, key='annual_401k_contribution')
        
        st.subheader("Traditional IRA")
        current_trad_ira = st.number_input("Current Traditional IRA Balance ($)", min_value=0.0, 
                                          step=5000.0, key='current_trad_ira')
        annual_trad_ira_contribution = st.number_input("Annual Traditional IRA Contribution ($)", min_value=0.0, 
                                                       step=500.0, key='annual_trad_ira_contribution')
        
        st.subheader("Roth IRA")
        current_roth_ira = st.number_input("Current Roth IRA Balance ($)", min_value=0.0, 
                                          step=5000.0, key='current_roth_ira')
        annual_roth_ira_contribution = st.number_input("Annual Roth IRA Contribution ($)", min_value=0.0, 
                                                       step=500.0, key='annual_roth_ira_contribution')
        
        st.subheader("Taxable Investments (Stocks, Bonds, Gold, etc.)")
        current_taxable = st.number_input("Current Taxable Account Balance ($)", min_value=0.0, 
                                         step=5000.0, key='current_taxable',
                                         help="Brokerage accounts, stocks, bonds, gold, ETFs")
        annual_taxable_contribution = st.number_input("Annual Taxable Contribution ($)", min_value=0.0, 
                                                      step=500.0, key='annual_taxable_contribution')
        
        return_rate = st.slider("Expected Annual Return Rate (%)", min_value=0.0, max_value=15.0, 
                               step=0.5, key='return_rate')
        
        st.subheader("💵 Living Expenses")
        current_monthly_expenses = st.number_input(
            "Current Monthly Expenses ($)", 
            min_value=0.0, 
            step=500.0, 
            key='current_monthly_expenses',
            help="Your current monthly spending"
        )
        
        retirement_expense_pct = st.slider(
            "Expected Expenses in Retirement (%)", 
            min_value=50, 
            max_value=150, 
            step=5,
            key='retirement_expense_pct',
            help="Typically 70-90%"
        )
        
        st.subheader("🏠 Home & Assets")
        current_home_value = st.number_input(
            "Current Home Value ($)", 
            min_value=0.0, 
            step=50000.0,
            key='current_home_value'
        )
        
        st.subheader("Retirement Benefits")
        full_retirement_age = st.selectbox("Full Retirement Age (FRA)", [66, 67], 
                                          key='full_retirement_age')
        pension_full = st.number_input("Monthly Pension at Full Retirement ($)", min_value=0.0, 
                                      step=100.0, key='pension_full')
        ss_full = st.number_input("Monthly Social Security at FRA ($)", min_value=0.0, 
                                 step=100.0, key='ss_full')
        
        st.subheader("Tax Information")
        federal_tax = st.selectbox(
            "Federal Marginal Tax Rate (%)",
            [10, 12, 22, 24, 32, 35, 37],
            key='federal_tax'
        )
        state_tax = st.slider("State Tax Rate (%)", min_value=0.0, max_value=15.0, 
                             step=0.5, key='state_tax')
        
        st.subheader("Planning Assumptions")
        inflation_rate = st.slider("Expected Inflation Rate (%)", min_value=0.0, max_value=10.0, 
                                  step=0.5, key='inflation_rate')
        include_medicare = st.checkbox("Include Medicare & Healthcare Costs", 
                                      key='include_medicare')
    
    # Main content
    if current_age >= 62:
        st.error("⚠️ You must be younger than 62 to see retirement projections.")
        return
    
    # Current summary
    current_total_retirement = current_401k + current_trad_ira + current_roth_ira + current_taxable
    current_total_net_worth = current_total_retirement + current_home_value
    
    st.header("📊 Current Financial Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("401(k)", format_currency(current_401k))
    with col2:
        st.metric("Traditional IRA", format_currency(current_trad_ira))
    with col3:
        st.metric("Roth IRA", format_currency(current_roth_ira))
    with col4:
        st.metric("Taxable", format_currency(current_taxable))
    with col5:
        st.metric("**Total Retirement**", format_currency(current_total_retirement))
    
    if current_home_value > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🏠 Home Value", format_currency(current_home_value))
        with col2:
            st.metric("💎 **Complete Net Worth**", format_currency(current_total_net_worth))
    
    if current_monthly_expenses > 0:
        st.subheader("💵 Current Monthly Expenses")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Monthly Spending", format_currency(current_monthly_expenses))
        with col2:
            st.metric("Annual Spending", format_currency(current_monthly_expenses * 12))
    
    st.markdown("---")
    
    # Calculate projections
    retirement_ages = [62, 65, 67, 70]
    projections = []
    
    for age in retirement_ages:
        if age > current_age:
            proj = calculate_projection(
                current_age, 
                current_401k, annual_401k_contribution,
                current_trad_ira, annual_trad_ira_contribution,
                current_roth_ira, annual_roth_ira_contribution,
                current_taxable, annual_taxable_contribution,
                return_rate, pension_full, ss_full, 
                full_retirement_age, federal_tax, state_tax,
                inflation_rate, include_medicare,
                current_monthly_expenses, retirement_expense_pct,
                current_home_value, age
            )
            if proj:
                projections.append(proj)
    
    # Display summary comparison
    st.header("📈 Needs-Based Withdrawal Analysis")
    
    st.info("""
    **What's Different:** This calculator determines exactly how much you need to withdraw to cover 
    expenses, taxes, and Medicare—not an arbitrary 4% rule. This preserves your assets longer!
    """)
    
    # Comparison table
    comparison_data = []
    for proj in projections:
        row = {
            'Age': proj['age'],
            'Retirement Assets': format_currency(proj['total_retirement_assets']),
            'Needed Withdrawal': format_currency(proj['needed_withdrawal']),
            '4% Rule': format_currency(proj['four_percent_withdrawal']),
            'Savings vs 4%': format_currency(proj['savings_vs_4pct'])
        }
        
        if current_home_value > 0:
            row['Net Worth'] = format_currency(proj['total_net_worth'])
        
        if current_monthly_expenses > 0:
            row['Coverage'] = f"{proj['expense_coverage_ratio']:.0f}%"
        
        comparison_data.append(row)
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Detailed tabs
    st.header("💵 Detailed Projections")
    
    tabs = st.tabs([f"Age {proj['age']}" for proj in projections])
    
    for tab, proj in zip(tabs, projections):
        with tab:
            # 4% vs Needs-Based comparison
            st.subheader("💰 Withdrawal Strategy Comparison")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("4% Rule Withdrawal", format_currency(proj['four_percent_withdrawal']))
                st.caption("Traditional approach")
            
            with col2:
                st.metric("Needs-Based Withdrawal", format_currency(proj['needed_withdrawal']))
                st.caption("What you actually need")
            
            with col3:
                if proj['savings_vs_4pct'] > 0:
                    st.metric("Annual Savings", format_currency(proj['savings_vs_4pct']),
                             delta="✅ Preserves assets", delta_color="normal")
                    st.caption(f"Over 18 years: {format_currency(proj['savings_vs_4pct'] * 18)}")
                else:
                    st.metric("Additional Need", format_currency(abs(proj['savings_vs_4pct'])),
                             delta="⚠️ Need more than 4%", delta_color="inverse")
            
            st.markdown("---")
            
            # Asset breakdown
            st.subheader("💼 Projected Assets at Retirement")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("401(k)", format_currency(proj['projected_401k']))
            with col2:
                st.metric("Traditional IRA", format_currency(proj['projected_trad_ira']))
            with col3:
                st.metric("Roth IRA", format_currency(proj['projected_roth_ira']))
            with col4:
                st.metric("Taxable", format_currency(proj['projected_taxable']))
            with col5:
                st.metric("**TOTAL**", format_currency(proj['total_retirement_assets']))
            
            if current_home_value > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏠 Home Value", format_currency(proj['projected_home_value']))
                with col2:
                    st.metric("💎 **Net Worth**", format_currency(proj['total_net_worth']))
            
            st.markdown("---")
            
            # Expense coverage
            if current_monthly_expenses > 0:
                st.subheader("💵 Income & Expense Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Net Monthly Income", format_currency(proj['net_monthly_income']))
                
                with col2:
                    st.metric("Monthly Expenses", format_currency(proj['monthly_retirement_expenses']))
                
                with col3:
                    if proj['monthly_surplus_shortfall'] >= 0:
                        st.metric("Monthly Surplus", format_currency(proj['monthly_surplus_shortfall']),
                                 delta="✅ Covered", delta_color="normal")
                    else:
                        st.metric("Monthly Shortfall", format_currency(abs(proj['monthly_surplus_shortfall'])),
                                 delta="⚠️ Deficit", delta_color="inverse")
                
                # Add detailed breakdown explanation
                with st.expander("📊 Click to see detailed income & expense breakdown"):
                    st.markdown(f"""
                    ### 💰 How Your Money Flows
                    
                    #### **INCOME SOURCES (What Comes In):**
                    
                    **Retirement Account Withdrawals (Needs-Based):**
                    - Total Needed from Savings: {format_currency(proj['needed_withdrawal'])}/year
                    - For Comparison, 4% Rule Would Be: {format_currency(proj['four_percent_withdrawal'])}/year
                    - **You Save: {format_currency(proj['savings_vs_4pct'])}/year** ✅
                    
                    **Guaranteed Income:**
                    - Pension: {format_currency(proj['pension'] * 12)}/year
                    - Social Security: {format_currency(proj['social_security'] * 12)}/year
                    
                    **Gross Annual Income:** {format_currency(proj['total_annual_income'])} ✅
                    
                    ---
                    
                    #### **DEDUCTIONS (What Comes Out):**
                    
                    **Taxes:**
                    - Federal & State Taxes: {format_currency(proj['taxes'])}/year
                    - Effective Tax Rate: {(proj['taxes']/proj['total_annual_income']*100) if proj['total_annual_income'] > 0 else 0:.1f}%
                    
                    **Healthcare:**
                    - Medicare Costs (Part B + D + Out-of-Pocket): {format_currency(proj['medicare_costs'])}/year
                    - Monthly: {format_currency(proj['medicare_costs']/12)}
                    
                    **Total Deductions:** {format_currency(proj['taxes'] + proj['medicare_costs'])} ❌
                    
                    ---
                    
                    #### **NET INCOME (What You Actually Get):**
                    
                    **Calculation:**
                    ```
                    Gross Income:        {format_currency(proj['total_annual_income'])}
                    - Taxes:             {format_currency(proj['taxes'])}
                    - Medicare:          {format_currency(proj['medicare_costs'])}
                    ═══════════════════════════════════
                    Net Annual Income:   {format_currency(proj['net_annual_income'])} ✅
                    Net Monthly Income:  {format_currency(proj['net_monthly_income'])}
                    ```
                    
                    ---
                    
                    #### **EXPENSES (What You Need to Spend):**
                    
                    **Your Living Expenses:**
                    - Original Monthly Expenses: {format_currency(current_monthly_expenses)}
                    - Inflated to Retirement Age: {format_currency(proj['monthly_retirement_expenses']/(retirement_expense_pct/100))}
                    - Adjusted for Retirement ({retirement_expense_pct:.0f}%): {format_currency(proj['monthly_retirement_expenses'])}
                    
                    **Annual Expenses:** {format_currency(proj['annual_expenses'])}
                    
                    *Note: This includes housing, food, transportation, entertainment, etc. 
                    Medicare is already deducted from income above.*
                    
                    ---
                    
                    #### **SURPLUS OR SHORTFALL:**
                    
                    **The Bottom Line:**
                    ```
                    Net Annual Income:   {format_currency(proj['net_annual_income'])}
                    - Living Expenses:   {format_currency(proj['annual_expenses'])}
                    ═══════════════════════════════════
                    Annual Result:       {format_currency(proj['monthly_surplus_shortfall'] * 12)}
                    Monthly Result:      {format_currency(proj['monthly_surplus_shortfall'])}
                    ```
                    
                    **Coverage Ratio:** {proj['expense_coverage_ratio']:.0f}%
                    - Above 100% = ✅ Income covers all expenses
                    - Below 100% = ⚠️ Expenses exceed income
                    
                    {'✅ **You have enough income to cover all expenses!**' if proj['monthly_surplus_shortfall'] >= 0 else '⚠️ **Warning: Your expenses exceed your income. Consider adjusting your plan.**'}
                    
                    ---
                    
                    #### **WHY NEEDS-BASED IS BETTER:**
                    
                    **Traditional 4% Rule:**
                    - Would withdraw: {format_currency(proj['four_percent_withdrawal'])}/year
                    - Regardless of actual need
                    - Higher taxes, higher Medicare costs
                    
                    **Needs-Based Approach:**
                    - Withdraws only: {format_currency(proj['needed_withdrawal'])}/year
                    - Covers exact expenses + taxes + Medicare
                    - **Saves: {format_currency(proj['savings_vs_4pct'])}/year**
                    - **Over 18 years: {format_currency(proj['savings_vs_4pct'] * 18)}** stays invested! 🎉
                    """)
                
                st.markdown("---")
            
            # Year-by-year schedule
            st.subheader(f"📅 Year-by-Year Schedule (Age {proj['age']} to 80)")
            
            if proj['amortization']:
                amort_df = pd.DataFrame(proj['amortization'])
                
                # Summary
                total_needed = amort_df['Needed Withdrawal'].sum()
                total_4pct = amort_df['4% Would Be'].sum()
                total_savings = total_4pct - total_needed
                final_balance = amort_df.iloc[-1]['Total End']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Needed", format_currency(total_needed))
                with col2:
                    st.metric("4% Total", format_currency(total_4pct))
                with col3:
                    st.metric("Total Savings", format_currency(total_savings),
                             delta="✅ vs 4% rule")
                with col4:
                    st.metric("Balance at 80", format_currency(final_balance))
                
                # Table
                display_columns = ['Year', 'Age', 'Total Start', 'Needed Withdrawal', 
                                  '4% Would Be', 'Savings vs 4%', 'RMD Required', 
                                  'Net Income', 'Annual Expenses', 'Surplus/Shortfall', 'Total End']
                
                display_df = amort_df[display_columns].copy()
                
                for col in ['Total Start', 'Needed Withdrawal', '4% Would Be', 'Savings vs 4%', 
                           'Net Income', 'Annual Expenses', 'Surplus/Shortfall', 'Total End']:
                    display_df[col] = display_df[col].apply(lambda x: format_currency(x))
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Download
                csv = amort_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Schedule as CSV",
                    data=csv,
                    file_name=f"retirement_needs_based_age_{proj['age']}.csv",
                    mime="text/csv"
                )
    
    # Info box
    st.header("ℹ️ Understanding Needs-Based Withdrawals")
    
    with st.expander("❓ What's the difference between 4% Rule and Needs-Based?"):
        st.markdown("""
        ### 4% Rule (Traditional):
        - Withdraw 4% of starting balance every year
        - Adjust for inflation
        - **Doesn't consider your actual needs**
        - May withdraw too much or too little
        
        ### Needs-Based (This Calculator):
        - Calculate exactly what you need:
          - Annual expenses
          - Plus Medicare costs
          - Plus taxes on withdrawals
          - Minus pension
          - Minus Social Security
        - **Only withdraw what you actually need**
        - At age 73+, withdraws RMD if higher than need
        
        ### Example:
        ```
        Assets: $2,000,000
        Expenses: $60,000/year
        Pension: $18,000/year
        Social Security: $24,000/year
        
        4% Rule:
        Withdraw $80,000/year (regardless of need)
        
        Needs-Based:
        Need: $60,000 (expenses)
        Have: $42,000 (pension + SS)
        Gap: $18,000
        Add: $3,000 (taxes) + $5,000 (medicare)
        Total: $26,000/year
        
        SAVINGS: $54,000/year stays invested!
        Over 18 years: $972,000 preserved!
        ```
        
        ### Benefits:
        ✅ Lower taxes (smaller withdrawals = lower tax brackets)
        ✅ Lower Medicare costs (lower income = lower IRMAA)
        ✅ Assets last longer
        ✅ Larger legacy for heirs
        ✅ More buffer for emergencies
        """)

if __name__ == "__main__":
    main()

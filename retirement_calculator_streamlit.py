#!/usr/bin/env python3
"""
Comprehensive Retirement Calculator - Enhanced Version
Web-based retirement planning with 401k, IRAs, other assets, taxes, Medicare, inflation, and RMDs
"""

import streamlit as st
import pandas as pd
from typing import Dict, List


# RMD Table (IRS Uniform Lifetime Table)
RMD_TABLE = {
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1,
    80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1,
    94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4
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
    
    divisor = RMD_TABLE.get(age, RMD_TABLE[100])
    return balance / divisor


def calculate_medicare_costs(age: int, gross_income: float) -> float:
    """Calculate Medicare and healthcare costs"""
    if age < 65:
        return 0
    
    # 2025 Medicare Part B base premium
    part_b = 174.70 * 12
    
    # IRMAA surcharges based on income
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
    
    # Part D prescription drug coverage
    part_d = 55 * 12
    
    # Estimated out-of-pocket costs
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
    
    # All withdrawals from tax-deferred accounts are taxable
    total_withdrawals = withdrawal_401k + withdrawal_trad_ira
    
    # Taxable account: only gains are taxed (assume 50% cost basis)
    taxable_gains = withdrawal_taxable * 0.5 * 0.15  # 15% capital gains rate
    
    # Calculate Social Security taxable portion
    combined_income = total_withdrawals + pension_income + (ss_income * 0.5) + (withdrawal_taxable * 0.5)
    
    if combined_income > 34000:
        ss_taxable_percent = 0.85
    elif combined_income > 25000:
        ss_taxable_percent = 0.50
    else:
        ss_taxable_percent = 0
    
    taxable_ss = ss_income * ss_taxable_percent
    total_taxable_income = total_withdrawals + pension_income + taxable_ss
    
    # Apply standard deduction
    standard_deduction = get_standard_deduction(age)
    adjusted_gross_income = max(0, total_taxable_income - standard_deduction)
    
    # Calculate taxes
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


def calculate_projection(current_age: int, 
                        current_401k: float, annual_401k_contribution: float,
                        current_trad_ira: float, annual_trad_ira_contribution: float,
                        current_roth_ira: float, annual_roth_ira_contribution: float,
                        current_taxable: float, annual_taxable_contribution: float,
                        return_rate: float, pension_full: float, ss_full: float,
                        full_retirement_age: int, federal_tax: float, state_tax: float,
                        inflation_rate: float, life_expectancy: int, include_medicare: bool,
                        retirement_age: int) -> Dict:
    """Calculate projection for a specific retirement age"""
    years_until_retirement = retirement_age - current_age
    
    if years_until_retirement <= 0:
        return None
    
    # Project all accounts growth
    projected_401k = calculate_account_growth(
        current_401k, years_until_retirement, annual_401k_contribution, return_rate
    )
    
    projected_trad_ira = calculate_account_growth(
        current_trad_ira, years_until_retirement, annual_trad_ira_contribution, return_rate
    )
    
    projected_roth_ira = calculate_account_growth(
        current_roth_ira, years_until_retirement, annual_roth_ira_contribution, return_rate
    )
    
    projected_taxable = calculate_account_growth(
        current_taxable, years_until_retirement, annual_taxable_contribution, return_rate
    )
    
    # Calculate total assets
    total_assets = projected_401k + projected_trad_ira + projected_roth_ira + projected_taxable
    
    # Calculate adjusted amounts
    ss_multiplier = get_social_security_multiplier(retirement_age, full_retirement_age)
    pension_multiplier = get_pension_multiplier(retirement_age)
    
    adjusted_ss = ss_full * ss_multiplier
    adjusted_pension = pension_full * pension_multiplier
    
    # Calculate 4% rule on total tax-deferred assets (401k + Trad IRA)
    taxable_assets = projected_401k + projected_trad_ira
    four_percent_401k = taxable_assets * 0.04 / 12
    
    # Roth IRA withdrawals (tax-free)
    four_percent_roth = projected_roth_ira * 0.04 / 12
    
    # Taxable account withdrawals
    four_percent_taxable = projected_taxable * 0.04 / 12
    
    total_monthly_income = four_percent_401k + four_percent_roth + four_percent_taxable + adjusted_pension + adjusted_ss
    total_annual_income = total_monthly_income * 12
    
    # Calculate taxes (Roth withdrawals are tax-free)
    annual_taxable_withdrawal = taxable_assets * 0.04
    annual_taxable_account = projected_taxable * 0.04
    annual_pension = adjusted_pension * 12
    annual_ss = adjusted_ss * 12
    
    taxes = calculate_taxes(
        annual_taxable_withdrawal * 0.6,  # Assume 60% from 401k
        annual_taxable_withdrawal * 0.4,  # Assume 40% from Trad IRA
        annual_taxable_account,
        annual_pension, 
        annual_ss,
        retirement_age, 
        federal_tax, 
        state_tax
    )
    
    # Calculate Medicare costs
    medicare_costs = 0
    if include_medicare:
        medicare_costs = calculate_medicare_costs(retirement_age, total_annual_income)
    
    net_annual_income = total_annual_income - taxes['total_tax'] - medicare_costs
    net_monthly_income = net_annual_income / 12
    
    return {
        'age': retirement_age,
        'projected_401k': projected_401k,
        'projected_trad_ira': projected_trad_ira,
        'projected_roth_ira': projected_roth_ira,
        'projected_taxable': projected_taxable,
        'total_assets': total_assets,
        'pension': adjusted_pension,
        'pension_multiplier': pension_multiplier,
        'social_security': adjusted_ss,
        'ss_multiplier': ss_multiplier,
        'monthly_income_401k': four_percent_401k,
        'monthly_income_roth': four_percent_roth,
        'monthly_income_taxable': four_percent_taxable,
        'total_monthly_income': total_monthly_income,
        'total_annual_income': total_annual_income,
        'taxes': taxes,
        'medicare_costs': medicare_costs,
        'net_annual_income': net_annual_income,
        'net_monthly_income': net_monthly_income,
        'years_until_retirement': years_until_retirement,
    }


def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.0f}"


def reset_inputs():
    """Reset all input values to defaults"""
    st.session_state['current_age'] = 45
    st.session_state['current_401k'] = 250000.0
    st.session_state['annual_401k_contribution'] = 20000.0
    st.session_state['current_trad_ira'] = 50000.0
    st.session_state['annual_trad_ira_contribution'] = 6500.0
    st.session_state['current_roth_ira'] = 30000.0
    st.session_state['annual_roth_ira_contribution'] = 6500.0
    st.session_state['current_taxable'] = 25000.0
    st.session_state['annual_taxable_contribution'] = 5000.0
    st.session_state['return_rate'] = 7.0
    st.session_state['full_retirement_age'] = 67
    st.session_state['pension_full'] = 2000.0
    st.session_state['ss_full'] = 2500.0
    st.session_state['federal_tax'] = 22
    st.session_state['state_tax'] = 5.0
    st.session_state['inflation_rate'] = 3.0
    st.session_state['life_expectancy'] = 90
    st.session_state['include_medicare'] = True


def main():
    """Main Streamlit app"""
    st.set_page_config(page_title="Retirement Calculator", page_icon="💰", layout="wide")
    
    st.title("💰 Comprehensive Retirement Calculator")
    st.markdown("""
    Calculate your retirement projections including 401(k), IRAs, taxable accounts, pension, Social Security,
    taxes, Medicare, inflation adjustments, and Required Minimum Distributions (RMDs).
    """)
    
    # Sidebar for inputs
    st.sidebar.header("📝 Your Information")
    
    # Clear/Reset button at the top of sidebar
    if st.sidebar.button("🔄 Clear All Values", use_container_width=True):
        reset_inputs()
        st.rerun()
    
    with st.sidebar:
        st.subheader("Basic Information")
        current_age = st.number_input("Current Age", min_value=18, max_value=70, 
                                     value=st.session_state.get('current_age', 45), 
                                     step=1, key='current_age')
        
        st.subheader("401(k) Account")
        current_401k = st.number_input("Current 401(k) Balance ($)", min_value=0.0, 
                                      value=st.session_state.get('current_401k', 250000.0), 
                                      step=10000.0, key='current_401k')
        annual_401k_contribution = st.number_input("Annual 401(k) Contribution ($)", min_value=0.0, 
                                                  value=st.session_state.get('annual_401k_contribution', 20000.0), 
                                                  step=1000.0, key='annual_401k_contribution')
        
        st.subheader("Traditional IRA")
        current_trad_ira = st.number_input("Current Traditional IRA Balance ($)", min_value=0.0, 
                                          value=st.session_state.get('current_trad_ira', 50000.0), 
                                          step=5000.0, key='current_trad_ira')
        annual_trad_ira_contribution = st.number_input("Annual Traditional IRA Contribution ($)", min_value=0.0, 
                                                       value=st.session_state.get('annual_trad_ira_contribution', 6500.0), 
                                                       step=500.0, key='annual_trad_ira_contribution')
        
        st.subheader("Roth IRA")
        current_roth_ira = st.number_input("Current Roth IRA Balance ($)", min_value=0.0, 
                                          value=st.session_state.get('current_roth_ira', 30000.0), 
                                          step=5000.0, key='current_roth_ira')
        annual_roth_ira_contribution = st.number_input("Annual Roth IRA Contribution ($)", min_value=0.0, 
                                                       value=st.session_state.get('annual_roth_ira_contribution', 6500.0), 
                                                       step=500.0, key='annual_roth_ira_contribution')
        
        st.subheader("Taxable Investments")
        current_taxable = st.number_input("Current Taxable Account Balance ($)", min_value=0.0, 
                                         value=st.session_state.get('current_taxable', 25000.0), 
                                         step=5000.0, key='current_taxable')
        annual_taxable_contribution = st.number_input("Annual Taxable Contribution ($)", min_value=0.0, 
                                                      value=st.session_state.get('annual_taxable_contribution', 5000.0), 
                                                      step=500.0, key='annual_taxable_contribution')
        
        return_rate = st.slider("Expected Annual Return Rate (%)", min_value=0.0, max_value=15.0, 
                               value=st.session_state.get('return_rate', 7.0), 
                               step=0.5, key='return_rate')
        
        st.subheader("Retirement Benefits")
        full_retirement_age = st.selectbox("Full Retirement Age (FRA)", [66, 67], 
                                          index=1 if st.session_state.get('full_retirement_age', 67) == 67 else 0,
                                          key='full_retirement_age')
        pension_full = st.number_input("Monthly Pension at Full Retirement ($)", min_value=0.0, 
                                      value=st.session_state.get('pension_full', 2000.0), 
                                      step=100.0, key='pension_full')
        ss_full = st.number_input("Monthly Social Security at FRA ($)", min_value=0.0, 
                                 value=st.session_state.get('ss_full', 2500.0), 
                                 step=100.0, key='ss_full')
        
        st.subheader("Tax Information")
        federal_tax = st.selectbox(
            "Federal Marginal Tax Rate (%)",
            [10, 12, 22, 24, 32, 35, 37],
            index=2 if st.session_state.get('federal_tax', 22) == 22 else 0,
            key='federal_tax'
        )
        state_tax = st.slider("State Tax Rate (%)", min_value=0.0, max_value=15.0, 
                             value=st.session_state.get('state_tax', 5.0), 
                             step=0.5, key='state_tax')
        
        st.subheader("Planning Assumptions")
        inflation_rate = st.slider("Expected Inflation Rate (%)", min_value=0.0, max_value=10.0, 
                                  value=st.session_state.get('inflation_rate', 3.0), 
                                  step=0.5, key='inflation_rate')
        life_expectancy = st.number_input("Life Expectancy", min_value=70, max_value=110, 
                                         value=st.session_state.get('life_expectancy', 90), 
                                         step=1, key='life_expectancy')
        include_medicare = st.checkbox("Include Medicare & Healthcare Costs", 
                                      value=st.session_state.get('include_medicare', True),
                                      key='include_medicare')
    
    # Main content area
    if current_age >= 62:
        st.error("⚠️ You must be younger than 62 to see retirement projections.")
        return
    
    # Calculate current total assets
    current_total_assets = current_401k + current_trad_ira + current_roth_ira + current_taxable
    
    # Display current assets summary
    st.header("📊 Current Assets Summary")
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
        st.metric("**TOTAL ASSETS**", format_currency(current_total_assets))
    
    st.markdown("---")
    
    # Calculate projections for all retirement ages
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
                inflation_rate, life_expectancy, include_medicare, age
            )
            if proj:
                projections.append(proj)
    
    # Display summary comparison
    st.header("📈 Retirement Age Comparison")
    
    # Create comparison table
    comparison_data = []
    for proj in projections:
        comparison_data.append({
            'Retirement Age': proj['age'],
            'Years Until': proj['years_until_retirement'],
            'Total Assets': format_currency(proj['total_assets']),
            '401(k)': format_currency(proj['projected_401k']),
            'Trad IRA': format_currency(proj['projected_trad_ira']),
            'Roth IRA': format_currency(proj['projected_roth_ira']),
            'Taxable': format_currency(proj['projected_taxable']),
            'Net Monthly Income': format_currency(proj['net_monthly_income']),
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Detailed view for each retirement age
    st.header("💵 Detailed Projections")
    
    tabs = st.tabs([f"Age {proj['age']}" for proj in projections])
    
    for tab, proj in zip(tabs, projections):
        with tab:
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
                st.metric("**TOTAL**", format_currency(proj['total_assets']),
                         f"{proj['years_until_retirement']} years")
            
            st.markdown("---")
            
            # Income breakdown
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Net Monthly Income", format_currency(proj['net_monthly_income']))
                st.metric("Net Annual Income", format_currency(proj['net_annual_income']))
            
            with col2:
                st.metric(
                    "Monthly Pension",
                    format_currency(proj['pension']),
                    f"{proj['pension_multiplier']*100:.0f}% of full"
                )
                st.metric(
                    "Monthly Social Security",
                    format_currency(proj['social_security']),
                    f"{proj['ss_multiplier']*100:.0f}% of full"
                )
            
            with col3:
                st.metric("Effective Tax Rate", f"{proj['taxes']['effective_rate']*100:.1f}%")
                if include_medicare:
                    st.metric("Annual Medicare", format_currency(proj['medicare_costs']))
            
            # Monthly income sources
            st.subheader("📋 Monthly Income Sources (4% Withdrawal)")
            
            income_data = {
                'Source': ['401(k) + Trad IRA', 'Roth IRA (Tax-Free)', 'Taxable Account', 'Pension', 'Social Security', '**TOTAL**'],
                'Monthly Amount': [
                    format_currency(proj['monthly_income_401k']),
                    format_currency(proj['monthly_income_roth']),
                    format_currency(proj['monthly_income_taxable']),
                    format_currency(proj['pension']),
                    format_currency(proj['social_security']),
                    format_currency(proj['total_monthly_income'])
                ]
            }
            
            df_income = pd.DataFrame(income_data)
            st.dataframe(df_income, use_container_width=True, hide_index=True)
    
    # Important notes
    st.header("ℹ️ Important Notes")
    
    with st.expander("Click to view important information"):
        st.markdown("""
        **Account Types:**
        - **401(k) & Traditional IRA**: Tax-deferred. Withdrawals fully taxable. RMDs required at 73.
        - **Roth IRA**: Tax-free withdrawals. No RMDs during owner's lifetime. Contributions must be qualified.
        - **Taxable Accounts**: Only capital gains taxed (assumed 15% on 50% cost basis).
        
        **Social Security:**
        - Taking benefits at 62 reduces monthly amount by ~30%
        - Waiting until 70 increases by ~24% above FRA
        - Up to 85% taxable depending on income
        
        **4% Withdrawal Rule:**
        - Withdraw 4% annually, adjusted for inflation
        - Designed to last 30+ years
        - Applied to all accounts
        
        **Total Assets:**
        - Sum of all retirement and investment accounts
        - Provides complete picture of retirement readiness
        - Different tax treatments apply to each account type
        
        **Disclaimer:**
        This calculator provides estimates only. Actual results vary based on market performance,
        tax law changes, and personal circumstances. Consult a financial advisor for personalized planning.
        """)


if __name__ == "__main__":
    main()
    

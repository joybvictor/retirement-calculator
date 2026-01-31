#!/usr/bin/env python3
"""
Comprehensive Retirement Calculator - Streamlit Version
Web-based retirement planning with taxes, Medicare, inflation, and RMDs
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


def calculate_401k_growth(current_balance: float, years: int, 
                         contribution: float, rate: float) -> float:
    """Calculate 401(k) growth with annual contributions"""
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


def calculate_taxes(withdrawal_401k: float, pension_income: float,
                   ss_income: float, age: int, federal_rate: float,
                   state_rate: float) -> Dict[str, float]:
    """Calculate taxes on retirement income"""
    federal = federal_rate / 100
    state = state_rate / 100
    
    # Calculate Social Security taxable portion
    combined_income = withdrawal_401k + pension_income + (ss_income * 0.5)
    
    if combined_income > 34000:
        ss_taxable_percent = 0.85
    elif combined_income > 25000:
        ss_taxable_percent = 0.50
    else:
        ss_taxable_percent = 0
    
    taxable_ss = ss_income * ss_taxable_percent
    total_taxable_income = withdrawal_401k + pension_income + taxable_ss
    
    # Apply standard deduction
    standard_deduction = get_standard_deduction(age)
    adjusted_gross_income = max(0, total_taxable_income - standard_deduction)
    
    # Calculate taxes
    federal_tax = adjusted_gross_income * federal
    state_tax = adjusted_gross_income * state
    total_tax = federal_tax + state_tax
    
    return {
        'tax_401k': (withdrawal_401k / total_taxable_income) * total_tax if total_taxable_income > 0 else 0,
        'tax_pension': (pension_income / total_taxable_income) * total_tax if total_taxable_income > 0 else 0,
        'tax_ss': (taxable_ss / total_taxable_income) * total_tax if total_taxable_income > 0 else 0,
        'ss_taxable_percent': ss_taxable_percent,
        'standard_deduction': standard_deduction,
        'adjusted_gross_income': adjusted_gross_income,
        'total_tax': total_tax,
        'effective_rate': total_tax / (withdrawal_401k + pension_income + ss_income) if (withdrawal_401k + pension_income + ss_income) > 0 else 0
    }


def generate_amortization_schedule(starting_balance: float,
                                  withdrawal_rate: float, return_rate: float,
                                  pension_income: float, ss_income: float,
                                  retirement_age: int, federal_rate: float,
                                  state_rate: float, inflation_rate: float,
                                  include_medicare: bool,
                                  years: int = 30) -> List[Dict]:
    """Generate year-by-year amortization schedule"""
    schedule = []
    balance = starting_balance
    annual_return = return_rate / 100
    inflation = inflation_rate / 100
    withdrawal_percent = withdrawal_rate / 100
    
    annual_withdrawal = starting_balance * withdrawal_percent
    adjusted_pension = pension_income
    adjusted_ss = ss_income
    
    for year in range(1, years + 1):
        if balance <= 0:
            break
            
        current_age = retirement_age + year - 1
        begin_balance = balance
        
        # Calculate RMD
        rmd = calculate_rmd(balance, current_age)
        withdrawal = max(annual_withdrawal, rmd)
        
        investment_growth = balance * annual_return
        actual_withdrawal = min(withdrawal, begin_balance + investment_growth)
        end_balance = max(0, balance + investment_growth - actual_withdrawal)
        
        # Calculate Medicare costs
        medicare_costs = 0
        if include_medicare:
            medicare_costs = calculate_medicare_costs(
                current_age, actual_withdrawal + adjusted_pension + adjusted_ss
            )
        
        # Calculate taxes
        taxes = calculate_taxes(
            actual_withdrawal, adjusted_pension, adjusted_ss,
            current_age, federal_rate, state_rate
        )
        
        gross_income = actual_withdrawal + adjusted_pension + adjusted_ss
        net_income = gross_income - taxes['total_tax'] - medicare_costs
        
        schedule.append({
            'Year': year,
            'Age': current_age,
            '401k Start': begin_balance,
            'Growth': investment_growth,
            'Withdrawal': actual_withdrawal,
            'RMD': 'Yes' if rmd > annual_withdrawal else 'No',
            '401k End': end_balance,
            'Pension': adjusted_pension,
            'Social Security': adjusted_ss,
            'Gross Income': gross_income,
            'Taxes': taxes['total_tax'],
            'Medicare': medicare_costs,
            'Net Income': net_income
        })
        
        balance = end_balance
        
        # Adjust for inflation
        annual_withdrawal *= (1 + inflation)
        adjusted_pension *= (1 + inflation)
        adjusted_ss *= (1 + inflation)
    
    return schedule


def calculate_projection(current_age: int, current_401k: float, annual_contribution: float,
                        return_rate: float, pension_full: float, ss_full: float,
                        full_retirement_age: int, federal_tax: float, state_tax: float,
                        inflation_rate: float, life_expectancy: int, include_medicare: bool,
                        retirement_age: int) -> Dict:
    """Calculate projection for a specific retirement age"""
    years_until_retirement = retirement_age - current_age
    
    if years_until_retirement <= 0:
        return None
    
    # Project 401(k) growth
    projected_401k = calculate_401k_growth(
        current_401k, years_until_retirement, annual_contribution, return_rate
    )
    
    # Calculate adjusted amounts
    ss_multiplier = get_social_security_multiplier(retirement_age, full_retirement_age)
    pension_multiplier = get_pension_multiplier(retirement_age)
    
    adjusted_ss = ss_full * ss_multiplier
    adjusted_pension = pension_full * pension_multiplier
    
    # Calculate withdrawals
    four_percent_rule = projected_401k * 0.04 / 12
    three_percent_rule = projected_401k * 0.03 / 12
    
    total_monthly_income = four_percent_rule + adjusted_pension + adjusted_ss
    total_annual_income = total_monthly_income * 12
    
    # Calculate taxes
    annual_401k_withdrawal = projected_401k * 0.04
    annual_pension = adjusted_pension * 12
    annual_ss = adjusted_ss * 12
    
    taxes = calculate_taxes(
        annual_401k_withdrawal, annual_pension, annual_ss,
        retirement_age, federal_tax, state_tax
    )
    
    # Calculate Medicare costs
    medicare_costs = 0
    if include_medicare:
        medicare_costs = calculate_medicare_costs(retirement_age, total_annual_income)
    
    net_annual_income = total_annual_income - taxes['total_tax'] - medicare_costs
    net_monthly_income = net_annual_income / 12
    
    years_to_live = life_expectancy - retirement_age
    
    # Generate amortization schedule
    amortization = generate_amortization_schedule(
        projected_401k, 4, return_rate, annual_pension, annual_ss,
        retirement_age, federal_tax, state_tax,
        inflation_rate, include_medicare, years_to_live
    )
    
    return {
        'age': retirement_age,
        'projected_401k': projected_401k,
        'pension': adjusted_pension,
        'pension_multiplier': pension_multiplier,
        'social_security': adjusted_ss,
        'ss_multiplier': ss_multiplier,
        'four_percent_rule': four_percent_rule,
        'three_percent_rule': three_percent_rule,
        'total_monthly_income': total_monthly_income,
        'total_annual_income': total_annual_income,
        'taxes': taxes,
        'medicare_costs': medicare_costs,
        'net_annual_income': net_annual_income,
        'net_monthly_income': net_monthly_income,
        'years_until_retirement': years_until_retirement,
        'amortization': amortization
    }


def format_currency(amount: float) -> str:
    """Format number as currency"""
    return f"${amount:,.0f}"


def main():
    """Main Streamlit app"""
    st.set_page_config(page_title="Retirement Calculator", page_icon="💰", layout="wide")
    
    st.title("💰 Comprehensive Retirement Calculator")
    st.markdown("""
    Calculate your retirement projections including 401(k) growth, pension, Social Security,
    taxes, Medicare, inflation adjustments, and Required Minimum Distributions (RMDs).
    """)
    
    # Sidebar for inputs
    st.sidebar.header("📝 Your Information")
    
    with st.sidebar:
        st.subheader("Basic Information")
        current_age = st.number_input("Current Age", min_value=18, max_value=70, value=45, step=1)
        
        st.subheader("401(k) Information")
        current_401k = st.number_input("Current 401(k) Balance ($)", min_value=0.0, value=250000.0, step=10000.0)
        annual_contribution = st.number_input("Annual 401(k) Contribution ($)", min_value=0.0, value=20000.0, step=1000.0)
        return_rate = st.slider("Expected Annual Return Rate (%)", min_value=0.0, max_value=15.0, value=7.0, step=0.5)
        
        st.subheader("Retirement Benefits")
        full_retirement_age = st.selectbox("Full Retirement Age (FRA)", [66, 67], index=1)
        pension_full = st.number_input("Monthly Pension at Full Retirement ($)", min_value=0.0, value=2000.0, step=100.0)
        ss_full = st.number_input("Monthly Social Security at FRA ($)", min_value=0.0, value=2500.0, step=100.0)
        
        st.subheader("Tax Information")
        federal_tax = st.selectbox(
            "Federal Marginal Tax Rate (%)",
            [10, 12, 22, 24, 32, 35, 37],
            index=2
        )
        state_tax = st.slider("State Tax Rate (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
        
        st.subheader("Planning Assumptions")
        inflation_rate = st.slider("Expected Inflation Rate (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.5)
        life_expectancy = st.number_input("Life Expectancy", min_value=70, max_value=110, value=90, step=1)
        include_medicare = st.checkbox("Include Medicare & Healthcare Costs", value=True)
    
    # Main content area
    if current_age >= 62:
        st.error("⚠️ You must be younger than 62 to see retirement projections.")
        return
    
    # Calculate projections for all retirement ages
    retirement_ages = [62, 65, 67, 70]
    projections = []
    
    for age in retirement_ages:
        if age > current_age:
            proj = calculate_projection(
                current_age, current_401k, annual_contribution, return_rate,
                pension_full, ss_full, full_retirement_age, federal_tax, state_tax,
                inflation_rate, life_expectancy, include_medicare, age
            )
            if proj:
                projections.append(proj)
    
    # Display summary comparison
    st.header("📊 Retirement Age Comparison")
    
    # Create comparison table
    comparison_data = []
    for proj in projections:
        comparison_data.append({
            'Retirement Age': proj['age'],
            'Years Until Retirement': proj['years_until_retirement'],
            'Projected 401(k)': format_currency(proj['projected_401k']),
            'Monthly Net Income': format_currency(proj['net_monthly_income']),
            'Annual Net Income': format_currency(proj['net_annual_income']),
            'Pension (% of full)': f"{format_currency(proj['pension'])} ({proj['pension_multiplier']*100:.0f}%)",
            'Social Security (% of full)': f"{format_currency(proj['social_security'])} ({proj['ss_multiplier']*100:.0f}%)"
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    # Detailed view for each retirement age
    st.header("📈 Detailed Projections")
    
    tabs = st.tabs([f"Age {proj['age']}" for proj in projections])
    
    for tab, proj in zip(tabs, projections):
        with tab:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Projected 401(k)", format_currency(proj['projected_401k']))
                st.metric("Years Until Retirement", proj['years_until_retirement'])
            
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
                st.metric("Net Monthly Income", format_currency(proj['net_monthly_income']))
                st.metric("Net Annual Income", format_currency(proj['net_annual_income']))
            
            # Income breakdown
            st.subheader("💵 Income & Tax Breakdown (4% Withdrawal)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Gross Income**")
                st.write(f"401(k) Withdrawal: {format_currency(proj['projected_401k'] * 0.04)}")
                st.write(f"Pension: {format_currency(proj['pension'] * 12)}")
                st.write(f"Social Security: {format_currency(proj['social_security'] * 12)}")
                st.write(f"**Total Gross: {format_currency(proj['total_annual_income'])}**")
            
            with col2:
                st.markdown("**Taxes & Deductions**")
                st.write(f"Standard Deduction: {format_currency(proj['taxes']['standard_deduction'])}")
                st.write(f"Taxable Income: {format_currency(proj['taxes']['adjusted_gross_income'])}")
                st.write(f"Federal & State Taxes: {format_currency(proj['taxes']['total_tax'])}")
                if include_medicare:
                    st.write(f"Medicare & Healthcare: {format_currency(proj['medicare_costs'])}")
                st.write(f"**Effective Rate: {proj['taxes']['effective_rate']*100:.1f}%**")
            
            # Monthly income options
            st.subheader("📋 Monthly Income Options")
            col1, col2 = st.columns(2)
            
            with col1:
                st.info(f"**Conservative (3% rule):** {format_currency(proj['three_percent_rule'] + proj['pension'] + proj['social_security'])}")
            
            with col2:
                st.success(f"**Standard (4% rule):** {format_currency(proj['total_monthly_income'])}")
            
            # Year-by-year breakdown
            st.subheader("📅 Year-by-Year Amortization Schedule")
            st.caption("All amounts adjusted for inflation annually")
            
            # Convert to DataFrame
            df_amort = pd.DataFrame(proj['amortization'])
            
            # Format currency columns
            currency_cols = ['401k Start', 'Growth', 'Withdrawal', '401k End', 
                           'Pension', 'Social Security', 'Gross Income', 'Taxes', 'Medicare', 'Net Income']
            
            for col in currency_cols:
                if col in df_amort.columns:
                    df_amort[col] = df_amort[col].apply(lambda x: format_currency(x))
            
            # Display table
            st.dataframe(df_amort, use_container_width=True, hide_index=True)
            
            # Summary stats
            final_balance = proj['amortization'][-1]['401k End'] if proj['amortization'] else 0
            years_lasted = len(proj['amortization'])
            
            st.info(f"💡 Money lasted **{years_lasted} years** (until age {proj['age'] + years_lasted - 1}) | "
                   f"Final balance: **{final_balance}**")
            
            # Download button for CSV
            csv = pd.DataFrame(proj['amortization']).to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"retirement_age_{proj['age']}_breakdown.csv",
                mime="text/csv"
            )
    
    # Important notes
    st.header("ℹ️ Important Notes")
    
    with st.expander("Click to view important information"):
        st.markdown("""
        **Social Security:**
        - Taking benefits at 62 reduces your monthly amount by about 30%
        - Waiting until age 70 increases it by about 24% above your full retirement age
        - Up to 85% of Social Security can be taxable depending on your total income
        - Includes automatic COLA (Cost of Living Adjustments)
        
        **Pension:**
        - Many pensions reduce benefits for early retirement
        - This calculator assumes 20% reduction at 62, 7% reduction at 65, and full benefits at 67+
        - Pension income is fully taxable as ordinary income
        - Includes inflation adjustments
        
        **401(k) Withdrawals:**
        - Traditional 401(k) withdrawals are fully taxable as ordinary income
        - The 4% rule suggests withdrawing 4% initially, then adjusting for inflation annually
        - Designed to make your money last 30+ years
        
        **Required Minimum Distributions (RMDs):**
        - Starting at age 73, you must withdraw a minimum amount from your 401(k) each year
        - Based on IRS life expectancy tables
        - Must take RMDs whether you need the money or not
        
        **Inflation:**
        - All income sources (pension, Social Security, and withdrawals) automatically increase
        - Adjustments maintain purchasing power over time
        
        **Medicare & Healthcare:**
        - Costs include Medicare Part B & D premiums
        - IRMAA surcharges (income-based premium adjustments) for high earners
        - Estimated out-of-pocket expenses
        - Medicare starts at age 65
        
        **Standard Deduction:**
        - Tax calculations include the standard deduction for single filers
        - Higher deduction for those 65+ (currently $16,550 vs $14,600)
        
        **Disclaimer:**
        This calculator uses simplified assumptions. Actual results may vary based on market performance,
        tax law changes, and personal circumstances. Consult a financial advisor for personalized retirement planning.
        """)


if __name__ == "__main__":
    main()

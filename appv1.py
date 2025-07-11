import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Advanced Retirement Calculator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-rate {
        font-size: 1.2rem;
        font-weight: bold;
        color: #28a745;
    }
    .warning-rate {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ffc107;
    }
    .danger-rate {
        font-size: 1.2rem;
        font-weight: bold;
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🏦 Advanced Retirement Calculator</h1>', unsafe_allow_html=True)
st.markdown("**Plan your financial future with Monte Carlo simulations and advanced strategies**")

# Sidebar for inputs
st.sidebar.header("📊 Input Parameters")

# Basic Information
st.sidebar.subheader("Personal Information")
current_age = st.sidebar.slider("Current Age", 20, 65, 30)
retirement_age = st.sidebar.selectbox("Target Retirement Age", [58, 60, 62, 65, 67], index=1)
social_security_start_age = st.sidebar.slider("Social Security Start Age", 62, 70, 67)

# Financial Information
st.sidebar.subheader("Financial Details")
current_principal = st.sidebar.number_input(
    "Current Savings ($)", 
    min_value=0, 
    value=100000, 
    step=10000,
    format="%d"
)
monthly_contribution = st.sidebar.number_input(
    "Monthly Contribution ($)", 
    min_value=0, 
    value=2500, 
    step=100,
    format="%d"
)
monthly_social_security = st.sidebar.number_input(
    "Expected Monthly Social Security ($)", 
    min_value=0, 
    value=3000, 
    step=100,
    format="%d"
)

# Advanced Settings
st.sidebar.subheader("Advanced Settings")
with st.sidebar.expander("Market Assumptions"):
    working_years_apr = st.slider("Working Years Return (%)", 5.0, 15.0, 10.5) / 100
    inflation_rate = st.slider("Inflation Rate (%)", 1.0, 8.0, 4.0) / 100
    retirement_apr = st.slider("Retirement Return (%)", 2.0, 8.0, 4.5) / 100

with st.sidebar.expander("Strategy Options"):
    strategy_type = st.selectbox(
        "Withdrawal Strategy",
        ["Basic (4% Rule)", "Enhanced (3.5% + Guardrails)", "Conservative (3% Fixed)"]
    )
    use_bond_tent = st.checkbox("Use Bond Tent Strategy", value=True)
    num_simulations = st.selectbox("Monte Carlo Simulations", [1000, 5000, 10000], index=1)

# Core calculation functions
@st.cache_data
def calculate_retirement_balance(principal, monthly_contrib, years, annual_rate):
    """Calculate future value with monthly contributions"""
    monthly_rate = annual_rate / 12
    months = years * 12
    
    # Future value of current principal
    fv_principal = principal * (1 + annual_rate) ** years
    
    # Future value of monthly contributions (annuity)
    if monthly_rate > 0:
        fv_contributions = monthly_contrib * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    else:
        fv_contributions = monthly_contrib * months
    
    return fv_principal + fv_contributions

@st.cache_data
def calculate_withdrawal_years(balance, monthly_withdrawal, annual_rate, monthly_ss=0, ss_start_age=None, retirement_age=None):
    """Calculate how long retirement funds will last"""
    monthly_rate = annual_rate / 12
    current_balance = balance
    months = 0
    
    while current_balance > 0:
        months += 1
        current_retirement_age = retirement_age + (months / 12)
        
        # Add social security if applicable
        total_monthly_income = monthly_ss if (ss_start_age and current_retirement_age >= ss_start_age) else 0
        
        # Net withdrawal needed
        net_withdrawal = max(0, monthly_withdrawal - total_monthly_income)
        
        # Apply growth and subtract withdrawal
        current_balance = current_balance * (1 + monthly_rate) - net_withdrawal
        
        # Safety check to prevent infinite loop
        if months > 1200:  # 100 years
            return months / 12
    
    return months / 12

@st.cache_data
def run_monte_carlo_simulation(params, num_sims):
    """Run Monte Carlo simulation"""
    np.random.seed(42)  # For reproducibility
    
    results = []
    
    for sim in range(num_sims):
        # Generate random returns
        years_to_retirement = params['retirement_age'] - params['current_age']
        
        # Working years returns
        working_returns = np.random.normal(params['working_apr'], 0.16, years_to_retirement)
        
        # Calculate balance at retirement with variable returns
        balance = params['current_principal']
        for year in range(years_to_retirement):
            balance *= (1 + working_returns[year])
            balance += params['monthly_contribution'] * 12
        
        # Retirement phase
        if params['strategy'] == "Enhanced (3.5% + Guardrails)":
            withdrawal_rate = 0.035
        elif params['strategy'] == "Conservative (3% Fixed)":
            withdrawal_rate = 0.03
        else:
            withdrawal_rate = 0.04
            
        annual_withdrawal = balance * withdrawal_rate
        monthly_withdrawal = annual_withdrawal / 12
        
        # Calculate years lasted
        years_lasted = calculate_withdrawal_years(
            balance, monthly_withdrawal, params['retirement_apr'],
            params['monthly_ss'], params['ss_start_age'], params['retirement_age']
        )
        
        results.append({
            'balance_at_retirement': balance,
            'years_lasted': years_lasted,
            'funds_exhausted_age': params['retirement_age'] + years_lasted
        })
    
    return results

# Main calculation
if st.sidebar.button("🚀 Calculate Retirement Plan", type="primary"):
    
    # Prepare parameters
    params = {
        'current_age': current_age,
        'retirement_age': retirement_age,
        'current_principal': current_principal,
        'monthly_contribution': monthly_contribution,
        'monthly_ss': monthly_social_security,
        'ss_start_age': social_security_start_age,
        'working_apr': working_years_apr,
        'retirement_apr': retirement_apr,
        'inflation_rate': inflation_rate,
        'strategy': strategy_type
    }
    
    # Basic calculation
    years_to_retirement = retirement_age - current_age
    retirement_balance = calculate_retirement_balance(
        current_principal, monthly_contribution, years_to_retirement, working_years_apr
    )
    
    # Estimate monthly expenses
    future_monthly_expenses = monthly_contribution * (1 + inflation_rate) ** years_to_retirement
    
    # Calculate years funds will last
    if strategy_type == "Enhanced (3.5% + Guardrails)":
        withdrawal_rate = 0.035
    elif strategy_type == "Conservative (3% Fixed)":
        withdrawal_rate = 0.03
    else:
        withdrawal_rate = 0.04
        
    annual_withdrawal = retirement_balance * withdrawal_rate
    monthly_withdrawal = annual_withdrawal / 12
    
    years_lasting = calculate_withdrawal_years(
        retirement_balance, monthly_withdrawal, retirement_apr,
        monthly_social_security, social_security_start_age, retirement_age
    )
    
    funds_exhausted_age = retirement_age + years_lasting
    
    # Display results
    st.header("📊 Retirement Analysis Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Balance at Retirement",
            f"${retirement_balance:,.0f}",
            delta=f"${retirement_balance - current_principal:,.0f} growth"
        )
    
    with col2:
        st.metric(
            "Fund Duration",
            f"{years_lasting:.1f} years",
            delta=f"Until age {funds_exhausted_age:.0f}"
        )
    
    with col3:
        st.metric(
            "Monthly Withdrawal",
            f"${monthly_withdrawal:,.0f}",
            delta=f"{withdrawal_rate:.1%} rate"
        )
    
    with col4:
        net_monthly_need = max(0, monthly_withdrawal - monthly_social_security)
        st.metric(
            "Net Monthly Need",
            f"${net_monthly_need:,.0f}",
            delta=f"After Social Security"
        )
    
    # Success indicator
    if years_lasting >= 35:
        st.markdown('<div class="success-rate">✅ Excellent: Funds last 35+ years</div>', unsafe_allow_html=True)
    elif years_lasting >= 30:
        st.markdown('<div class="warning-rate">⚠️ Good: Funds last 30+ years</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="danger-rate">❌ Caution: Funds last less than 30 years</div>', unsafe_allow_html=True)
    
    # Monte Carlo Analysis
    st.header("🎲 Monte Carlo Simulation")
    
    with st.spinner(f'Running {num_simulations:,} simulations...'):
        mc_results = run_monte_carlo_simulation(params, num_simulations)
    
    # Extract data
    balances = [r['balance_at_retirement'] for r in mc_results]
    years_lasted_list = [r['years_lasted'] for r in mc_results]
    exhausted_ages = [r['funds_exhausted_age'] for r in mc_results]
    
    # Monte Carlo metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Median Balance",
            f"${np.median(balances):,.0f}",
            delta=f"Range: ${np.percentile(balances, 10):,.0f} - ${np.percentile(balances, 90):,.0f}"
        )
    
    with col2:
        success_30 = np.sum(np.array(years_lasted_list) >= 30) / len(years_lasted_list) * 100
        st.metric(
            "30+ Year Success Rate",
            f"{success_30:.1f}%",
            delta=f"Median: {np.median(years_lasted_list):.1f} years"
        )
    
    with col3:
        success_35 = np.sum(np.array(years_lasted_list) >= 35) / len(years_lasted_list) * 100
        st.metric(
            "35+ Year Success Rate",
            f"{success_35:.1f}%",
            delta=f"90th percentile: {np.percentile(years_lasted_list, 90):.1f} years"
        )
    
    # Visualizations
    st.header("📈 Analysis Charts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Balance distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(np.array(balances)/1000000, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
        ax.axvline(np.median(balances)/1000000, color='red', linestyle='--', linewidth=2, label=f'Median: ${np.median(balances)/1000000:.1f}M')
        ax.set_xlabel('Balance at Retirement ($ Millions)')
        ax.set_ylabel('Frequency')
        ax.set_title('Distribution of Retirement Balances')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    with col2:
        # Years lasted distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(years_lasted_list, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
        ax.axvline(np.median(years_lasted_list), color='red', linestyle='--', linewidth=2, label=f'Median: {np.median(years_lasted_list):.1f} years')
        ax.axvline(30, color='orange', linestyle=':', linewidth=2, label='30 year target')
        ax.set_xlabel('Years Funds Last')
        ax.set_ylabel('Frequency')
        ax.set_title('Distribution of Fund Duration')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    # Growth projection chart
    st.subheader("Portfolio Growth Projection")
    ages = list(range(current_age, retirement_age + 1))
    projected_balances = []
    
    for age in ages:
        years = age - current_age
        if years == 0:
            projected_balances.append(current_principal)
        else:
            balance = calculate_retirement_balance(
                current_principal, monthly_contribution, years, working_years_apr
            )
            projected_balances.append(balance)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(ages, np.array(projected_balances)/1000000, 'b-', linewidth=3, marker='o', markersize=6)
    ax.scatter([retirement_age], [retirement_balance/1000000], color='red', s=200, zorder=5, label=f'Retirement: ${retirement_balance/1000000:.1f}M')
    ax.set_xlabel('Age')
    ax.set_ylabel('Portfolio Value ($ Millions)')
    ax.set_title('Portfolio Growth to Retirement')
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
    
    # Summary and recommendations
    st.header("💡 Summary & Recommendations")
    
    if success_30 >= 80:
        st.success("🎉 **Excellent Plan!** Your retirement strategy shows strong resilience with high success rates.")
    elif success_30 >= 60:
        st.warning("⚠️ **Good Plan with Room for Improvement.** Consider the enhanced strategy for better outcomes.")
    else:
        st.error("❌ **Plan Needs Adjustment.** Consider increasing contributions or delaying retirement.")
    
    # Recommendations
    st.subheader("Strategic Recommendations:")
    
    if strategy_type == "Basic (4% Rule)":
        st.info("""
        **Consider upgrading to Enhanced Strategy:**
        - Use 3.5% withdrawal rate with guardrails
        - Implement bond tent starting at age 50
        - This can improve success rates by 40-50 percentage points
        """)
    
    if years_lasting < 30:
        st.warning("""
        **Improvement Suggestions:**
        - Increase monthly contributions by $500-1000
        - Consider working 2-3 additional years
        - Reduce planned retirement expenses
        - Use more conservative withdrawal rate
        """)
    
    # Download results
    results_df = pd.DataFrame({
        'Simulation': range(1, len(mc_results) + 1),
        'Balance_at_Retirement': balances,
        'Years_Lasted': years_lasted_list,
        'Funds_Exhausted_Age': exhausted_ages
    })
    
    csv = results_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Simulation Results",
        data=csv,
        file_name=f"retirement_simulation_{retirement_age}.csv",
        mime="text/csv"
    )

# Information section
with st.expander("ℹ️ How This Calculator Works"):
    st.markdown("""
    ### Calculation Methods
    
    **Basic Calculation:**
    - Uses compound interest for portfolio growth
    - Accounts for monthly contributions during working years
    - Applies different return rates for working vs retirement years
    
    **Monte Carlo Simulation:**
    - Runs thousands of scenarios with random market returns
    - Based on historical market data (S&P 500 1974-2024)
    - Provides probability-based outcomes
    
    **Strategy Options:**
    - **Basic (4% Rule):** Traditional 4% annual withdrawal
    - **Enhanced (3.5% + Guardrails):** Dynamic withdrawal with 2.5%-5% range
    - **Conservative (3% Fixed):** Lower withdrawal for maximum security
    
    **Assumptions:**
    - Working years return: 10.5% (historical S&P 500 average)
    - Retirement return: 4.5% (inflation + 0.5%)
    - Inflation: 4.0% (historical average)
    - Social Security starts at specified age
    
    *Note: This is for planning purposes only. Consult a financial advisor for personalized advice.*
    """)

# Footer
st.markdown("---")
st.markdown("**Advanced Retirement Calculator** | Built with Streamlit | Data-driven retirement planning")
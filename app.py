import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Retirement Simulator",
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
        font-weight: bold;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-metric {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
    }
    .warning-metric {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">💰 Retirement Planning Calculator + Simulator</h1>', unsafe_allow_html=True)

# Sidebar for inputs
st.sidebar.header("📊 Retirement Parameters")

# Personal Information
st.sidebar.subheader("Personal Information")
current_age = st.sidebar.slider("Current Age", 20, 65, 30)
target_retirement_age = st.sidebar.slider("Target Retirement Age", 55, 70, 62)
current_savings = st.sidebar.number_input("Current Savings ($)", 0, 2000000, 100000, step=1000)
monthly_contribution = st.sidebar.number_input("Monthly Contribution ($)", 0, 20000, 2000, step=100)

# Social Security
st.sidebar.subheader("Social Security")
ss_start_age = st.sidebar.slider("Social Security Start Age", 62, 70, 67)
monthly_ss = st.sidebar.number_input("Monthly Social Security ($)", 0, 10000, 3000, step=100)

# Market Assumptions
st.sidebar.subheader("Market Assumptions")
working_return = st.sidebar.slider("Working Years Return (%)", 6.0, 15.0, 10.5, 0.1) / 100
inflation_rate = st.sidebar.slider("Inflation Rate (%)", 2.0, 6.0, 4.0, 0.1) / 100
retirement_return = st.sidebar.slider("Retirement Return (%)", 3.0, 8.0, 4.5, 0.1) / 100

# Enhanced Withdrawal Strategy
st.sidebar.subheader("Withdrawal Strategy")
withdrawal_strategies = {
    "Conservative (3.0%)": 0.030,
    "Enhanced (3.5% + Guardrails)": 0.035,
    "Traditional (4.0%)": 0.040,
    "Aggressive (4.5%)": 0.045
}
selected_strategy = st.sidebar.selectbox("Withdrawal Strategy", list(withdrawal_strategies.keys()), index=1)
withdrawal_rate = withdrawal_strategies[selected_strategy]

# Guardrails settings (only show if Enhanced strategy selected)
use_guardrails = "Guardrails" in selected_strategy
if use_guardrails:
    st.sidebar.write("**Guardrails Settings:**")
    guardrail_lower = st.sidebar.slider("Minimum Withdrawal Rate (%)", 2.0, 4.0, 2.5, 0.1) / 100
    guardrail_upper = st.sidebar.slider("Maximum Withdrawal Rate (%)", 4.0, 6.0, 5.0, 0.1) / 100
else:
    guardrail_lower = withdrawal_rate
    guardrail_upper = withdrawal_rate

# Bond Tent Strategy
st.sidebar.subheader("Bond Tent Strategy")
use_bond_tent = st.sidebar.checkbox("Use Bond Tent Strategy", value=True)
if use_bond_tent:
    bond_tent_start_age = st.sidebar.slider("Bond Tent Start Age", 40, 60, 50)
    final_bond_ratio = st.sidebar.slider("Final Bond Ratio (%)", 20, 80, 50) / 100
    initial_stock_ratio = st.sidebar.slider("Initial Stock Ratio (%)", 60, 100, 90) / 100
else:
    bond_tent_start_age = target_retirement_age
    final_bond_ratio = 0.4
    initial_stock_ratio = 0.8

# Monte Carlo Settings
st.sidebar.subheader("Monte Carlo Simulation")
num_simulations = st.sidebar.selectbox("Number of Simulations", [1000, 5000, 10000], index=1)

# Information section
with st.sidebar.expander("ℹ️ Strategy Information"):
    st.write("""
    **Enhanced Strategy (3.5% + Guardrails):**
    - Starts with 3.5% withdrawal rate
    - Automatically adjusts based on portfolio performance
    - Reduces withdrawals in bad markets (down to 2.5%)
    - Increases withdrawals in good markets (up to 5.0%)
    - Provides better long-term sustainability
    
    **Bond Tent Strategy:**
    - Gradually shifts from stocks to bonds as you approach retirement
    - Reduces sequence of returns risk
    - Maintains growth potential while managing volatility
    - Example: Start 90% stocks at age 35, gradually move to 50% stocks/50% bonds by retirement
    - Helps protect against market crashes near retirement
    
    **Guardrails Approach:**
    - Dynamic withdrawal adjustments based on portfolio performance
    - If portfolio grows significantly: increase withdrawals
    - If portfolio declines: temporarily reduce withdrawals
    - Maintains purchasing power while protecting principal
    """)

# Calculate button
if st.sidebar.button("🚀 Calculate Retirement Plan", type="primary"):
    
    # Helper functions
    def calculate_bond_tent_allocation(age, start_age, retirement_age, initial_stock, final_bond):
        """Calculate stock/bond allocation based on bond tent strategy"""
        if not use_bond_tent or age < start_age:
            return initial_stock, 1 - initial_stock
        elif age >= retirement_age:
            return 1 - final_bond, final_bond
        else:
            # Linear transition
            progress = (age - start_age) / (retirement_age - start_age)
            stock_reduction = initial_stock - (1 - final_bond)
            current_stock = initial_stock - (stock_reduction * progress)
            return current_stock, 1 - current_stock
    
    def calculate_retirement_balance(principal, monthly_contrib, years, annual_rate, use_tent=False):
        """Calculate future value with monthly contributions and optional bond tent"""
        balance = principal
        
        for year in range(years):
            age = current_age + year
            
            if use_tent:
                stock_pct, bond_pct = calculate_bond_tent_allocation(
                    age, bond_tent_start_age, target_retirement_age, 
                    initial_stock_ratio, final_bond_ratio
                )
                # Blended return based on allocation
                stock_return = annual_rate
                bond_return = retirement_return
                blended_return = (stock_pct * stock_return) + (bond_pct * bond_return)
            else:
                blended_return = annual_rate
            
            # Apply return
            balance *= (1 + blended_return)
            
            # Add contributions
            annual_contribution = monthly_contrib * 12
            balance += annual_contribution
        
        return balance
    
    def calculate_withdrawal_years_enhanced(balance, monthly_withdrawal, annual_rate, 
                                          monthly_ss=0, ss_start_age=None, retirement_age=None,
                                          use_guardrails=False, lower_bound=0.025, upper_bound=0.05):
        """Calculate how long retirement funds will last with enhanced strategy"""
        monthly_rate = annual_rate / 12
        current_balance = balance
        months = 0
        initial_annual_withdrawal = monthly_withdrawal * 12
        current_withdrawal_rate = initial_annual_withdrawal / balance
        annual_withdrawal = initial_annual_withdrawal
        
        # Track for infinite fund detection
        consecutive_growth_months = 0
        
        while current_balance > 0 and months < 1200:  # Remove 100-year cap, use 1200 months as safety
            months += 1
            current_retirement_age = retirement_age + (months / 12)
            
            # Apply growth
            current_balance *= (1 + monthly_rate)
            
            # Social Security
            ss_income = monthly_ss if (ss_start_age and current_retirement_age >= ss_start_age) else 0
            
            # Guardrails adjustment (annual basis)
            if use_guardrails and months % 12 == 0 and months > 0:
                current_implied_rate = annual_withdrawal / current_balance if current_balance > 0 else upper_bound
                
                if current_implied_rate > upper_bound:
                    # Reduce withdrawal
                    current_withdrawal_rate = max(lower_bound, current_withdrawal_rate * 0.95)
                    annual_withdrawal = current_balance * current_withdrawal_rate
                elif current_implied_rate < lower_bound and current_withdrawal_rate < upper_bound:
                    # Increase withdrawal
                    current_withdrawal_rate = min(upper_bound, current_withdrawal_rate * 1.05)
                    annual_withdrawal = current_balance * current_withdrawal_rate
            
            # Net withdrawal
            monthly_net_withdrawal = max(0, (annual_withdrawal / 12) - ss_income)
            current_balance -= monthly_net_withdrawal
            
            # Check for infinite fund scenario (35 years of consistent growth)
            if current_balance > balance * 0.8:  # If balance is still 80% of original after some time
                consecutive_growth_months += 1
                if consecutive_growth_months >= 420:  # 35 years
                    return float('inf')  # Infinite duration
            else:
                consecutive_growth_months = 0
        
        return months / 12
    
    def run_monte_carlo_simulation(num_sims):
        """Run Monte Carlo simulation with enhanced strategies"""
        results = []
        
        for sim in range(num_sims):
            np.random.seed(sim)
            
            # Generate random returns
            years_to_retirement = target_retirement_age - current_age
            working_returns = np.random.normal(working_return, 0.17, years_to_retirement)
            
            # Calculate balance at retirement with bond tent
            balance = current_savings
            for year in range(years_to_retirement):
                age = current_age + year
                
                if use_bond_tent:
                    stock_pct, bond_pct = calculate_bond_tent_allocation(
                        age, bond_tent_start_age, target_retirement_age,
                        initial_stock_ratio, final_bond_ratio
                    )
                    stock_return_sim = working_returns[year]
                    bond_return_sim = np.random.normal(retirement_return, 0.025)
                    blended_return = (stock_pct * stock_return_sim) + (bond_pct * bond_return_sim)
                else:
                    blended_return = working_returns[year]
                
                balance *= (1 + blended_return)
                balance += monthly_contribution * 12
            
            # Calculate withdrawal phase
            future_monthly_expenses = monthly_contribution * (1 + inflation_rate) ** years_to_retirement
            
            years_lasted = calculate_withdrawal_years_enhanced(
                balance, future_monthly_expenses, retirement_return,
                monthly_ss, ss_start_age, target_retirement_age,
                use_guardrails, guardrail_lower, guardrail_upper
            )
            
            # Calculate monthly withdrawal amount for this simulation
            if years_lasted == float('inf'):
                # For infinite scenarios, calculate sustainable withdrawal
                sustainable_annual = balance * withdrawal_rate
                monthly_withdrawal_amount = sustainable_annual / 12
            else:
                # Use the planned withdrawal amount
                monthly_withdrawal_amount = future_monthly_expenses
            
            results.append({
                'balance_at_retirement': balance,
                'years_lasted': years_lasted,
                'monthly_withdrawal': monthly_withdrawal_amount
            })
        
        return results
    
    # Perform calculations
    with st.spinner('Running calculations...'):
        # Basic calculation
        years_to_retirement = target_retirement_age - current_age
        retirement_balance = calculate_retirement_balance(
            current_savings, monthly_contribution, years_to_retirement, 
            working_return, use_bond_tent
        )
        
        # Future monthly expenses
        future_monthly_expenses = monthly_contribution * (1 + inflation_rate) ** years_to_retirement
        
        # Calculate fund duration
        fund_duration = calculate_withdrawal_years_enhanced(
            retirement_balance, future_monthly_expenses, retirement_return,
            monthly_ss, ss_start_age, target_retirement_age,
            use_guardrails, guardrail_lower, guardrail_upper
        )
        
        # Monte Carlo simulation
        mc_results = run_monte_carlo_simulation(num_simulations)
        
        # Extract results
        balances = [r['balance_at_retirement'] for r in mc_results]
        years_lasted = [r['years_lasted'] for r in mc_results if r['years_lasted'] != float('inf')]
        infinite_scenarios = sum(1 for r in mc_results if r['years_lasted'] == float('inf'))
        monthly_withdrawals = [r['monthly_withdrawal'] for r in mc_results]
    
    # Display results
    st.header("📊 Retirement Analysis Results")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container success-metric">', unsafe_allow_html=True)
        st.metric("Balance at Retirement", f"${retirement_balance:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if fund_duration == float('inf'):
            duration_display = "Infinite ♾️"
            st.markdown('<div class="metric-container success-metric">', unsafe_allow_html=True)
        elif fund_duration >= 35:
            duration_display = f"{fund_duration:.0f} years"
            st.markdown('<div class="metric-container success-metric">', unsafe_allow_html=True)
        else:
            duration_display = f"{fund_duration:.0f} years"
            st.markdown('<div class="metric-container warning-metric">', unsafe_allow_html=True)
        
        st.metric("Fund Duration", duration_display)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Monthly Expenses", f"${future_monthly_expenses:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        funds_exhausted_age = target_retirement_age + fund_duration if fund_duration != float('inf') else "Never"
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Funds Last Until Age", funds_exhausted_age)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Special handling for infinite fund duration
    if fund_duration == float('inf'):
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.success("🎉 **Infinite Fund Duration Detected!** Your retirement funds are projected to last indefinitely.")
        
        # Calculate 35-year retirement monthly withdrawal
        sustainable_35_year = retirement_balance * 0.035  # 3.5% annual
        monthly_35_year = sustainable_35_year / 12
        
        st.write(f"""
        **For a 35-year retirement period, you could withdraw:**
        - **Monthly Amount:** ${monthly_35_year:,.0f}
        - **Annual Amount:** ${sustainable_35_year:,.0f}
        - **Withdrawal Rate:** 3.5% annually
        
        This withdrawal amount would provide a comfortable 35-year retirement while preserving capital.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Monte Carlo Results
    st.header("🎲 Monte Carlo Simulation Results")
    st.write(f"Based on {num_simulations:,} simulations:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        median_balance = np.median(balances)
        st.metric("Median Balance at Retirement", f"${median_balance:,.0f}")
        
        # Calculate median monthly withdrawal
        median_monthly_withdrawal = np.median(monthly_withdrawals)
        st.metric("Median Monthly Withdrawal", f"${median_monthly_withdrawal:,.0f}")
    
    with col2:
        if years_lasted:
            median_years = np.median(years_lasted)
            st.metric("Median Fund Duration", f"{median_years:.0f} years")
        else:
            st.metric("Median Fund Duration", "All Infinite ♾️")
        
        if infinite_scenarios > 0:
            infinite_pct = (infinite_scenarios / num_simulations) * 100
            st.metric("Infinite Duration Rate", f"{infinite_pct:.1f}%")
    
    with col3:
        if years_lasted:
            success_30 = sum(1 for y in years_lasted if y >= 30) / len(years_lasted) * 100
            success_35 = sum(1 for y in years_lasted if y >= 35) / len(years_lasted) * 100
            
            # Add infinite scenarios to success rates
            total_success_30 = (sum(1 for y in years_lasted if y >= 30) + infinite_scenarios) / num_simulations * 100
            total_success_35 = (sum(1 for y in years_lasted if y >= 35) + infinite_scenarios) / num_simulations * 100
            
            st.metric("30+ Year Success Rate", f"{total_success_30:.1f}%")
            st.metric("35+ Year Success Rate", f"{total_success_35:.1f}%")
        else:
            st.metric("30+ Year Success Rate", "100.0%")
            st.metric("35+ Year Success Rate", "100.0%")
    
    # Visualizations
    st.header("📈 Analysis Charts")
    
    # Create charts
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Balance Distribution
    ax1.hist(np.array(balances)/1000000, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax1.axvline(median_balance/1000000, color='red', linestyle='--', linewidth=2, label=f'Median: ${median_balance/1000000:.1f}M')
    ax1.set_xlabel('Balance at Retirement ($ Millions)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Retirement Balances')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Years Lasted Distribution
    if years_lasted:
        ax2.hist(years_lasted, bins=30, alpha=0.7, color='lightgreen', edgecolor='black')
        if years_lasted:
            ax2.axvline(np.median(years_lasted), color='red', linestyle='--', linewidth=2, 
                       label=f'Median: {np.median(years_lasted):.0f} years')
        ax2.set_xlabel('Years Funds Last')
        ax2.set_ylabel('Frequency')
        ax2.set_title('Distribution of Fund Duration')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        if infinite_scenarios > 0:
            ax2.text(0.7, 0.9, f'Infinite scenarios: {infinite_scenarios}', 
                    transform=ax2.transAxes, bbox=dict(boxstyle="round", facecolor='yellow', alpha=0.7))
    else:
        ax2.text(0.5, 0.5, 'All scenarios show\ninfinite duration', 
                ha='center', va='center', transform=ax2.transAxes, 
                bbox=dict(boxstyle="round", facecolor='lightgreen', alpha=0.7))
        ax2.set_title('Fund Duration: All Infinite')
    
    # 3. Growth Projection
    ages = list(range(current_age, target_retirement_age + 1))
    projected_balances = []
    balance = current_savings
    
    for i, age in enumerate(ages):
        if i == 0:
            projected_balances.append(balance)
        else:
            if use_bond_tent:
                stock_pct, bond_pct = calculate_bond_tent_allocation(
                    age-1, bond_tent_start_age, target_retirement_age,
                    initial_stock_ratio, final_bond_ratio
                )
                blended_return = (stock_pct * working_return) + (bond_pct * retirement_return)
            else:
                blended_return = working_return
            
            balance = balance * (1 + blended_return) + (monthly_contribution * 12)
            projected_balances.append(balance)
    
    ax3.plot(ages, np.array(projected_balances)/1000000, 'b-', linewidth=3, label='Projected Balance')
    ax3.scatter([target_retirement_age], [retirement_balance/1000000], color='red', s=100, zorder=5, label='Retirement')
    ax3.set_xlabel('Age')
    ax3.set_ylabel('Balance ($ Millions)')
    ax3.set_title('Account Growth Projection')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. Bond Tent Allocation (if enabled)
    if use_bond_tent:
        tent_ages = list(range(current_age, target_retirement_age + 5))
        stock_allocations = []
        bond_allocations = []
        
        for age in tent_ages:
            stock_pct, bond_pct = calculate_bond_tent_allocation(
                age, bond_tent_start_age, target_retirement_age,
                initial_stock_ratio, final_bond_ratio
            )
            stock_allocations.append(stock_pct * 100)
            bond_allocations.append(bond_pct * 100)
        
        ax4.plot(tent_ages, stock_allocations, 'b-', linewidth=2, label='Stocks')
        ax4.plot(tent_ages, bond_allocations, 'r-', linewidth=2, label='Bonds')
        ax4.axvline(bond_tent_start_age, color='gray', linestyle='--', alpha=0.7, label='Tent Start')
        ax4.axvline(target_retirement_age, color='black', linestyle='--', alpha=0.7, label='Retirement')
        ax4.set_xlabel('Age')
        ax4.set_ylabel('Allocation (%)')
        ax4.set_title('Bond Tent Strategy')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_ylim(0, 100)
    else:
        ax4.text(0.5, 0.5, 'Bond Tent Strategy\nNot Enabled', 
                ha='center', va='center', transform=ax4.transAxes,
                bbox=dict(boxstyle="round", facecolor='lightgray', alpha=0.7))
        ax4.set_title('Bond Tent Strategy: Disabled')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Download simulation results
    if st.button("📥 Download Simulation Results"):
        df_results = pd.DataFrame(mc_results)
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"retirement_simulation_{num_simulations}_runs.csv",
            mime="text/csv"
        )

else:
    # Default display when no calculation has been run
    st.info("👈 Adjust your parameters in the sidebar and click 'Calculate Retirement Plan' to see your results!")
    
    # Show some educational content
    st.header("🎓 Understanding Your Retirement Strategy")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Enhanced Withdrawal Strategy")
        st.write("""
        The Enhanced Strategy (3.5% + Guardrails) provides:
        - **Better Sustainability**: Lower initial withdrawal rate
        - **Flexibility**: Automatic adjustments based on market performance
        - **Protection**: Reduces withdrawals during market downturns
        - **Growth**: Increases withdrawals during market upturns
        """)
        
        st.subheader("Bond Tent Strategy")
        st.write("""
        Gradually shifts from aggressive to conservative allocation:
        - **Early Career**: High stock allocation for growth
        - **Pre-Retirement**: Gradual shift to bonds for stability
        - **Retirement**: Balanced allocation for longevity
        - **Benefit**: Reduces sequence of returns risk
        """)
    
    with col2:
        st.subheader("Monte Carlo Simulation")
        st.write("""
        Tests your plan against thousands of market scenarios:
        - **Realistic**: Uses historical market volatility
        - **Comprehensive**: Tests various market conditions
        - **Probabilistic**: Shows range of possible outcomes
        - **Confidence**: Provides success rate estimates
        """)
        
        st.subheader("Key Metrics")
        st.write("""
        - **Fund Duration**: How long your money lasts
        - **Success Rate**: Probability of lasting 30+ years
        - **Median Balance**: Middle outcome from simulations
        - **Withdrawal Rate**: Percentage of portfolio withdrawn annually
        """)

# Footer
st.markdown("---")
st.markdown("*This calculator provides estimates based on historical data and assumptions. Consult with a financial advisor for personalized advice.*")
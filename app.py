import streamlit as st
import pandas as pd
import yaml
from dotenv import load_dotenv
import os
from datetime import datetime

from sim_engine.fleet import Fleet
from sim_engine.price_engine import PriceEngine
from sim_engine.optimizer import Optimizer
from sim_engine.visualizations import calculate_kpis, plot_soe, plot_revenue_cumulative, plot_dispatch_and_price, plot_individual_battery_analysis, plot_revenue_pie_chart, plot_battery_performance_table

# Page Config
st.set_page_config(page_title="Battery Fleet Sim", layout="wide")

# Load Config
def load_config():
    load_dotenv("config/.env")
    with open("config/batteries.yaml", "r") as f:
        full_config = yaml.safe_load(f)
    return full_config, os.environ

full_config, env = load_config()
batteries_cfg = full_config['batteries']
fleet_global_cfg = full_config.get('fleet_global', {})

# Sidebar Controls
# State Initialization & Reset
default_params = {
    "charge_thresh": 100.0,
    "discharge_thresh": 150.0,
    "sim_days": 7,
    "base_price": 80.0,
    "peak_multiplier": 2.0
}

for key, val in default_params.items():
    if key not in st.session_state:
        st.session_state[key] = val

def reset_defaults():
    for key, val in default_params.items():
        st.session_state[key] = val



st.sidebar.subheader("Strategy Settings")
strategy_type = st.sidebar.selectbox("Strategy", ["Threshold-Based"])
charge_thresh = st.sidebar.slider("Charge Threshold ($/MWh)", 0.0, 150.0, key="charge_thresh", step=1.0, help="Charge when price is below this.")
discharge_thresh = st.sidebar.slider("Discharge Threshold ($/MWh)", 100.0, 300.0, key="discharge_thresh", step=1.0, help="Discharge when price is above this.")

st.sidebar.subheader("Price Simulation Parameters")
sim_days = st.sidebar.slider("Duration (Days)", 1, 30, key="sim_days")
base_price = st.sidebar.number_input("Base Price ($/MWh)", key="base_price")
peak_multiplier = st.sidebar.slider("Peak Multiplier", 1.0, 4.0, key="peak_multiplier", step=0.1, help="Multiplier for evening peaks.")

# Main Dashboard
st.title("Battery Fleet Optimization")

# Fleet Overview (Always Visible)
display_fleet = Fleet(batteries_cfg)
with st.expander("Fleet Overview", expanded=True):
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total BESS", display_fleet.count)
    m2.metric("Total Capacity", f"{display_fleet.total_capacity} MWh")
    m3.metric("Max Charge", f"{fleet_global_cfg.get('max_charge_mw', 100)} MW", help="Maximum charge rate of the fleet.")
    m4.metric("Max Discharge", f"{fleet_global_cfg.get('max_discharge_mw', 100)} MW", help="Maximum discharge rate of the fleet.")
    m5.metric("Market Resolution", env.get('MARKET_RESOLUTION', '60min'), help="Resolution of the market data.")

if st.sidebar.button("Run Simulation", type="primary"):
    with st.spinner("Running Optimization..."):
        # 1. Setup
        fleet = Fleet(batteries_cfg)
        price_engine = PriceEngine()
        optimizer = Optimizer(fleet)
        
        # Parse Resolution from Env
        resolution_str = env.get('MARKET_RESOLUTION', '60min').replace('T', 'min')
        duration_hours = pd.to_timedelta(resolution_str).total_seconds() / 3600.0
        
        # 2. Generate Prices
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        prices_df = price_engine.generate_prices(
            start_date, 
            days=sim_days, 
            resolution=resolution_str,
            base_price=base_price,
            peak_multiplier=peak_multiplier
        )
        
        # 3. Run Optimization
        results_df = optimizer.run_threshold_strategy(
            prices_df,
            charge_threshold=charge_thresh,
            discharge_threshold=discharge_thresh,
            fleet_max_charge=float(fleet_global_cfg.get('max_charge_mw', 100)),
            fleet_max_discharge=float(fleet_global_cfg.get('max_discharge_mw', 100)),
            duration_hours=duration_hours
        )
        
        # Store in Session State
        st.session_state['results_df'] = results_df
        st.session_state['fleet_capacity'] = fleet.total_capacity

# Render Dashboard if results exist
if 'results_df' in st.session_state:
    results_df = st.session_state['results_df']
    fleet_capacity = st.session_state['fleet_capacity']
    
    # 4. Display KPIs
    kpis = calculate_kpis(results_df, fleet_capacity, sim_days)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Net Revenue", f"${kpis['revenue']:,.2f}", delta_color="normal", help="Total earnings from discharging minus cost of charging.")
    col2.metric("Norm. Revenue", f"${kpis['annualized_rev_per_mwh']:,.2f}", help="Annualized Normalized Revenue ($/MWh/Year).")
    col3.metric("Total Charged", f"{kpis['charged_mwh']:.1f} MWh", help="Total energy absorbed by the fleet from the grid.")
    col4.metric("Total Discharged", f"{kpis['discharged_mwh']:.1f} MWh", help="Total energy supplied by the fleet to the grid.")
    col5.metric("Equivalent Cycles", f"{kpis['cycles']:.2f}", help="Total energy discharged divided by total fleet capacity.")
    
    # 5. Visualizations
    tab1, tab2, tab3 = st.tabs(["Fleet Performance", "Revenue", "Asset Performance"])
    
    with tab1:
        st.plotly_chart(
            plot_dispatch_and_price(results_df, charge_thresh, discharge_thresh), 
            width='stretch'
        )
        st.plotly_chart(plot_soe(results_df), width='stretch')
        
    with tab2:
        st.plotly_chart(plot_revenue_cumulative(results_df), width='stretch')
        st.plotly_chart(plot_revenue_pie_chart(results_df), width='stretch')
        
    with tab3:        
        #st.subheader("Single Battery Performance")

        st.plotly_chart(plot_battery_performance_table(results_df, batteries_cfg), width='stretch')
    
        battery_ids = sorted(results_df['battery_id'].unique())
        selected_battery = st.selectbox("Select Battery ID", battery_ids)
        
        if selected_battery:
            st.plotly_chart(
                plot_individual_battery_analysis(results_df, selected_battery),
                width='stretch'
            )

    # 6. Data Export
    with st.expander("Detailed Results"):
        st.dataframe(results_df)
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, "simulation_results.csv", "text/csv")
else:
    st.info("Adjust settings in the sidebar and click 'Run Simulation' to start.")

st.sidebar.markdown("---")
st.sidebar.button("Reset to Defaults", on_click=reset_defaults)

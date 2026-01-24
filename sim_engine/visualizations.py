import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def calculate_kpis(results_df: pd.DataFrame, fleet_capacity_mwh: float, sim_days: int = 7):
    """
    Calculate Key Performance Indicators.
    """
    total_revenue = results_df['revenue'].sum()
    total_charged_mwh = abs(results_df[results_df['mw'] < 0]['mw'].sum())
    total_discharged_mwh = results_df[results_df['mw'] > 0]['mw'].sum()
    
    equivalent_cycles = total_discharged_mwh / fleet_capacity_mwh if fleet_capacity_mwh > 0 else 0
    
    # Annualized Normalized Revenue ($/MWh/Year)
    # Norm Rev ($/MWh) = Total Rev / Capacity
    # Annualized = Norm Rev * (365 / sim_days)
    if fleet_capacity_mwh > 0:
        norm_rev = total_revenue / fleet_capacity_mwh
        annualized_rev_per_mwh = norm_rev * (365 / sim_days)
    else:
        annualized_rev_per_mwh = 0.0
    
    return {
        "revenue": total_revenue,
        "charged_mwh": total_charged_mwh,
        "discharged_mwh": total_discharged_mwh,
        "cycles": equivalent_cycles,
        "annualized_rev_per_mwh": annualized_rev_per_mwh
    }

def plot_prices(prices_df: pd.DataFrame, charge_thresh: float, discharge_thresh: float):
    """
    Plot Price vs Time with threshold lines.
    """
    fig = px.line(prices_df, x='timestamp', y='price_mwh', title='Market Prices ($/MWh)')
    
    fig.add_hline(y=charge_thresh, line_dash="dash", line_color="green", annotation_text="Charge Threshold")
    fig.add_hline(y=discharge_thresh, line_dash="dash", line_color="red", annotation_text="Discharge Threshold")
    
    fig.update_layout(xaxis_title="Time", yaxis_title="Price ($/MWh)", template="plotly_white")
    return fig

def plot_soe(results_df: pd.DataFrame):
    """
    Plot State of Energy for all batteries.
    """
    fig = px.line(results_df, x='timestamp', y='soe_after', color='battery_id', 
                  title='State of Energy (MWh)', labels={'soe_after': 'SoE (MWh)'})
    fig.update_layout()
    return fig

def plot_revenue_cumulative(results_df: pd.DataFrame):
    """
    Combined chart: Interval Revenue (Bar) + Cumulative Revenue (Line).
    """
    # Aggregate revenue by timestamp
    daily_rev = results_df.groupby('timestamp')['revenue'].sum().reset_index()
    daily_rev['cumulative_revenue'] = daily_rev['revenue'].cumsum()
    
    fig = go.Figure()
    
    # 1. Interval Revenue (Bar - Primary Left)
    fig.add_trace(go.Bar(
        x=daily_rev['timestamp'],
        y=daily_rev['revenue'],
        name="Interval Revenue ($)",
        yaxis="y",
        marker_color="lightblue",
        opacity=0.7
    ))
    
    # 2. Cumulative Revenue (Line - Secondary Right)
    fig.add_trace(go.Scatter(
        x=daily_rev['timestamp'],
        y=daily_rev['cumulative_revenue'],
        name="Cumulative Revenue ($)",
        yaxis="y2",
        line=dict(color="darkblue", width=3)
    ))
    
    # Layout
    fig.update_layout(
        title="Revenue Performance",
        xaxis_title="Time",
        yaxis=dict(
            title="Interval Revenue ($)",
            side="left"
        ),
        yaxis2=dict(
            title="Cumulative Revenue ($)",
            side="right",
            overlaying="y",
            showgrid=False
        ),
        legend=dict(orientation="h", y=1.1),
        height=500
    )
    return fig

def plot_dispatch_and_price(results_df: pd.DataFrame, charge_thresh: float, discharge_thresh: float):
    """
    Combined chart: Price (Left/Primary) + Stacked Bar for Dispatch (Right/Secondary).
    """
    fig = go.Figure()
    
    # 1. Price Line (Primary Axis - Left)
    # Extract unique price curve
    prices = results_df[['timestamp', 'price']].drop_duplicates().sort_values('timestamp')
    
    fig.add_trace(go.Scatter(
        x=prices['timestamp'],
        y=prices['price'],
        name="Price ($/MWh)",
        line=dict(width=3), # Use default color cycle, or specify a theme-friendly one like 'purple'
        yaxis="y" 
    ))
    
    # 2. Stacked Bars for Fleet Dispatch (Secondary Axis - Right)
    batteries = results_df['battery_id'].unique()
    for bat_id in batteries:
        bat_data = results_df[results_df['battery_id'] == bat_id]
        fig.add_trace(go.Bar(
            x=bat_data['timestamp'],
            y=bat_data['mw'],
            name=f"{bat_id} (MW)",
            yaxis="y2",
            opacity=0.7 # Slight transparency to see price line if overlap
        ))
    
    # Threshold Lines (Price Axis - y)
    fig.add_hline(y=charge_thresh, line_dash="dash", line_color="green", annotation_text="Charge", row="all", col="all", yref="y")
    fig.add_hline(y=discharge_thresh, line_dash="dash", line_color="red", annotation_text="Discharge", row="all", col="all", yref="y")

    # Layout
    fig.update_layout(
        title="Market Prices & Fleet Dispatch",
        xaxis_title="Time",
        yaxis=dict(
            title="Price ($/MWh)",
            side="left"
        ),
        yaxis2=dict(
            title="Fleet Power (MW)",
            side="right",
            overlaying="y",
            showgrid=False
        ),
        barmode='relative',
        legend=dict(orientation="h", y=1.1),
        height=500,
        # Remove template="plotly_white" to respect Streamlit theme
    )
    
    return fig

def plot_individual_battery_analysis(results_df: pd.DataFrame, battery_id: str):
    """
    Dual-axis chart for a SPECIFIC battery:
    - Primary Y (Left): Dispatch MW (Bar).
    - Secondary Y (Right): SoE MWh (Line).
    """
    bat_data = results_df[results_df['battery_id'] == battery_id]
    
    fig = go.Figure()
    
    # 1. Dispatch MW (Bar - Left Axis)
    fig.add_trace(go.Bar(
        x=bat_data['timestamp'],
        y=bat_data['mw'],
        name="Dispatch (MW)",
        yaxis="y",
        marker_color="teal",
        opacity=0.6
    ))
    
    # 2. SoE (Line - Right Axis)
    fig.add_trace(go.Scatter(
        x=bat_data['timestamp'],
        y=bat_data['soe_after'],
        name="State of Energy (MWh)",
        yaxis="y2",
        line=dict(color="orange", width=3)
    ))
    
    # Layout
    fig.update_layout(
        title=f"Analysis: {battery_id}",
        xaxis_title="Time",
        yaxis=dict(
            title="Dispatch (MW)",
            side="left"
        ),
        yaxis2=dict(
            title="State of Energy (MWh)",
            side="right",
            overlaying="y",
            showgrid=False
        ),
        legend=dict(orientation="h", y=1.1),
        height=500
    )
    
    return fig

def plot_revenue_pie_chart(results_df: pd.DataFrame):
    """
    Pie chart of total revenue contribution by battery.
    """
    bat_rev = results_df.groupby('battery_id')['revenue'].sum().reset_index()
    
    fig = px.pie(bat_rev, values='revenue', names='battery_id', 
                 title='Revenue Contribution by Battery',
                 hole=0.4) # Donut chart style
    fig.update_traces(textinfo='percent+label')
    return fig

def plot_battery_performance_table(results_df: pd.DataFrame, batteries_cfg: list):
    """
    Table showing static params + dynamic performance (Total Revenue).
    """
    # 1. Calc Revenue per battery
    bat_rev = results_df.groupby('battery_id')['revenue'].sum().reset_index()
    bat_rev.rename(columns={'revenue': 'Total Revenue ($)'}, inplace=True)
    
    # 2. Prepare Config Data
    config_data = []
    for b in batteries_cfg:
        config_data.append({
            'battery_id': b['id'],
            'Capacity (MWh)': b['capacity_mwh'],
            'Max Charge (MW)': b['charge_rate_mw'],
            'Max Discharge (MW)': b['discharge_rate_mw'],
            'Efficiency': b['efficiency']
        })
    config_df = pd.DataFrame(config_data)
    
    # 3. Merge
    final_df = pd.merge(config_df, bat_rev, on='battery_id', how='left')
    final_df['Total Revenue ($)'] = final_df['Total Revenue ($)'].fillna(0).apply(lambda x: f"${x:,.2f}")
    
    # 4. Create Plotly Table
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(final_df.columns),
                    align='left'),
        cells=dict(values=[final_df[k].tolist() for k in final_df.columns],
                   align='left'))
    ])
    
    fig.update_layout(title="Asset Performance Summary", height=300)
    return fig

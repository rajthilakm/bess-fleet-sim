import os
import yaml
import logging
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

from sim_engine.fleet import Fleet
from sim_engine.price_engine import PriceEngine
from sim_engine.optimizer import Optimizer

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    load_dotenv("config/.env")
    
    with open("config/batteries.yaml", "r") as f:
        full_config = yaml.safe_load(f)
        
    return full_config, os.environ

def main():
    logger.info("Starting Battery Fleet Simulation...")
    
    # 1. Load Config
    full_config, env = load_config()
    batteries_cfg = full_config['batteries']
    fleet_global_cfg = full_config.get('fleet_global', {})
    logger.info(f"Loaded {len(batteries_cfg)} batteries.")
    
    # 2. Initialize Models
    fleet = Fleet(batteries_cfg)
    price_engine = PriceEngine()
    optimizer = Optimizer(fleet)
    
    # Parse Resolution
    resolution_str = env.get('MARKET_RESOLUTION', '60min').replace('T', 'min')
    duration_hours = pd.to_timedelta(resolution_str).total_seconds() / 3600.0
    logger.info(f"Market Resolution: {resolution_str} ({duration_hours:.2f} hours)")
    
    # 3. Generate Prices
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    prices_df = price_engine.generate_prices(start_date, days=7, resolution=resolution_str)
    prices_df.to_csv("./simulation_results/prices.csv", index=False)
    logger.info(f"Generated {len(prices_df)} price points.")
    
    # 4. Run Optimization
    logger.info("Running Threshold Strategy...")
    results_df = optimizer.run_threshold_strategy(
        prices_df,
        charge_threshold=100.0,
        discharge_threshold=150.0,
        fleet_max_charge=float(fleet_global_cfg.get('max_charge_mw', 100)),
        fleet_max_discharge=float(fleet_global_cfg.get('max_discharge_mw', 100)),
        duration_hours=duration_hours
    )

    results_df.to_csv("./simulation_results/results.csv", index=False)
    # 5. Summary
    total_revenue = results_df['revenue'].sum()
    total_charged = abs(results_df[results_df['mw'] < 0]['mw'].sum())
    total_discharged = results_df[results_df['mw'] > 0]['mw'].sum()
    
    print("\n" + "="*40)
    print("SIMULATION RESULTS SUMMARY")
    print("="*40)
    print(f"Total Revenue:       ${total_revenue:,.2f}")
    print(f"Total Energy Charged:    {total_charged:.2f} MWh")
    print(f"Total Energy Discharged: {total_discharged:.2f} MWh")
    print("-" * 40)
    print("Final State of Energy:")
    for status in fleet.get_status():
        print(f"  {status['id']}: {status['soe_mwh']:.2f} MWh ({status['soe_perc']:.1f}%)")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()

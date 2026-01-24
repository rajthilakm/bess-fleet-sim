import pandas as pd
from sim_engine.fleet import Fleet
from sim_engine.revenue import calculate_revenue

class Optimizer:
    def __init__(self, fleet: Fleet):
        self.fleet = fleet
        
    def run_threshold_strategy(self, prices_df: pd.DataFrame, 
                               charge_threshold: float, 
                               discharge_threshold: float,
                               fleet_max_charge: float,
                               fleet_max_discharge: float,
                               duration_hours: float = 1.0) -> pd.DataFrame:
        """
        Run simple threshold strategy.
        """
        results = []
        prices_df = prices_df.sort_values("timestamp")
        
        for _, row in prices_df.iterrows():
            step_results = self._process_timestep(
                row['timestamp'], row['price_mwh'],
                charge_threshold, discharge_threshold,
                fleet_max_charge, fleet_max_discharge,
                duration_hours
            )
            results.extend(step_results)
                
        return pd.DataFrame(results)

    def _process_timestep(self, ts, price, charge_thresh, discharge_thresh, 
                          fleet_max_charge, fleet_max_discharge, duration_hours):
        """Process a single timestep for the fleet."""
        is_charge = price < charge_thresh
        is_discharge = price > discharge_thresh
        
        sorted_batteries = self._get_prioritized_batteries(is_charge, is_discharge)
        
        step_results = []
        current_fleet_mw = 0.0
        
        for battery in sorted_batteries:
            result, realized_mw = self._dispatch_single_battery(
                battery, ts, price, is_charge, is_discharge, 
                current_fleet_mw, fleet_max_charge, fleet_max_discharge, 
                duration_hours
            )
            step_results.append(result)
            current_fleet_mw += realized_mw
            
        return step_results

    def _get_prioritized_batteries(self, is_charge: bool, is_discharge: bool):
        """Sort batteries based on priority logic."""
        if is_charge:
            # Priority: Max Charge Rate, Max Capacity, Lowest SoE
            return sorted(
                self.fleet.batteries,
                key=lambda b: (b.max_charge_mw, b.capacity_mwh, -b.soe_mwh),
                reverse=True
            )
        elif is_discharge:
            # Priority: Max Discharge Rate, Max Capacity, Highest SoE
            return sorted(
                self.fleet.batteries,
                key=lambda b: (b.max_discharge_mw, b.capacity_mwh, b.soe_mwh),
                reverse=True
            )
        return self.fleet.batteries

    def _dispatch_single_battery(self, battery, ts, price, is_charge, is_discharge, 
                                 current_fleet_mw, fleet_max_charge, fleet_max_discharge, 
                                 duration_hours):
        """Calculate dispatch for a single battery and update its state."""
        desired = 0.0
        if is_charge:
            desired = -battery.max_charge_mw
        elif is_discharge:
            desired = battery.max_discharge_mw
            
        # Apply Fleet Constraint
        action_mw = self._apply_fleet_constraints(
            desired, current_fleet_mw, fleet_max_charge, fleet_max_discharge
        )
        
        # Execute Dispatch
        soe_before = battery.soe_mwh
        realized_mw = battery.update_soe(action_mw, duration_hours=duration_hours)
        soe_after = battery.soe_mwh
        
        revenue = calculate_revenue(realized_mw, price, duration_hours)
        
        result = {
            "timestamp": ts,
            "battery_id": battery.id,
            "action": "CHARGE" if realized_mw < 0 else "DISCHARGE" if realized_mw > 0 else "IDLE",
            "mw": realized_mw,
            "price": price,
            "revenue": revenue,
            "soe_before": soe_before,
            "soe_after": soe_after
        }
        
        return result, realized_mw

    def _apply_fleet_constraints(self, desired, current_fleet_mw, max_charge, max_discharge):
        """Clamp desired MW based on remaining fleet capacity."""
        if desired < 0: # Charging
            remaining = max_charge - abs(current_fleet_mw)
            return max(desired, -remaining) if remaining > 0 else 0.0
        elif desired > 0: # Discharging
            remaining = max_discharge - abs(current_fleet_mw)
            return min(desired, remaining) if remaining > 0 else 0.0
        return 0.0

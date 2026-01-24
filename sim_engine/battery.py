import logging

class Battery:
    """
    Represents a Battery Energy Storage System (BESS).
    
    Physics Model (Grid-Side MW convention):
    - MW is defined at the Grid Connection Point (GCP).
    - Charging (MW < 0): Energy entering battery = abs(MW) * efficiency
    - Discharging (MW > 0): Energy leaving battery = abs(MW) / efficiency
    """
    
    def __init__(self, config: dict):
        self.id = config['id']
        self.capacity_mwh = float(config['capacity_mwh'])
        self.max_charge_mw = float(config['charge_rate_mw'])
        self.max_discharge_mw = float(config['discharge_rate_mw'])
        self.efficiency = float(config['efficiency'])
        
        if 'initial_soe_pct' in config:
            self.soe_mwh = self.capacity_mwh * (float(config['initial_soe_pct']) / 100.0)
        else:
            self.soe_mwh = float(config.get('initial_soe_mwh', self.capacity_mwh * 0.5))
        
    def update_soe(self, mw: float, duration_hours: float = 1.0) -> float:
        """
        Update State of Energy based on power dispatch.
        
        Args:
            mw (float): Power in MW. Negative = Charge, Positive = Discharge.
            duration_hours (float): Time interval in hours.
            
        Returns:
            float: The actual MW dispatched (clamped by constraints).
        """
        # 1. Check constraints
        feasible_mw = self.check_constraints(mw, duration_hours)
        
        # 2. Physics Update
        if feasible_mw < 0: # Charging
            energy_in = abs(feasible_mw) * duration_hours * self.efficiency
            self.soe_mwh += energy_in
        elif feasible_mw > 0: # Discharging
            energy_out = abs(feasible_mw) * duration_hours / self.efficiency
            self.soe_mwh -= energy_out
            
        # Clamp SoE (floating point correction)
        self.soe_mwh = max(0.0, min(self.capacity_mwh, self.soe_mwh))
        
        return feasible_mw

    def check_constraints(self, target_mw: float, duration_hours: float = 1.0) -> float:
        """
        Check if target MW is feasible given current SoE and Rate limits.
        Returns the feasible MW.
        """
        # Rate Constraints
        if target_mw < 0: # Charging
            limit = -self.max_charge_mw
            feasible_mw = max(limit, target_mw)
            
            # SoE Capacity Constraint
            # Max energy we can add = (Capacity - Current)
            # Energy added = MW * t * eff
            # MW_max_energy = (Cap - Cur) / (t * eff)
            max_energy_space = self.capacity_mwh - self.soe_mwh
            max_charge_power_energy = - (max_energy_space / (duration_hours * self.efficiency))
            
            # Apply strictest limit (closest to 0)
            feasible_mw = max(feasible_mw, max_charge_power_energy)

        elif target_mw > 0: # Discharging
            limit = self.max_discharge_mw
            feasible_mw = min(limit, target_mw)
            
            # SoE Content Constraint
            # Max energy we can draw = Current SoE
            # Energy drawn = MW * t / eff
            # MW_max_energy = Current * eff / t
            max_discharge_power_energy = (self.soe_mwh * self.efficiency) / duration_hours
            
            # Apply strictest limit
            feasible_mw = min(feasible_mw, max_discharge_power_energy)
            
        else:
            feasible_mw = 0.0
            
        return feasible_mw

    def __repr__(self):
        return f"Battery({self.id}, SoE={self.soe_mwh:.2f}MWh)"

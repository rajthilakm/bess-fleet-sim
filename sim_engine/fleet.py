from typing import List, Dict
from sim_engine.battery import Battery

class Fleet:
    def __init__(self, batteries_config: List[Dict]):
        self.batteries = [Battery(b) for b in batteries_config]
        
    @property
    def count(self):
        return len(self.batteries)

    @property
    def total_capacity(self):
        return sum(b.capacity_mwh for b in self.batteries)
        
    @property
    def current_soe(self):
        return sum(b.soe_mwh for b in self.batteries)
    
    @property
    def agg_charge_rate(self):
        return sum(b.max_charge_mw for b in self.batteries)
    
    @property
    def agg_discharge_rate(self):
        return sum(b.max_discharge_mw for b in self.batteries)
        
    def dispatch(self, battery_id: str, mw: float, duration_hours: float = 1.0) -> float:
        """
        Dispatch a specific battery.
        """
        for b in self.batteries:
            if b.id == battery_id:
                return b.update_soe(mw, duration_hours)
        raise ValueError(f"Battery {battery_id} not found")
        
    def get_status(self) -> List[Dict]:
        return [
            {
                "id": b.id,
                "soe_mwh": b.soe_mwh,
                "soe_perc": (b.soe_mwh / b.capacity_mwh * 100) if b.capacity_mwh > 0 else 0.0
            }
            for b in self.batteries
        ]

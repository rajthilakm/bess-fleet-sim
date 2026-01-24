import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PriceEngine:
    def __init__(self):
        pass
        
    def generate_prices(self, start_date: datetime, days: int = 7, resolution: str = "60min",
                        base_price: float = 80.0, peak_multiplier: float = 2.0) -> pd.DataFrame:
        """
        Generate synthetic prices for N days with specific resolution and params.
        """
        timestamps = []
        prices = []
        
        step = pd.to_timedelta(resolution)
        current_time = start_date
        end_time = start_date + timedelta(days=days)
        
        while current_time < end_time:
            hour = current_time.hour
            price_noise = np.random.uniform(-10, 10)
            
            # multiplier logic
            multiplier = 1.0
            if 7 <= hour < 9: # Morning Peak (Simulated)
                multiplier = 1.8 * (peak_multiplier / 2.0) # Scale roughly
            elif 17 <= hour < 21: # Evening Peak
                multiplier = peak_multiplier
            
            final_price = (base_price * multiplier) + price_noise
            # Clamp to range
            final_price = max(50.0, min(250.0, final_price))
            
            timestamps.append(current_time)
            prices.append(round(final_price, 2))
            
            current_time += step
            
        return pd.DataFrame({
            "timestamp": timestamps,
            "price_mwh": prices
        })

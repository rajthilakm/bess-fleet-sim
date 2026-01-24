def calculate_revenue(mw: float, price_mwh: float, duration_hours: float = 1.0) -> float:
    """
    Calculate revenue for a dispatch.
    
    Args:
        mw (float): Signed Power (Negative = Charge/Buy, Positive = Discharge/Sell)
        price_mwh (float): Price in $/MWh
        
    Returns:
        float: Revenue in $ (Negative = Cost, Positive = Income)
    """
    return mw * price_mwh * duration_hours

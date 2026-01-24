import pytest
from sim_engine.revenue import calculate_revenue

def test_revenue_discharge():
    # Selling power (positive MW) at positive price
    mw = 10.0
    price = 100.0
    assert calculate_revenue(mw, price) == 1000.0

def test_revenue_charge():
    # Buying power (negative MW) at positive price = Cost (negative revenue)
    mw = -10.0
    price = 50.0
    assert calculate_revenue(mw, price) == -500.0

def test_revenue_negative_price_charge():
    # Buying power at negative price = Earn money to consume
    mw = -10.0
    price = -20.0
    assert calculate_revenue(mw, price) == 200.0

def test_revenue_zero_mw():
    assert calculate_revenue(0, 100) == 0.0

def test_revenue_duration():
    mw = 10.0
    price = 100.0
    duration = 0.5
    assert calculate_revenue(mw, price, duration) == 500.0

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_monitor.monitor import (
    get_db_connection,
    get_current_stock,
    simulate_daily_consumption,
    check_threshold_breach
)

# ============ DATABASE TESTS ============
def test_get_db_connection():
    conn = get_db_connection()
    assert conn is not None
    conn.close()

# ============ STOCK TESTS ============
def test_get_current_stock():
    stock = get_current_stock()
    assert stock is not None
    assert 'current_stock' in stock
    assert 'daily_consumption' in stock

def test_get_current_stock_hospital_c():
    stock = get_current_stock()
    assert stock['daily_consumption'] == 79

# ============ CONSUMPTION TESTS ============
def test_simulate_daily_consumption():
    result = simulate_daily_consumption(100)
    assert result > 0
    assert result < 200  # With spike max 150

def test_simulate_daily_consumption_zero():
    result = simulate_daily_consumption(0)
    assert result == 0

def test_simulate_daily_consumption_never_negative():
    for _ in range(20):
        result = simulate_daily_consumption(50)
        assert result >= 0

# ============ THRESHOLD TESTS ============
def test_check_threshold_breach():
    breach, data = check_threshold_breach()
    assert isinstance(breach, bool)
    if breach:
        assert data is not None
        assert 'current_stock' in data
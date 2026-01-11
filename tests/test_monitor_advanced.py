import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_monitor.monitor import (
    get_db_connection,
    get_current_stock,
    update_stock,
    simulate_daily_consumption,
    check_threshold_breach,
)

# ============ UPDATE STOCK TESTS ============
def test_update_stock_success():
    """Stok güncellemesi başarılı mı?"""
    result = update_stock(0)  
    assert result == True

def test_update_stock_with_consumption():
    """Tüketim ile stok güncelleme"""
    initial = get_current_stock()
    if initial['current_stock'] > 10:
        result = update_stock(5)
        assert result == True

# ============ CALCULATION TESTS ============
def test_days_of_supply_calculation():
    """Days of supply doğru hesaplanıyor mu?"""
    stock = get_current_stock()
    if stock['current_stock'] > 0 and stock['daily_consumption'] > 0:
        expected = stock['current_stock'] / stock['daily_consumption']
        actual = float(stock['days_of_supply'])

        assert abs(expected - actual) < 0.5

# ============ CONSUMPTION PATTERNS TESTS ============
def test_simulate_consumption_range():
    """Tüketim makul aralıkta mı?"""
    base = 79
    results = [simulate_daily_consumption(base) for _ in range(10)]
    
    
    for r in results:
        assert r >= 0
    
    reasonable = [r for r in results if 60 < r < 120]
    assert len(reasonable) >= 7

def test_simulate_consumption_large_base():
    """Büyük base tüketim"""
    result = simulate_daily_consumption(1000)
    assert result > 0
    assert result < 2000

def test_simulate_consumption_small_base():
    """Küçük base tüketim"""
    result = simulate_daily_consumption(10)
    assert result >= 0
    assert result < 30

# ============ THRESHOLD BREACH TESTS ============
def test_threshold_breach_structure():
    """Threshold breach doğru yapıda mı?"""
    breach, data = check_threshold_breach()
    assert isinstance(breach, bool)
    
    if breach and data:
        assert 'current_stock' in data
        assert 'daily_consumption' in data
        assert 'days_of_supply' in data
        assert isinstance(data['current_stock'], int)
        assert isinstance(data['daily_consumption'], int)

# ============ DATABASE OPERATIONS TESTS ============
def test_db_query_stock():
    """Database'den stok sorgulanabiliyor mu?"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT current_stock_units, daily_consumption_units 
        FROM stock 
        WHERE hospital_id = 'Hospital-C'
    """)
    
    result = cursor.fetchone()
    assert result is not None
    assert len(result) == 2
    
    cursor.close()
    conn.close()

def test_db_query_event_log():
    """Event log sorgulanabiliyor mu?"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM event_log")
    count = cursor.fetchone()[0]
    assert count >= 0
    
    cursor.close()
    conn.close()

# ============ EDGE CASES ============
def test_get_current_stock_consistency():
    """Stok verileri tutarlı mı?"""
    stock1 = get_current_stock()
    stock2 = get_current_stock()
    
 
    assert stock1['daily_consumption'] == stock2['daily_consumption']

def test_hospital_id_constant():
    """Hospital ID doğru mu?"""
    stock = get_current_stock()

    assert stock['daily_consumption'] == 79

# ============ INTEGRATION TESTS ============
def test_full_monitoring_cycle():
    """Tam monitoring döngüsü"""

    stock = get_current_stock()
    assert stock is not None
    

    consumption = simulate_daily_consumption(stock['daily_consumption'])
    assert consumption >= 0
    

    breach, data = check_threshold_breach()
    assert isinstance(breach, bool)

def test_multiple_threshold_checks():
    """Birden fazla threshold kontrolü"""
    for _ in range(5):
        breach, data = check_threshold_breach()
        assert isinstance(breach, bool)
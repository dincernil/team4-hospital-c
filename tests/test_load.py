import requests
import time

def test_stockms_load():
    """Load test StockMS"""
    success = 0
    fail = 0
    
    for i in range(30):
        try:
            r = requests.get("http://localhost:8081/health", timeout=2)
            if r.status_code == 200:
                success += 1
            else:
                fail += 1
        except:
            fail += 1
        time.sleep(0.1)
    
    assert success > 25  
    print(f"Success: {success}, Fail: {fail}")

def test_orderms_load():
    """Load test OrderMS"""
    success = 0
    fail = 0
    
    for i in range(30):
        try:
            r = requests.get("http://localhost:8082/health", timeout=2)
            if r.status_code == 200:
                success += 1
            else:
                fail += 1
        except:
            fail += 1
        time.sleep(0.1)
    
    assert success > 25  # En az 25/30 başarılı
    print(f"Success: {success}, Fail: {fail}")
import requests
import pytest

def test_orderms_health():
    """OrderMS health check"""
    r = requests.get("http://localhost:8082/health")
    assert r.status_code == 200
    assert r.json()["status"] == "UP"

def test_orderms_receive_order():
    """OrderMS receive order"""
    import time
    order = {
        "commandId": f"CMD-TEST-{int(time.time())}",
        "orderId": f"ORD-TEST-{int(time.time())}",
        "hospitalId": "Hospital-C",
        "productCode": "PHYSIO-SALINE-500ML",
        "orderQuantity": 200,
        "priority": "HIGH",
        "estimatedDeliveryDate": "2026-01-08T10:00:00",
        "warehouseId": "CENTRAL-WAREHOUSE"
    }
    r = requests.post("http://localhost:8082/receive-order", json=order)
    assert r.status_code == 200
    assert r.json()["success"] == True
import requests
import pytest

def test_stockms_health():
    """StockMS health check"""
    r = requests.get("http://localhost:8081/health")
    assert r.status_code == 200
    assert r.json()["status"] == "UP"

def test_stockms_publish_event():
    """StockMS event publishing"""
    r = requests.post("http://localhost:8081/publish-event")
    assert r.status_code == 200
    assert r.json()["success"] == True
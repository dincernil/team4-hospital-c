import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from soap_client.client import (
    get_db_connection,
    get_current_stock,
    create_soap_envelope,
    parse_soap_response,
    log_event
)

# =========================
# DATABASE TESTS
# =========================

def test_get_db_connection():
    conn = get_db_connection()
    assert conn is not None
    conn.close()


def test_get_db_connection_failure(monkeypatch):
    """Coverage booster – DB connection failure"""
    import soap_client.client as client

    monkeypatch.setattr(
        client.psycopg2,
        "connect",
        lambda **kw: (_ for _ in ()).throw(Exception("DB error"))
    )

    conn = client.get_db_connection()
    assert conn is None


# =========================
# STOCK TESTS
# =========================

def test_get_current_stock():
    stock = get_current_stock()
    assert stock is not None
    assert 'currentStockUnits' in stock
    assert 'dailyConsumptionUnits' in stock
    assert 'daysOfSupply' in stock


def test_get_current_stock_hospital_c():
    stock = get_current_stock()
    assert stock['dailyConsumptionUnits'] == 79


def test_get_current_stock_none_db(monkeypatch):
    """Coverage booster – db returns None"""
    import soap_client.client as client
    monkeypatch.setattr(client, "get_db_connection", lambda: None)

    stock = client.get_current_stock()
    assert stock is None


# =========================
# SOAP ENVELOPE TESTS
# =========================

def test_create_soap_envelope():
    data = {'currentStockUnits': 100, 'dailyConsumptionUnits': 50, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    assert envelope is not None
    assert '<?xml' in envelope
    assert 'Hospital-C' in envelope
    assert 'PHYSIO-SALINE-500ML' in envelope


def test_create_soap_envelope_contains_data():
    data = {'currentStockUnits': 123, 'dailyConsumptionUnits': 45, 'daysOfSupply': 2.73}
    envelope = create_soap_envelope(data)
    assert '123' in envelope
    assert '45' in envelope





# =========================
# SOAP PARSING TESTS
# =========================

def test_parse_soap_response_success():
    xml = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap">
                <tns:success>true</tns:success>
                <tns:message>Order created</tns:message>
                <tns:orderTriggered>true</tns:orderTriggered>
                <tns:orderId>ORD-123</tns:orderId>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    result = parse_soap_response(xml)
    assert result['success'] is True
    assert result['orderId'] == 'ORD-123'


def test_parse_soap_response_no_order():
    xml = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>Stock sufficient</tns:message>
                <tns:orderTriggered>false</tns:orderTriggered>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    result = parse_soap_response(xml)
    assert result['orderTriggered'] is False
    assert result['orderId'] is None


def test_parse_soap_response_invalid():
    """Coverage booster – invalid XML safe path"""
    result = parse_soap_response("invalid xml")
    assert result['success'] is False


def test_parse_soap_response_none():
    """Coverage booster – None XML"""
    result = parse_soap_response(None)
    assert result['success'] is False


# =========================
# LOGGING TESTS
# =========================

def test_log_event():
    log_event('TEST', 'SUCCESS', 'payload', None, 100)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM event_log WHERE event_type = 'TEST'")
    count = cursor.fetchone()[0]

    assert count > 0
    cursor.close()
    conn.close()


def test_log_event_db_fail(monkeypatch):
    """Coverage booster – logging DB failure should not crash"""
    import soap_client.client as client

    monkeypatch.setattr(client, "get_db_connection", lambda: None)

    # should NOT raise
    client.log_event('FAIL', 'ERROR', 'payload', None, 0)


# =========================
# COVERAGE BOOSTERS (SAFE)
# =========================

def test_parse_soap_response_missing_tags():
    """Coverage booster – missing XML tags"""
    xml = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap">
                <tns:success>true</tns:success>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    result = parse_soap_response(xml)
    assert result["success"] is True



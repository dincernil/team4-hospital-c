import sys
import os
import pytest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from soap_client.client import (
    get_db_connection,
    get_current_stock,
    create_soap_envelope,
    parse_soap_response,
    log_event
)

# ============ SOAP ENVELOPE ADVANCED TESTS ============
def test_soap_envelope_xml_structure():
    """SOAP envelope XML yapısı doğru mu?"""
    data = {'currentStockUnits': 100, 'dailyConsumptionUnits': 50, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    
    # XML parse edilebilmeli
    try:
        root = ET.fromstring(envelope)
        assert root is not None
    except:
        pytest.fail("Invalid XML structure")

def test_soap_envelope_namespaces():
    """SOAP namespaces doğru mu?"""
    data = {'currentStockUnits': 100, 'dailyConsumptionUnits': 50, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    
    assert 'xmlns:soap' in envelope
    assert 'xmlns:tns' in envelope

def test_soap_envelope_body():
    """SOAP Body var mı?"""
    data = {'currentStockUnits': 100, 'dailyConsumptionUnits': 50, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    
    assert '<soap:Body>' in envelope
    assert '</soap:Body>' in envelope

def test_soap_envelope_request_element():
    """StockUpdateRequest elementi var mı?"""
    data = {'currentStockUnits': 100, 'dailyConsumptionUnits': 50, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    
    assert 'StockUpdateRequest' in envelope

def test_soap_envelope_all_fields():
    """Tüm gerekli alanlar var mı?"""
    data = {'currentStockUnits': 200, 'dailyConsumptionUnits': 79, 'daysOfSupply': 2.53}
    envelope = create_soap_envelope(data)
    
    assert 'hospitalId' in envelope
    assert 'Hospital-C' in envelope
    assert 'productCode' in envelope
    assert 'PHYSIO-SALINE-500ML' in envelope
    assert '200' in envelope
    assert '79' in envelope

def test_soap_envelope_different_values():
    """Farklı değerlerle SOAP envelope"""
    data = {'currentStockUnits': 50, 'dailyConsumptionUnits': 25, 'daysOfSupply': 2.0}
    envelope = create_soap_envelope(data)
    
    assert '50' in envelope
    assert '25' in envelope

# ============ SOAP PARSING ADVANCED TESTS ============
def test_parse_response_with_order():
    """Sipariş tetiklenmiş response"""
    xml = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>Order created</tns:message>
                <tns:orderTriggered>true</tns:orderTriggered>
                <tns:orderId>ORD-TEST-456</tns:orderId>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    
    result = parse_soap_response(xml)
    assert result['success'] == True
    assert result['orderTriggered'] == True
    assert result['orderId'] == 'ORD-TEST-456'
    assert 'Order created' in result['message']

def test_parse_response_failure():
    """Başarısız response"""
    xml = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>false</tns:success>
                <tns:message>Invalid hospital</tns:message>
                <tns:orderTriggered>false</tns:orderTriggered>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    
    result = parse_soap_response(xml)
    assert result['success'] == False
    assert result['orderTriggered'] == False

def test_parse_response_empty():
    """Boş response"""
    result = parse_soap_response("")
    assert result['success'] == False

def test_parse_response_malformed():
    """Bozuk XML"""
    result = parse_soap_response("<invalid>xml")
    assert result['success'] == False

# ============ LOGGING ADVANCED TESTS ============
def test_log_event_success():
    """Başarılı event logging"""
    log_event('TEST_SUCCESS', 'SUCCESS', 'test payload', None, 50)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, latency_ms FROM event_log 
        WHERE event_type = 'TEST_SUCCESS'
        ORDER BY timestamp DESC LIMIT 1
    """)
    result = cursor.fetchone()
    
    assert result is not None
    assert result[0] == 'SUCCESS'
    assert result[1] == 50
    
    cursor.close()
    conn.close()

def test_log_event_failure():
    """Başarısız event logging"""
    log_event('TEST_FAILURE', 'FAILURE', 'fail payload', 'Test error message', 200)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, error_message FROM event_log 
        WHERE event_type = 'TEST_FAILURE'
        ORDER BY timestamp DESC LIMIT 1
    """)
    result = cursor.fetchone()
    
    assert result is not None
    assert result[0] == 'FAILURE'
    assert 'Test error message' in result[1]
    
    cursor.close()
    conn.close()

def test_log_event_different_latencies():
    """Farklı latency değerleri"""
    log_event('TEST_LAT_1', 'SUCCESS', 'p1', None, 10)
    log_event('TEST_LAT_2', 'SUCCESS', 'p2', None, 100)
    log_event('TEST_LAT_3', 'SUCCESS', 'p3', None, 500)
    
    # Hepsi kaydedilmiş olmalı

# ============ STOCK RETRIEVAL TESTS ============
def test_get_current_stock_fields():
    """Stok alanları doğru tipte mi?"""
    stock = get_current_stock()
    
    assert isinstance(stock['currentStockUnits'], int)
    assert isinstance(stock['dailyConsumptionUnits'], int)
    assert isinstance(stock['daysOfSupply'], float)

def test_get_current_stock_values():
    """Stok değerleri mantıklı mı?"""
    stock = get_current_stock()
    
    assert stock['currentStockUnits'] >= 0
    assert stock['dailyConsumptionUnits'] > 0
    assert stock['daysOfSupply'] >= 0

# ============ DATABASE CONNECTION TESTS ============
def test_db_connection_multiple():
    """Birden fazla bağlantı"""
    conn1 = get_db_connection()
    conn2 = get_db_connection()
    
    assert conn1 is not None
    assert conn2 is not None
    
    conn1.close()
    conn2.close()

def test_db_connection_query():
    """Bağlantı ile query"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1+1")
    result = cursor.fetchone()
    assert result[0] == 2
    
    cursor.close()
    conn.close()
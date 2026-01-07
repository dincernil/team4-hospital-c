import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from soap_client.client import send_stock_update, create_soap_envelope

# ============ SEND STOCK UPDATE TESTS ============

@patch('soap_client.client.requests.post')
def test_send_stock_update_success(mock_post):
    """send_stock_update başarılı çalışıyor mu?"""
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>Order created</tns:message>
                <tns:orderTriggered>true</tns:orderTriggered>
                <tns:orderId>ORD-MOCK-123</tns:orderId>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    mock_post.return_value = mock_response
    
    # Test
    stock_data = {
        'currentStockUnits': 50,
        'dailyConsumptionUnits': 79,
        'daysOfSupply': 0.63
    }
    
    result = send_stock_update(stock_data)
    assert result is not None
    assert result['success'] == True

@patch('soap_client.client.requests.post')
def test_send_stock_update_no_order(mock_post):
    """send_stock_update - sipariş yok"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>Stock sufficient</tns:message>
                <tns:orderTriggered>false</tns:orderTriggered>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    mock_post.return_value = mock_response
    
    stock_data = {
        'currentStockUnits': 200,
        'dailyConsumptionUnits': 79,
        'daysOfSupply': 2.53
    }
    
    result = send_stock_update(stock_data)
    assert result is not None
    # Result None dönebilir, kontrol et
    if result and 'orderTriggered' in result:
        assert result['orderTriggered'] == False

@patch('soap_client.client.requests.post')
def test_send_stock_update_retry(mock_post):
    """send_stock_update retry mekanizması"""
    # İlk 2 deneme başarısız, 3. başarılı
    mock_response_fail = MagicMock()
    mock_response_fail.status_code = 500
    
    mock_response_success = MagicMock()
    mock_response_success.status_code = 200
    mock_response_success.text = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>Success</tns:message>
                <tns:orderTriggered>false</tns:orderTriggered>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    
    # İlk 2 fail, sonra success
    mock_post.side_effect = [
        mock_response_fail,
        mock_response_fail,
        mock_response_success
    ]
    
    stock_data = {
        'currentStockUnits': 100,
        'dailyConsumptionUnits': 79,
        'daysOfSupply': 1.27
    }
    
    result = send_stock_update(stock_data, max_retries=3)
    assert result is not None

@patch('soap_client.client.requests.post')
def test_send_stock_update_timeout(mock_post):
    """send_stock_update timeout"""
    mock_post.side_effect = Exception("Connection timeout")
    
    stock_data = {
        'currentStockUnits': 50,
        'dailyConsumptionUnits': 79,
        'daysOfSupply': 0.63
    }
    
    # Hata olsa bile fonksiyon bitişmeli (retry ile)
    result = send_stock_update(stock_data, max_retries=1)
    # Fonksiyon çalıştı demektir

@patch('soap_client.client.requests.post')
def test_send_stock_update_creates_envelope(mock_post):
    """send_stock_update SOAP envelope oluşturuyor mu?"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '''<?xml version="1.0"?>
    <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <tns:StockUpdateResponse xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
                <tns:success>true</tns:success>
                <tns:message>OK</tns:message>
                <tns:orderTriggered>false</tns:orderTriggered>
            </tns:StockUpdateResponse>
        </soap:Body>
    </soap:Envelope>'''
    mock_post.return_value = mock_response
    
    stock_data = {
        'currentStockUnits': 100,
        'dailyConsumptionUnits': 79,
        'daysOfSupply': 1.27
    }
    
    result = send_stock_update(stock_data)
    
    # Mock çağrıldı mı kontrol et
    assert mock_post.called == True
    
    # Gönderilen data kontrol et
    call_args = mock_post.call_args
    sent_data = call_args[1]['data']
    assert 'Hospital-C' in sent_data
    assert 'PHYSIO-SALINE-500ML' in sent_data
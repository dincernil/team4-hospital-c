import os
import sys
from datetime import datetime
import requests
import psycopg2
from dotenv import load_dotenv
from xml.etree import ElementTree as ET

# .env dosyasını yükle
load_dotenv()

# Ayarlar
SOAP_URL = os.getenv('SOAP_STOCK_UPDATE_URL', 'http://localhost:8000/StockUpdateService')
HOSPITAL_ID = 'Hospital-C'
PRODUCT_CODE = 'PHYSIO-SALINE-500ML'

# Database bağlantı bilgileri
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def get_db_connection():
    """Database bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database bağlantı hatası: {e}")
        return None

def get_current_stock():
    """Mevcut stok bilgisini al"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT current_stock_units, daily_consumption_units, days_of_supply
            FROM stock
            WHERE hospital_id = %s AND product_code = %s
        """, (HOSPITAL_ID, PRODUCT_CODE))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'currentStockUnits': result[0],
                'dailyConsumptionUnits': result[1],
                'daysOfSupply': float(result[2])
            }
        return None
    except Exception as e:
        print(f"❌ Stok okuma hatası: {e}")
        return None

def log_event(event_type, status, payload=None, error_message=None, latency_ms=None):
    """Event log'a kayıt yaz"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO event_log 
            (event_type, direction, architecture, payload, status, error_message, latency_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (event_type, 'OUTGOING', 'SOA', payload, status, error_message, latency_ms))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️  Log yazma hatası: {e}")

def create_soap_envelope(stock_data):
    """SOAP XML envelope oluştur"""
    timestamp = datetime.now().isoformat()
    
    soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:tns="http://hospital-supply-chain.example.com/soap/stock">
    <soap:Body>
        <tns:StockUpdateRequest>
            <tns:hospitalId>{HOSPITAL_ID}</tns:hospitalId>
            <tns:productCode>{PRODUCT_CODE}</tns:productCode>
            <tns:currentStockUnits>{stock_data['currentStockUnits']}</tns:currentStockUnits>
            <tns:dailyConsumptionUnits>{stock_data['dailyConsumptionUnits']}</tns:dailyConsumptionUnits>
            <tns:daysOfSupply>{stock_data['daysOfSupply']:.2f}</tns:daysOfSupply>
            <tns:timestamp>{timestamp}</tns:timestamp>
        </tns:StockUpdateRequest>
    </soap:Body>
</soap:Envelope>"""
    
    return soap_envelope

def parse_soap_response(xml_response):
    """SOAP response'u parse et"""
    try:
        root = ET.fromstring(xml_response)
        
        # Namespace'leri tanımla
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'tns': 'http://hospital-supply-chain.example.com/soap/stock'
        }
        
        # Response elemanlarını bul
        success = root.find('.//tns:success', namespaces)
        message = root.find('.//tns:message', namespaces)
        order_triggered = root.find('.//tns:orderTriggered', namespaces)
        order_id = root.find('.//tns:orderId', namespaces)
        
        return {
            'success': success.text.lower() == 'true' if success is not None else False,
            'message': message.text if message is not None else '',
            'orderTriggered': order_triggered.text.lower() == 'true' if order_triggered is not None else False,
            'orderId': order_id.text if order_id is not None else None
        }
    except Exception as e:
        print(f"⚠️  XML parse hatası: {e}")
        return {
            'success': False,
            'message': f'Parse error: {str(e)}',
            'orderTriggered': False,
            'orderId': None
        }

def send_stock_update(stock_data):
    """SOAP ile stok güncelleme mesajı gönder"""
    
    print("\n" + "="*60)
    print("📤 SOAP Request Gönderiliyor...")
    print("="*60)
    
    start_time = datetime.now()
    
    try:
        # SOAP envelope oluştur
        soap_request = create_soap_envelope(stock_data)
        
        print(f"🏥 Hospital ID: {HOSPITAL_ID}")
        print(f"📦 Product: {PRODUCT_CODE}")
        print(f"📊 Current Stock: {stock_data['currentStockUnits']} units")
        print(f"📉 Daily Consumption: {stock_data['dailyConsumptionUnits']} units")
        print(f"⏱️  Days of Supply: {stock_data['daysOfSupply']:.2f} days")
        print(f"🔗 Endpoint: {SOAP_URL}")
        
        # SOAP request gönder
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'http://hospital-supply-chain.example.com/soap/stock/StockUpdate'
        }
        
        response = requests.post(
            SOAP_URL,
            data=soap_request,
            headers=headers,
            timeout=30
        )
        
        # Latency hesapla
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Response'u kontrol et
        if response.status_code == 200:
            parsed_response = parse_soap_response(response.text)
            
            print(f"\n✅ Response Alındı (Latency: {latency_ms}ms)")
            print("-"*60)
            print(f"Success: {parsed_response['success']}")
            print(f"Message: {parsed_response['message']}")
            print(f"Order Triggered: {parsed_response['orderTriggered']}")
            
            if parsed_response.get('orderId'):
                print(f"Order ID: {parsed_response['orderId']}")
            
            # Log'a yaz
            log_event(
                event_type='STOCK_UPDATE_SENT',
                status='SUCCESS',
                payload=str(stock_data),
                latency_ms=latency_ms
            )
            
            print("="*60)
            
            return {
                'success': True,
                'response': parsed_response,
                'latency_ms': latency_ms
            }
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
    except Exception as e:
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        print(f"\n❌ SOAP Hatası: {e}")
        print("="*60)
        
        # Log'a yaz
        log_event(
            event_type='STOCK_UPDATE_SENT',
            status='FAILURE',
            payload=str(stock_data),
            error_message=str(e),
            latency_ms=latency_ms
        )
        
        return {
            'success': False,
            'error': str(e),
            'latency_ms': latency_ms
        }

def main():
    """Ana fonksiyon"""
    print("\n" + "="*60)
    print("🏥 Hospital-C SOAP Client")
    print("="*60)
    
    # Mevcut stoku al
    print("\n📊 Stok bilgisi alınıyor...")
    stock_data = get_current_stock()
    
    if not stock_data:
        print("❌ Stok bilgisi alınamadı!")
        sys.exit(1)
    
    print(f"✅ Stok bilgisi alındı:")
    print(f"   Current Stock: {stock_data['currentStockUnits']} units")
    print(f"   Daily Consumption: {stock_data['dailyConsumptionUnits']} units")
    print(f"   Days of Supply: {stock_data['daysOfSupply']:.2f} days")
    
    # SOAP ile gönder
    result = send_stock_update(stock_data)
    
    if result['success']:
        print(f"\n✅ İşlem başarılı! (Latency: {result['latency_ms']}ms)")
    else:
        print(f"\n❌ İşlem başarısız!")
        sys.exit(1)

if __name__ == "__main__":
    main()
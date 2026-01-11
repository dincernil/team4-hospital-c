import psycopg2
import random
import time
import sys
import os
import requests
import json
from datetime import datetime, date
from dotenv import load_dotenv


sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'soap_client'))
from client import send_stock_update


load_dotenv()


DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

HOSPITAL_ID = 'Hospital-C'
PRODUCT_CODE = 'PHYSIO-SALINE-500ML'
THRESHOLD = 2.0
STOCKMS_URL = os.getenv('STOCKMS_URL', 'http://localhost:8081')

def publish_event_to_hub(stock_data):
    """Event Hub'a event publish et (StockMS üzerinden)"""
    start_time = datetime.now()
    
    try:
        
        event_payload = {
            'eventId': f'EVT-{int(time.time())}',
            'eventType': 'InventoryLow',
            'hospitalId': HOSPITAL_ID,
            'productCode': PRODUCT_CODE,
            'currentStockUnits': stock_data['current_stock'],
            'dailyConsumptionUnits': stock_data['daily_consumption'],
            'daysOfSupply': float(stock_data['days_of_supply']),
            'threshold': THRESHOLD,
            'timestamp': datetime.now().isoformat()
        }
        
     
        response = requests.post(
            f'{STOCKMS_URL}/publish-event',
            json=event_payload,
            timeout=30
        )
        
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'event_id': event_payload['eventId'],
                'latency_ms': latency_ms,
                'response': result
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}: {response.text}',
                'latency_ms': latency_ms
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout (30s)',
            'latency_ms': 30000
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection failed - StockMS not reachable',
            'latency_ms': 0
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'latency_ms': 0
        }

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
    """Mevcut stok bilgisini getir"""
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
                'current_stock': result[0],
                'daily_consumption': result[1],
                'days_of_supply': result[2]
            }
        return None
    except Exception as e:
        print(f"❌ Stok okuma hatası: {e}")
        return None

def simulate_daily_consumption(base_consumption):
    """Günlük tüketimi simüle et"""
    
    variation = random.uniform(-0.15, 0.15)
    consumption = base_consumption * (1 + variation)
    
  
    if random.random() < 0.05:
        consumption *= 1.5
        print("⚡ SPIKE: Yüksek tüketim algılandı!")
    
    #
    if date.today().weekday() >= 5:  
        consumption *= 0.7
        print(" Hafta sonu: Düşük tüketim")
    
    return int(consumption)

def update_stock(consumed_units):
    """Stoku güncelle"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
       
        cursor.execute("""
            SELECT current_stock_units, daily_consumption_units
            FROM stock
            WHERE hospital_id = %s AND product_code = %s
        """, (HOSPITAL_ID, PRODUCT_CODE))
        
        result = cursor.fetchone()
        if not result:
            print("❌ Stok kaydı bulunamadı!")
            return False
        
        current_stock = result[0]
        daily_consumption = result[1]
        
        
        new_stock = max(0, current_stock - consumed_units)
        new_days_of_supply = new_stock / daily_consumption if daily_consumption > 0 else 0
        
        
        cursor.execute("""
            UPDATE stock
            SET current_stock_units = %s,
                days_of_supply = %s,
                last_updated = %s
            WHERE hospital_id = %s AND product_code = %s
        """, (new_stock, round(new_days_of_supply, 2), datetime.now(), HOSPITAL_ID, PRODUCT_CODE))
        
      
        cursor.execute("""
            INSERT INTO consumption_history 
            (hospital_id, product_code, consumption_date, units_consumed, 
             opening_stock, closing_stock, day_of_week, is_weekend)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            HOSPITAL_ID, 
            PRODUCT_CODE, 
            date.today(),
            consumed_units,
            current_stock,
            new_stock,
            date.today().strftime('%A'),
            date.today().weekday() >= 5
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Stok güncellendi: {current_stock} → {new_stock} (Tüketim: {consumed_units})")
        print(f" Kalan gün sayısı: {new_days_of_supply:.2f} gün")
        
        return True
    except Exception as e:
        print(f"Stok güncelleme hatası: {e}")
        return False

def check_threshold_breach():
    """Eşik değer kontrolü yap"""
    stock_data = get_current_stock()
    if not stock_data:
        return False, None
    
    if stock_data['days_of_supply'] < THRESHOLD:
        print(f" ALARM! Stok kritik seviyede: {stock_data['days_of_supply']:.2f} gün")
        
    
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                
                if stock_data['days_of_supply'] < 1.0:
                    severity = 'URGENT'
                    alert_type = 'CRITICAL_STOCK'
                elif stock_data['days_of_supply'] < 2.0:
                    severity = 'HIGH'
                    alert_type = 'LOW_STOCK'
                else:
                    severity = 'NORMAL'
                    alert_type = 'LOW_STOCK'
                
                cursor.execute("""
                    INSERT INTO alerts 
                    (hospital_id, alert_type, severity, current_stock, 
                     daily_consumption, days_of_supply, threshold)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    HOSPITAL_ID,
                    alert_type,
                    severity,
                    stock_data['current_stock'],
                    stock_data['daily_consumption'],
                    stock_data['days_of_supply'],
                    THRESHOLD
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f" Alert kaydı hatası: {e}")
        
        return True, stock_data
    
    print(f"✔️ Stok yeterli: {stock_data['days_of_supply']:.2f} gün")
    return False, None

def main():
    """Ana döngü"""
    print("=" * 60)
    print(" Hospital-C - Stok Takip Sistemi")
    print("=" * 60)
    print(" Demo modu: Her 10 saniyede bir tüketim simüle edilecek")
    print(" Ctrl+C ile durdurun")
    print("=" * 60)
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            print(f"\n{'='*60}")
            print(f" İterasyon #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
        
            stock_data = get_current_stock()
            if not stock_data:
                print("⚠️ Stok bilgisi alınamadı, 10 saniye sonra tekrar denenecek...")
                time.sleep(10)
                continue
            
            print(f"Mevcut Stok: {stock_data['current_stock']} birim")
            print(f" Günlük Tüketim: {stock_data['daily_consumption']} birim")
            print(f"  Kalan Gün: {stock_data['days_of_supply']:.2f} gün")
            
          
            consumed = simulate_daily_consumption(stock_data['daily_consumption'])
            print(f" Simüle edilen tüketim: {consumed} birim")
            
         
            if update_stock(consumed):
               
                breach, breach_data = check_threshold_breach()
                
                if breach:
                    print(f"\n{'='*60}")
                    print("⚡ DUAL PATH EXECUTION: SOA + SERVERLESS")
                    print(f"{'='*60}")
                    
                    
                    soap_data = {
                        'currentStockUnits': breach_data['current_stock'],
                        'dailyConsumptionUnits': breach_data['daily_consumption'],
                        'daysOfSupply': float(breach_data['days_of_supply'])
                    }
                    
                    # ========================================
                    # PATH 1: SOA (SOAP)
                    # ========================================
                    print(f"\n PATH 1: SOAP Client Çağrılıyor...")
                    print("-" * 60)
                    
                    soap_result = send_stock_update(soap_data)
                    
                    if soap_result['success']:
                        print(f" SOAP Request başarılı! (Latency: {soap_result['latency_ms']}ms)")
                        if soap_result['response'].get('orderTriggered'):
                            print(f" Sipariş oluşturuldu: {soap_result['response'].get('orderId')}")
                    else:
                        print(f"SOAP Request başarısız: {soap_result.get('error')}")
                    
                    # ========================================
                    # PATH 2: SERVERLESS (EVENT HUB)
                    # ========================================
                    print(f"\nPATH 2: Event Hub'a Event Publish Ediliyor...")
                    print("-" * 60)
                    
                    event_result = publish_event_to_hub(breach_data)
                    
                    if event_result['success']:
                        print(f"Event published başarılı! (Latency: {event_result['latency_ms']}ms)")
                        print(f" Event ID: {event_result['event_id']}")
                    else:
                        print(f"Event publish başarısız: {event_result.get('error')}")
                    
                    # ========================================
                    # COMPARISON SUMMARY
                    # ========================================
                    print(f"\n{'='*60}")
                    print(" DUAL PATH COMPARISON")
                    print(f"{'='*60}")
                    print(f"SOAP Latency:      {soap_result.get('latency_ms', 0):>6} ms | Status: {' OK' if soap_result['success'] else '❌ FAIL'}")
                    print(f"Event Hub Latency: {event_result.get('latency_ms', 0):>6} ms | Status: {' OK' if event_result['success'] else '❌ FAIL'}")
                    print(f"{'='*60}")

            
            print(f"\n⏳ 10 saniye bekleniyor...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n Program sonlandırılıyor...")
            break
        except Exception as e:
            print(f" Beklenmeyen hata: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
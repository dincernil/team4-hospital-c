import psycopg2
import random
import time
import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

# soap_client'ı import et
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'soap_client'))
from client import send_stock_update

# .env dosyasını yükle
load_dotenv()

# Database bağlantı bilgileri
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

HOSPITAL_ID = 'Hospital-C'
PRODUCT_CODE = 'PHYSIO-SALINE-500ML'
THRESHOLD = 2.0

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
    # ±15% rastgele varyasyon
    variation = random.uniform(-0.15, 0.15)
    consumption = base_consumption * (1 + variation)
    
    # %5 ihtimalle %50 artış (spike)
    if random.random() < 0.05:
        consumption *= 1.5
        print("⚡ SPIKE: Yüksek tüketim algılandı!")
    
    # Hafta sonu etkisi (daha düşük tüketim)
    if date.today().weekday() >= 5:  # Cumartesi=5, Pazar=6
        consumption *= 0.7
        print("📅 Hafta sonu: Düşük tüketim")
    
    return int(consumption)

def update_stock(consumed_units):
    """Stoku güncelle"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Mevcut stoku al
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
        
        # Yeni stok değerini hesapla
        new_stock = max(0, current_stock - consumed_units)
        new_days_of_supply = new_stock / daily_consumption if daily_consumption > 0 else 0
        
        # Stoku güncelle
        cursor.execute("""
            UPDATE stock
            SET current_stock_units = %s,
                days_of_supply = %s,
                last_updated = %s
            WHERE hospital_id = %s AND product_code = %s
        """, (new_stock, round(new_days_of_supply, 2), datetime.now(), HOSPITAL_ID, PRODUCT_CODE))
        
        # Tüketim geçmişini kaydet
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
        
        print(f"✅ Stok güncellendi: {current_stock} → {new_stock} (Tüketim: {consumed_units})")
        print(f"📊 Kalan gün sayısı: {new_days_of_supply:.2f} gün")
        
        return True
    except Exception as e:
        print(f"❌ Stok güncelleme hatası: {e}")
        return False

def check_threshold_breach():
    """Eşik değer kontrolü yap"""
    stock_data = get_current_stock()
    if not stock_data:
        return False, None
    
    if stock_data['days_of_supply'] < THRESHOLD:
        print(f"🚨 ALARM! Stok kritik seviyede: {stock_data['days_of_supply']:.2f} gün")
        
        # Alert kaydı oluştur
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Severity belirle
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
                print(f"❌ Alert kaydı hatası: {e}")
        
        return True, stock_data
    
    print(f"✔️ Stok yeterli: {stock_data['days_of_supply']:.2f} gün")
    return False, None

def main():
    """Ana döngü"""
    print("=" * 60)
    print("🏥 Hospital-C - Stok Takip Sistemi")
    print("=" * 60)
    print("⚠️  Demo modu: Her 10 saniyede bir tüketim simüle edilecek")
    print("⚠️  Ctrl+C ile durdurun")
    print("=" * 60)
    
    iteration = 0
    
    while True:
        try:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"🔄 İterasyon #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Mevcut stoku al
            stock_data = get_current_stock()
            if not stock_data:
                print("⚠️ Stok bilgisi alınamadı, 10 saniye sonra tekrar denenecek...")
                time.sleep(10)
                continue
            
            print(f"📊 Mevcut Stok: {stock_data['current_stock']} birim")
            print(f"📉 Günlük Tüketim: {stock_data['daily_consumption']} birim")
            print(f"⏱️  Kalan Gün: {stock_data['days_of_supply']:.2f} gün")
            
            # Günlük tüketimi simüle et
            consumed = simulate_daily_consumption(stock_data['daily_consumption'])
            print(f"🔻 Simüle edilen tüketim: {consumed} birim")
            
            # Stoku güncelle
            if update_stock(consumed):
                # Eşik değer kontrolü
                breach, breach_data = check_threshold_breach()
                
                if breach:
                    print(f"\n{'='*60}")
                    print("📤 SOAP Client Çağrılıyor...")
                    print(f"{'='*60}")
                    
                    # SOAP client'ı çağır
                    soap_data = {
                        'currentStockUnits': breach_data['current_stock'],
                        'dailyConsumptionUnits': breach_data['daily_consumption'],
                        'daysOfSupply': float(breach_data['days_of_supply'])
                    }
                    
                    result = send_stock_update(soap_data)
                    
                    if result['success']:
                        print(f"✅ SOAP Request başarılı! (Latency: {result['latency_ms']}ms)")
                        if result['response'].get('orderTriggered'):
                            print(f"📦 Sipariş oluşturuldu: {result['response'].get('orderId')}")
                    else:
                        print(f"❌ SOAP Request başarısız: {result.get('error')}")
            
            print(f"\n⏳ 10 saniye bekleniyor...")
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n👋 Program sonlandırılıyor...")
            break
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
from flask import Flask, jsonify
import os
import time
import json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

HOSPITAL_ID = os.getenv('HOSPITAL_ID', 'Hospital-C')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def get_db_connection():
    """Database bağlantısı"""
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print(f"❌ DB Error: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'UP',
        'service': 'StockMS',
        'hospital': HOSPITAL_ID,
        'timestamp': time.time()
    })

@app.route('/publish-event', methods=['POST'])
def publish_event():
    """Simulated event publisher"""
    start_time = datetime.now()
    
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT current_stock_units, daily_consumption_units, days_of_supply
            FROM stock
            WHERE hospital_id = %s
        """, (HOSPITAL_ID,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Stock not found'}), 404
        
        event = {
            'eventId': f'EVT-{int(time.time())}',
            'eventType': 'InventoryLow',
            'hospitalId': HOSPITAL_ID,
            'productCode': 'PHYSIO-SALINE-500ML',
            'currentStockUnits': result[0],
            'dailyConsumptionUnits': result[1],
            'daysOfSupply': float(result[2]),
            'threshold': 2.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Latency hesapla
        end_time = datetime.now()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Log event (latency ile)
        cursor.execute("""
            INSERT INTO event_log 
            (event_type, direction, architecture, payload, status, latency_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, ('INVENTORY_LOW_EVENT', 'OUTGOING', 'SERVERLESS', json.dumps(event), 'SUCCESS', latency_ms))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Event published: {event['eventId']} (Latency: {latency_ms}ms)")
        
        return jsonify({
            'success': True,
            'event': event,
            'latency_ms': latency_ms
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'service': 'StockMS - Event Producer',
        'hospital': HOSPITAL_ID,
        'message': 'Simulated Event Hub Producer'
    })

if __name__ == '__main__':
    print(f"🚀 StockMS starting for {HOSPITAL_ID}...")
    app.run(host='0.0.0.0', port=8081, debug=True)
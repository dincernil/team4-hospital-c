from flask import Flask, jsonify, request
import os
import time
import json
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
import time

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
        'service': 'OrderMS',
        'hospital': HOSPITAL_ID,
        'timestamp': time.time()
    })

@app.route('/receive-order', methods=['POST'])
@app.route('/receive-order', methods=['POST'])
def receive_order():
    """Simulated order receiver with duplicate detection"""
    try:
        data = request.get_json()
        
        # Hospital ID kontrolü
        if data.get('hospitalId') != HOSPITAL_ID:
            return jsonify({'error': 'Wrong hospital ID'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Duplicate kontrolü - orderId
        cursor.execute("""
            SELECT order_id FROM orders WHERE order_id = %s
        """, (data.get('orderId'),))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            print(f"⚠️  Duplicate order detected: {data.get('orderId')}")
            return jsonify({
                'success': True,
                'orderId': data.get('orderId'),
                'message': 'Order already exists (duplicate ignored)',
                'duplicate': True
            }), 200
        
        # Duplicate kontrolü - commandId
        cursor.execute("""
            SELECT command_id FROM orders WHERE command_id = %s
        """, (data.get('commandId'),))
        
        if cursor.fetchone():
            cursor.close()
            conn.close()
            print(f"⚠️  Duplicate command detected: {data.get('commandId')}")
            return jsonify({
                'success': True,
                'commandId': data.get('commandId'),
                'message': 'Command already processed (duplicate ignored)',
                'duplicate': True
            }), 200
        
        # Order kaydet (yeni kayıt)
        cursor.execute("""
            INSERT INTO orders 
            (order_id, command_id, hospital_id, product_code, order_quantity, 
             priority, order_status, estimated_delivery_date, warehouse_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('orderId'),
            data.get('commandId'),
            data.get('hospitalId'),
            data.get('productCode'),
            data.get('orderQuantity'),
            data.get('priority'),
            'PENDING',
            data.get('estimatedDeliveryDate'),
            data.get('warehouseId')
        ))
        
        # Event log
        cursor.execute("""
            INSERT INTO event_log 
            (event_type, direction, architecture, payload, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ('ORDER_COMMAND_RECEIVED', 'INCOMING', 'SERVERLESS', json.dumps(data), 'SUCCESS'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Order received: {data.get('orderId')}")
        
        return jsonify({
            'success': True,
            'orderId': data.get('orderId'),
            'message': 'Order received successfully',
            'duplicate': False
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500
        
def home():
    return jsonify({
        'service': 'OrderMS - Event Consumer',
        'hospital': HOSPITAL_ID,
        'message': 'Simulated Event Hub Consumer'
    })

if __name__ == '__main__':
    print(f"🚀 OrderMS starting for {HOSPITAL_ID}...")
    app.run(host='0.0.0.0', port=8082, debug=True)
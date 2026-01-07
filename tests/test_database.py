import psycopg2
import os
from dotenv import load_dotenv
import pytest

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'hospital_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

def get_connection():
    """Database bağlantısı"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def test_database_connection():
    """Database bağlanıyor mu?"""
    conn = get_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result[0] == 1
    cursor.close()
    conn.close()

def test_stock_table_exists():
    """Stock tablosu var mı?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'stock'
        )
    """)
    exists = cursor.fetchone()[0]
    assert exists == True
    cursor.close()
    conn.close()

def test_orders_table_exists():
    """Orders tablosu var mı?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'orders'
        )
    """)
    exists = cursor.fetchone()[0]
    assert exists == True
    cursor.close()
    conn.close()

def test_event_log_table_exists():
    """Event log tablosu var mı?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'event_log'
        )
    """)
    exists = cursor.fetchone()[0]
    assert exists == True
    cursor.close()
    conn.close()

def test_stock_data_exists():
    """Hospital-C stok verisi var mı?"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM stock 
        WHERE hospital_id = 'Hospital-C'
    """)
    count = cursor.fetchone()[0]
    assert count > 0
    cursor.close()
    conn.close()
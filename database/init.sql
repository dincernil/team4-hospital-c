-- Hospital-C Database Schema

CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL,
    product_code TEXT NOT NULL,
    current_stock_units INTEGER NOT NULL,
    daily_consumption_units INTEGER NOT NULL,
    days_of_supply DECIMAL(5,2) NOT NULL,
    reorder_threshold DECIMAL(5,2) DEFAULT 2.0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_id TEXT UNIQUE NOT NULL,
    command_id TEXT,
    hospital_id TEXT NOT NULL,
    product_code TEXT NOT NULL,
    order_quantity INTEGER NOT NULL,
    priority TEXT NOT NULL,
    order_status TEXT DEFAULT 'PENDING',
    estimated_delivery_date TIMESTAMP,
    warehouse_id TEXT,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS event_log (
    id SERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    architecture TEXT NOT NULL,
    payload TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consumption_history (
    id SERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL,
    product_code TEXT NOT NULL,
    consumption_date DATE NOT NULL,
    units_consumed INTEGER NOT NULL,
    opening_stock INTEGER NOT NULL,
    closing_stock INTEGER NOT NULL,
    day_of_week TEXT,
    is_weekend BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    current_stock INTEGER NOT NULL,
    daily_consumption INTEGER NOT NULL,
    days_of_supply DECIMAL(5,2) NOT NULL,
    threshold DECIMAL(5,2) NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İlk veriyi ekle (Hospital-C için)
INSERT INTO stock (hospital_id, product_code, current_stock_units, daily_consumption_units, days_of_supply)
VALUES ('Hospital-C', 'PHYSIO-SALINE-500ML', 200, 79, 2.53)
ON CONFLICT DO NOTHING;
-- Migration: Add CHECK Constraints and Indexes
-- Purpose: Improve data integrity and query performance
-- COMP 464 Module D Requirements

-- ============================================================
-- PART 1: ADD CHECK CONSTRAINTS
-- ============================================================

-- Stock table constraints
ALTER TABLE stock
ADD CONSTRAINT check_stock_positive
    CHECK (current_stock_units >= 0),
ADD CONSTRAINT check_consumption_positive
    CHECK (daily_consumption_units >= 0),
ADD CONSTRAINT check_days_of_supply_positive
    CHECK (days_of_supply >= 0),
ADD CONSTRAINT check_threshold_positive
    CHECK (reorder_threshold >= 0);

-- Orders table constraints
ALTER TABLE orders
ADD CONSTRAINT check_order_quantity_positive
    CHECK (order_quantity > 0),
ADD CONSTRAINT check_priority_valid
    CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL')),
ADD CONSTRAINT check_order_status_valid
    CHECK (order_status IN ('PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'FAILED'));

-- Event_log table constraints
ALTER TABLE event_log
ADD CONSTRAINT check_direction_valid
    CHECK (direction IN ('INBOUND', 'OUTBOUND')),
ADD CONSTRAINT check_architecture_valid
    CHECK (architecture IN ('SOA', 'SERVERLESS')),
ADD CONSTRAINT check_status_valid
    CHECK (status IN ('SUCCESS', 'FAILURE', 'RETRY', 'TIMEOUT')),
ADD CONSTRAINT check_latency_positive
    CHECK (latency_ms >= 0);

-- Consumption_history table constraints
ALTER TABLE consumption_history
ADD CONSTRAINT check_consumption_units_positive
    CHECK (units_consumed >= 0),
ADD CONSTRAINT check_opening_stock_positive
    CHECK (opening_stock >= 0),
ADD CONSTRAINT check_closing_stock_positive
    CHECK (closing_stock >= 0),
ADD CONSTRAINT check_day_of_week_valid
    CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'));

-- Alerts table constraints
ALTER TABLE alerts
ADD CONSTRAINT check_alert_type_valid
    CHECK (alert_type IN ('LOW_STOCK', 'CRITICAL_STOCK', 'OUT_OF_STOCK', 'HIGH_CONSUMPTION', 'DELIVERY_DELAY')),
ADD CONSTRAINT check_severity_valid
    CHECK (severity IN ('INFO', 'WARNING', 'CRITICAL', 'EMERGENCY')),
ADD CONSTRAINT check_alert_stock_positive
    CHECK (current_stock >= 0),
ADD CONSTRAINT check_alert_consumption_positive
    CHECK (daily_consumption >= 0),
ADD CONSTRAINT check_alert_days_positive
    CHECK (days_of_supply >= 0),
ADD CONSTRAINT check_alert_threshold_positive
    CHECK (threshold >= 0);

-- ============================================================
-- PART 2: CREATE PERFORMANCE INDEXES
-- ============================================================

-- Stock table indexes
CREATE INDEX IF NOT EXISTS idx_stock_hospital_product
    ON stock(hospital_id, product_code);

CREATE INDEX IF NOT EXISTS idx_stock_days_of_supply
    ON stock(days_of_supply)
    WHERE days_of_supply < 3.0;  -- Partial index for critical stock

CREATE INDEX IF NOT EXISTS idx_stock_last_updated
    ON stock(last_updated DESC);

-- Orders table indexes
CREATE INDEX IF NOT EXISTS idx_orders_hospital_product
    ON orders(hospital_id, product_code);

CREATE INDEX IF NOT EXISTS idx_orders_status
    ON orders(order_status)
    WHERE order_status IN ('PENDING', 'PROCESSING');  -- Partial index for active orders

CREATE INDEX IF NOT EXISTS idx_orders_created_at
    ON orders(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_orders_command_id
    ON orders(command_id)
    WHERE command_id IS NOT NULL;  -- For duplicate detection

-- Event_log table indexes
CREATE INDEX IF NOT EXISTS idx_event_log_type_architecture
    ON event_log(event_type, architecture);

CREATE INDEX IF NOT EXISTS idx_event_log_timestamp
    ON event_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_event_log_status
    ON event_log(status)
    WHERE status = 'FAILURE';  -- For error monitoring

CREATE INDEX IF NOT EXISTS idx_event_log_latency
    ON event_log(latency_ms)
    WHERE latency_ms > 1000;  -- For performance analysis

-- Consumption_history table indexes
CREATE INDEX IF NOT EXISTS idx_consumption_hospital_product_date
    ON consumption_history(hospital_id, product_code, consumption_date DESC);

CREATE INDEX IF NOT EXISTS idx_consumption_date
    ON consumption_history(consumption_date DESC);

CREATE INDEX IF NOT EXISTS idx_consumption_weekend
    ON consumption_history(is_weekend, consumption_date DESC);

-- Alerts table indexes
CREATE INDEX IF NOT EXISTS idx_alerts_hospital_type
    ON alerts(hospital_id, alert_type);

CREATE INDEX IF NOT EXISTS idx_alerts_unacknowledged
    ON alerts(created_at DESC)
    WHERE acknowledged = FALSE;  -- For active alerts

CREATE INDEX IF NOT EXISTS idx_alerts_severity
    ON alerts(severity, created_at DESC)
    WHERE severity IN ('CRITICAL', 'EMERGENCY');  -- For urgent alerts

-- ============================================================
-- PART 3: ADD USEFUL COMPOSITE INDEXES
-- ============================================================

-- For Stock Monitor queries
CREATE INDEX IF NOT EXISTS idx_stock_monitor_query
    ON stock(hospital_id, product_code, days_of_supply);

-- For Order tracking queries
CREATE INDEX IF NOT EXISTS idx_order_tracking
    ON orders(hospital_id, order_status, created_at DESC);

-- For Performance analysis queries
CREATE INDEX IF NOT EXISTS idx_performance_analysis
    ON event_log(architecture, status, timestamp DESC);

-- For Consumption trend analysis
CREATE INDEX IF NOT EXISTS idx_consumption_trends
    ON consumption_history(product_code, consumption_date DESC, is_weekend);

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Verify constraints
SELECT
    con.conname AS constraint_name,
    tbl.relname AS table_name,
    pg_get_constraintdef(con.oid) AS constraint_definition
FROM pg_constraint con
JOIN pg_class tbl ON tbl.oid = con.conrelid
WHERE tbl.relname IN ('stock', 'orders', 'event_log', 'consumption_history', 'alerts')
    AND con.contype = 'c'
ORDER BY tbl.relname, con.conname;

-- Verify indexes
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('stock', 'orders', 'event_log', 'consumption_history', 'alerts')
ORDER BY tablename, indexname;

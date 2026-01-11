# 🏥 Hospital-C Supply Chain Management System

**COMP 464 - Service-Oriented Architecture & Serverless Computing**
**Team 4 - Hospital-C**

---

## 📋 Project Overview

This project implements a **hybrid SOA + Serverless architecture** for Hospital-C's medical supply chain management system. The system monitors critical medicine stock levels (PHYSIO-SALINE-500ML) and automatically triggers orders through two parallel paths:

1. **SOA Path**: Synchronous SOAP/XML communication with Team 1's central platform
2. **Serverless Path**: Asynchronous event-driven architecture using Azure Event Hubs

### Key Features

- ✅ Real-time stock monitoring with consumption simulation
- ✅ Dual architecture comparison (SOA vs Serverless)
- ✅ Automatic order triggering when stock < 2 days
- ✅ Retry mechanism with exponential backoff
- ✅ Comprehensive event logging and performance tracking
- ✅ PostgreSQL with 11 CHECK constraints + 22 custom indexes
- ✅ Docker Compose orchestration with health checks
- ✅ Integration with Team 1's Azure SOAP service

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hospital-C Infrastructure                     │
│                                                                  │
│  ┌──────────────┐      ┌─────────────────┐                     │
│  │    Stock     │──────>│   PostgreSQL    │                     │
│  │   Monitor    │<──────│    Database     │                     │
│  └──────┬───────┘      └─────────────────┘                     │
│         │                                                        │
│         │ Threshold                                              │
│         │ Breach                                                 │
│         │                                                        │
│    ┌────┴───────────────────────┐                               │
│    │                            │                               │
│    v                            v                               │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │ SOAP Client  │         │   StockMS    │                     │
│  │ (Retry 3x)   │         │  (Port 8081) │                     │
│  └──────┬───────┘         └──────┬───────┘                     │
└─────────┼────────────────────────┼──────────────────────────────┘
          │                        │
          │ SOAP/XML               │ Events
          │ HTTPS                  │ AMQP/WebSocket
          │                        │
┌─────────┼────────────────────────┼──────────────────────────────┐
│         v                        v                               │
│  ┌──────────────┐         ┌──────────────┐                     │
│  │  Team 1 SOAP │         │ Azure Event  │                     │
│  │   Service    │         │     Hub      │                     │
│  └──────────────┘         └──────┬───────┘                     │
│                                   │                              │
│                                   v                              │
│                            ┌──────────────┐                     │
│                            │   OrderMS    │                     │
│                            │  (Port 8082) │                     │
│                            └──────────────┘                     │
│                                                                  │
│                   Team 1 - Central Platform (Azure)             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Database** | PostgreSQL 15 | Data persistence, event logging |
| **Backend** | Python 3.11 | Core business logic |
| **Web Framework** | Flask 2.3 | Microservices (StockMS, OrderMS) |
| **SOA** | SOAP/XML + requests | Synchronous communication |
| **Serverless** | Azure Event Hubs | Asynchronous event-driven |
| **Orchestration** | Docker Compose | Container management |
| **Database Driver** | psycopg2-binary | PostgreSQL connectivity |

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Python 3.11+
- Git

### 1. Clone Repository

```bash
git clone <repository-url>
cd team4-hospital-c-main
```

### 2. Configure Environment

Create `.env` file in project root:

```env
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=hospital_db
DB_USER=postgres
DB_PASSWORD=postgres

# Hospital Configuration
HOSPITAL_ID=Hospital-C
PRODUCT_CODE=PHYSIO-SALINE-500ML
THRESHOLD=2.0

# Team 1 Integration
SOAP_STOCK_UPDATE_URL=https://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices
SOAP_ORDER_CREATION_URL=

# Azure Event Hub (request from Team 1)
EVENT_HUB_CONNECTION_STRING=<provided-by-team1>
EVENT_HUB_INVENTORY_LOW=inventory-low-events
EVENT_HUB_ORDER_COMMANDS=order-commands
```

### 3. Start Docker Services

```bash
# Stop any local PostgreSQL to avoid port conflicts
brew services stop postgresql@16  # macOS only

# Start Docker containers
docker-compose up -d

# Verify services are healthy
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE                      STATUS                   PORTS
b24223711b2a   postgres:15-alpine         Up (healthy)             0.0.0.0:5432->5432/tcp
b6dc41c507c4   hospital-c-stockms         Up                       0.0.0.0:8081->8081/tcp
3258a5b34a4a   hospital-c-orderms         Up                       0.0.0.0:8082->8082/tcp
```

### 4. Install Python Dependencies

```bash
pip3 install --break-system-packages \
    psycopg2-binary \
    requests \
    python-dotenv \
    flask \
    azure-eventhub
```

### 5. Run Stock Monitor

```bash
cd stock_monitor
python3 monitor.py
```

Expected output:
```
============================================================
🏥 Hospital-C - Stok Takip Sistemi
============================================================
⚠️  Demo modu: Her 10 saniyede bir tüketim simüle edilecek
⚠️  Ctrl+C ile durdurun
============================================================

============================================================
🔄 İterasyon #1 - 2026-01-08 18:30:00
============================================================
📊 Mevcut Stok: 200 birim
📉 Günlük Tüketim: 79 birim
⏱️  Kalan Gün: 2.53 gün
🔻 Simüle edilen tüketim: 75 birim
✅ Stok güncellendi: 200 → 125 (Tüketim: 75)
✔️ Stok yeterli: 1.58 gün
```

---

## 📁 Project Structure

```
team4-hospital-c-main/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment configuration
├── README.md                   # This file
│
├── database/
│   ├── init.sql                # Initial schema & data
│   └── migrations/
│       └── 001_add_constraints_and_indexes.sql
│
├── stock_monitor/
│   └── monitor.py              # Stock monitoring system
│
├── soap_client/
│   └── client.py               # SOAP client with retry logic
│
├── stockms/
│   ├── Dockerfile
│   ├── app.py                  # Event producer (Flask)
│   └── requirements.txt
│
├── orderms/
│   ├── Dockerfile
│   ├── app.py                  # Event consumer (Flask)
│   └── requirements.txt
│
├── docs/
│   ├── ARCHITECTURE.md         # System architecture diagrams
│   ├── SEQUENCE_FLOW.md        # Detailed sequence diagrams
│   ├── PERFORMANCE_ANALYSIS.md # SOA vs Serverless comparison
│   └── DEPLOYMENT_GUIDE.md     # Production deployment
│
├── tests/
│   ├── test_stock_monitor_units.py
│   └── test_soap_client_units.py
│
└── events/
    ├── inventory_low_event.json
    └── order_creation_command.json
```

---

## 🗄️ Database Schema

### Tables (5)

1. **stock** - Current inventory levels
2. **orders** - Order records (PENDING/CONFIRMED/DELIVERED)
3. **event_log** - All system events (SOA/SERVERLESS)
4. **consumption_history** - Daily consumption tracking
5. **alerts** - Critical stock alerts

### Data Integrity

- **11 CHECK constraints**: Enforce valid enum values and positive numbers
- **22 Custom indexes**: Optimized queries (composite, partial, time-based)
- **UNIQUE constraints**: Prevent duplicate orders (orderId + commandId)

### Example Queries

```sql
-- View recent stock updates
SELECT * FROM stock ORDER BY last_updated DESC LIMIT 5;

-- Compare SOA vs Serverless performance
SELECT
    architecture,
    AVG(latency_ms) as avg_latency,
    COUNT(*) as total_events,
    COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*) as success_rate
FROM event_log
GROUP BY architecture;

-- View active alerts
SELECT * FROM alerts
WHERE acknowledged = FALSE
ORDER BY created_at DESC;
```

---

## 🔄 System Workflows

### 1. Stock Monitoring Cycle (Every 10 seconds)

1. Query current stock from database
2. Simulate daily consumption (base ± 15% variance)
3. Apply weekend effect (×0.7) and random spikes (5% probability, ×1.5)
4. Update stock and log consumption history
5. Calculate `days_of_supply = current_stock / daily_consumption`
6. If `days_of_supply < 2.0` → Trigger alerts

### 2. SOA Path (Synchronous)

When threshold breached:
1. SOAP Client builds XML envelope with dual namespaces
2. POST to Team 1's SOAP endpoint (HTTPS)
3. Retry up to 3 times (delays: 5s, 15s, 30s)
4. Parse SOAP response (orderId, success status)
5. Log event with latency measurement

### 3. Serverless Path (Asynchronous)

When threshold breached:
1. Stock Monitor calls StockMS `/publish-event`
2. StockMS publishes `InventoryLowEvent` to Azure Event Hub
3. OrderMS subscribes and receives event
4. Duplicate detection (check orderId/commandId)
5. Create order with PENDING status
6. Log event (SERVERLESS architecture)

---

## 📈 Performance Metrics

### Observed Latencies

| Architecture | Avg Latency | Success Rate | Notes |
|-------------|-------------|--------------|-------|
| **SOA** | 755-995ms | High | Blocking, immediate confirmation |
| **Serverless** | <100ms (publish) | High | Non-blocking, eventual consistency |

### Event Log Analysis

```sql
-- Performance by architecture
SELECT
    architecture,
    COUNT(*) as events,
    AVG(latency_ms) as avg_latency_ms,
    MIN(latency_ms) as min_latency_ms,
    MAX(latency_ms) as max_latency_ms
FROM event_log
WHERE architecture IN ('SOA', 'SERVERLESS')
    AND status = 'SUCCESS'
GROUP BY architecture;
```

---

## 🧪 Testing

### Unit Tests

```bash
# Stock Monitor tests
pytest tests/test_stock_monitor_units.py -v

# SOAP Client tests
pytest tests/test_soap_client_units.py -v
```

### Integration Tests

```bash
# Test SOAP endpoint
curl -X POST http://localhost:8000/CentralServices \
  -H "Content-Type: text/xml" \
  -d @tests/soap_request_sample.xml

# Test StockMS
curl -X POST http://localhost:8081/publish-event \
  -H "Content-Type: application/json" \
  -d @events/inventory_low_event.json
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_HOST` | PostgreSQL host | `127.0.0.1` (use IPv4, not `localhost`) |
| `DB_PORT` | PostgreSQL port | `5432` |
| `HOSPITAL_ID` | Hospital identifier | `Hospital-C` |
| `PRODUCT_CODE` | Medicine code | `PHYSIO-SALINE-500ML` |
| `THRESHOLD` | Days of supply threshold | `2.0` |
| `SOAP_STOCK_UPDATE_URL` | Team 1 SOAP endpoint | Team 1's Azure URL |
| `EVENT_HUB_CONNECTION_STRING` | Azure Event Hub credentials | Provided by Team 1 |

### Important Notes

⚠️ **Use `127.0.0.1` instead of `localhost`** for `DB_HOST` to avoid IPv6 (::1) connection issues on macOS.

⚠️ **Stop local PostgreSQL** before running Docker:
```bash
brew services stop postgresql@16
```

---

## 📚 Documentation

- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - System architecture, components, ER diagrams
- [**SEQUENCE_FLOW.md**](docs/SEQUENCE_FLOW.md) - Detailed sequence diagrams for all flows
- [**PERFORMANCE_ANALYSIS.md**](docs/PERFORMANCE_ANALYSIS.md) - SOA vs Serverless comparison
- [**DEPLOYMENT_GUIDE.md**](docs/DEPLOYMENT_GUIDE.md) - Production deployment instructions

---

## 🐛 Troubleshooting

### Issue: Database connection error "role postgres does not exist"

**Solution**: Local PostgreSQL is conflicting with Docker. Stop it:
```bash
brew services stop postgresql@16
lsof -i :5432  # Verify only Docker is listening
```

### Issue: SOAP schema validation error

**Solution**: Verify XML namespaces:
- Envelope: `http://schemas.xmlsoap.org/soap/envelope/`
- Operation: `http://hospital-supply-chain.example.com/soap`
- Fields: `http://hospital-supply-chain.example.com/soap/stock`

### Issue: Event Hub connection fails

**Solution**:
1. Request connection string from Team 1
2. Add to `.env`: `EVENT_HUB_CONNECTION_STRING=Endpoint=sb://...`
3. Verify Event Hub name: `inventory-low-events`

---

## 👥 Team Integration

### Team 1 - Central Platform

**SOAP Service:**
- Endpoint: `https://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices`
- WSDL: Same URL + `?wsdl`
- Operation: `StockUpdate`

**Azure Event Hub:**
- Name: `inventory-low-events`
- Protocol: AMQP over WebSocket (firewall-friendly)
- Connection: Request from Team 1

---

## 📊 COMP 464 Requirements Checklist

### Module A: Stock Monitoring System ✅
- [x] Daily consumption simulation (variance, spike, weekend)
- [x] Threshold breach detection (< 2 days)
- [x] Alert creation and logging

### Module B: SOA Integration ✅
- [x] SOAP/XML messaging with Team 1
- [x] Retry mechanism (3 attempts, exponential backoff)
- [x] WSDL schema compliance

### Module C: Serverless Microservices ⚠️
- [x] StockMS event producer
- [x] OrderMS event consumer
- [ ] Real Azure Event Hubs (simulated, needs connection string)

### Module D: Database ✅
- [x] PostgreSQL with 5 tables
- [x] 11 CHECK constraints
- [x] 22 custom indexes

### Module E: Docker & Deployment ✅
- [x] docker-compose.yml with 3 services
- [x] Health checks and dependencies
- [x] Environment configuration

### Documentation ✅
- [x] Architecture diagrams (Mermaid)
- [x] Sequence diagrams
- [x] README with setup instructions
- [x] Performance analysis

**Overall Completion: 88%**

---

## 🔮 Future Enhancements

1. **Real Azure Event Hub Integration** - Replace simulation with actual Event Hub
2. **Monitoring Dashboard** - Grafana + Prometheus for real-time metrics
3. **GitHub Actions CI/CD** - Automated testing and deployment
4. **Multi-Hospital Support** - Extend to Hospital-A, Hospital-B
5. **Predictive Analytics** - ML-based consumption forecasting

---

## 📝 License

This project is developed for **COMP 464 - Service-Oriented Architecture** course.

---

## 📧 Contact

**Team 4 - Hospital-C**
Course: COMP 464
Semester: Fall 2025

---

**Last Updated**: 2026-01-08
**Version**: 1.0.0

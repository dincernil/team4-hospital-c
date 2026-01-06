# Hospital-C - Medical Supply Chain System
**COMP 464 Final Project - Team 4**

IoT-based hospital inventory management system integrating SOA and Serverless architectures.

## 🏥 Project Overview

This system monitors Hospital-C's stock levels for PHYSIO-SALINE-500ML and automatically triggers orders when inventory falls below 2.0 days of supply.

### Architecture
- **SOA Path:** SOAP-based communication with Team 1's central warehouse
- **Serverless Path:** Event-driven microservices (Event Hub simulation)
- **Database:** PostgreSQL for all data persistence
- **Monitoring:** Real-time stock tracking with consumption simulation

## 📊 System Components

### Services
1. **Stock Monitor** - Simulates daily consumption and monitors thresholds
2. **SOAP Client** - Communicates with central warehouse via SOAP/XML
3. **StockMS** (Port 8081) - Event producer for inventory alerts
4. **OrderMS** (Port 8082) - Event consumer for order commands
5. **PostgreSQL** (Port 5432) - Database for all data

### Database Tables
- `stock` - Current inventory levels
- `orders` - Order history
- `event_log` - SOA and Serverless event tracking
- `alerts` - Threshold breach alerts
- `consumption_history` - Daily consumption records

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Python 3.11+
- Git

### Installation

1. **Clone the repository:**
```bash
git clone [YOUR-REPO-URL]
cd hospital-c-project
```

2. **Start all services:**
```bash
docker-compose up --build
```

3. **Verify services are running:**
```bash
curl http://localhost:8081/health  # StockMS
curl http://localhost:8082/health  # OrderMS
```

### Running Stock Monitor (Simulation)
```bash
cd stock_monitor
pip3 install -r requirements.txt --break-system-packages
python3 monitor.py
```

### Running SOAP Client (Manual Test)
```bash
cd soap_client
pip3 install -r requirements.txt --break-system-packages
python3 client.py
```

## 🧪 Testing

### Health Checks
```bash
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Publish Event (StockMS)
```bash
curl -X POST http://localhost:8081/publish-event
```

### Receive Order (OrderMS)
```bash
curl -X POST http://localhost:8082/receive-order \
  -H "Content-Type: application/json" \
  -d '{
    "commandId": "CMD-TEST",
    "orderId": "ORD-TEST-001",
    "hospitalId": "Hospital-C",
    "productCode": "PHYSIO-SALINE-500ML",
    "orderQuantity": 300,
    "priority": "HIGH",
    "estimatedDeliveryDate": "2026-01-07T12:00:00",
    "warehouseId": "CENTRAL-WAREHOUSE"
  }'
```

### Database Access
```bash
docker exec -it hospital-c-db psql -U postgres -d hospital_db
```

## 📁 Project Structure
```
hospital-c-project/
├── database/
│   └── init.sql              # Database schema
├── soap_client/
│   ├── client.py             # SOAP client implementation
│   ├── requirements.txt
│   └── wsdl/
│       └── StockUpdateService.wsdl
├── stock_monitor/
│   ├── monitor.py            # Stock monitoring system
│   └── requirements.txt
├── stockms/
│   ├── app.py               # Event producer microservice
│   ├── Dockerfile
│   └── requirements.txt
├── orderms/
│   ├── app.py               # Event consumer microservice
│   ├── Dockerfile
│   └── requirements.txt
├── contracts/
│   └── schemas/             # JSON event schemas
├── docker-compose.yml       # Multi-container orchestration
├── .env                     # Environment configuration
└── README.md
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hospital_db
DB_USER=postgres
DB_PASSWORD=postgres

# Hospital
HOSPITAL_ID=Hospital-C
PRODUCT_CODE=PHYSIO-SALINE-500ML
THRESHOLD=2.0

# Team 1 Integration
SOAP_STOCK_UPDATE_URL=http://localhost:8000/StockUpdateService
```

## 📈 Performance Metrics

- **SOAP Latency:** 2-14ms
- **Event Processing:** <5ms
- **Database Operations:** <10ms
- **Stock Monitoring:** 10-second intervals

## 🔗 Integration with Team 1

This project integrates with Team 1's Central Platform:
- **GitHub:** https://github.com/YunusogluKerem/COMP464-Team1-Central-Platform
- **WSDL:** StockUpdateService
- **Event Hub:** inventory-low-events, order-commands

## 👥 Team Members

**Team 4 - Hospital-C**
- [Your names here]

## 📝 License

This project is part of COMP 464 coursework at MEF University.

## 🆘 Troubleshooting

### Port Already in Use
```bash
docker-compose down
docker-compose up
```

### Database Connection Error
```bash
docker-compose restart database
```

### Reset Database
```bash
docker-compose down -v
docker-compose up --build
```

## 📞 Support

For issues or questions, contact the team via [your contact method].
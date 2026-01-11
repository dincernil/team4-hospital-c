# Hospital-C Production Deployment Guide

**COMP 464 - Deployment & Operations Manual**
**Version:** 1.0.0
**Last Updated:** 2026-01-08

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#1-pre-deployment-checklist)
2. [Environment Setup](#2-environment-setup)
3. [Docker Deployment](#3-docker-deployment)
4. [Security Hardening](#4-security-hardening)
5. [Monitoring & Observability](#5-monitoring--observability)
6. [Backup & Disaster Recovery](#6-backup--disaster-recovery)
7. [Scaling Guidelines](#7-scaling-guidelines)
8. [CI/CD Pipeline](#8-cicd-pipeline)
9. [Troubleshooting](#9-troubleshooting)
10. [Maintenance Procedures](#10-maintenance-procedures)

---

## 1️⃣ Pre-Deployment Checklist

### Infrastructure Requirements

**Minimum Specifications:**
```
CPU:    4 cores (2.0 GHz+)
RAM:    8 GB
Disk:   50 GB SSD
OS:     Ubuntu 22.04 LTS / RHEL 8+ / macOS 12+
```

**Production Specifications:**
```
CPU:    8 cores (3.0 GHz+)
RAM:    16 GB
Disk:   200 GB SSD (NVMe preferred)
OS:     Ubuntu 22.04 LTS (recommended)
```

### Software Prerequisites

**Required Software:**
```bash
# Docker Engine
Docker version 24.0+
Docker Compose version 2.20+

# Python
Python 3.11+

# Database Tools
psql (PostgreSQL client) 15+

# Networking
curl, netcat, lsof
```

**Installation Commands (Ubuntu):**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Python
sudo apt install python3.11 python3.11-pip

# Install PostgreSQL client
sudo apt install postgresql-client-15
```

### Network Requirements

**Outbound Connections:**
```
Azure SOAP Service:
  - Host: team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net
  - Port: 443 (HTTPS)
  - Protocol: HTTPS/TLS 1.2+

Azure Event Hub:
  - Host: *.servicebus.windows.net
  - Port: 5671 (AMQP over TLS)
  - Port: 443 (AMQP over WebSocket)
  - Protocol: AMQP 1.0
```

**Inbound Connections (optional):**
```
StockMS API: Port 8081 (HTTP)
OrderMS API: Port 8082 (HTTP)
PostgreSQL: Port 5432 (only for admin access)
```

### Security Checklist

- [ ] Firewall configured (allow only necessary ports)
- [ ] SSH key-based authentication enabled
- [ ] Root login disabled
- [ ] Fail2ban installed and configured
- [ ] SSL certificates obtained (if exposing APIs)
- [ ] Secrets stored in vault (not in .env)
- [ ] User accounts created (non-root)
- [ ] Audit logging enabled

---

## 2️⃣ Environment Setup

### Step 1: Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/hospital-c
sudo chown $USER:$USER /opt/hospital-c
cd /opt/hospital-c

# Clone repository
git clone https://github.com/your-org/team4-hospital-c-main.git
cd team4-hospital-c-main

# Verify files
ls -la
```

### Step 2: Configure Environment Variables

**Create Production .env:**
```bash
cp .env.example .env
nano .env
```

**Production .env Template:**
```env
# ============================================================
# DATABASE CONFIGURATION
# ============================================================
DB_HOST=database  # Docker service name (internal network)
DB_PORT=5432
DB_NAME=hospital_db
DB_USER=postgres
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD_HERE  # Use strong password!

# ============================================================
# HOSPITAL CONFIGURATION
# ============================================================
HOSPITAL_ID=Hospital-C
PRODUCT_CODE=PHYSIO-SALINE-500ML
THRESHOLD=2.0

# ============================================================
# TEAM 1 INTEGRATION (SOA)
# ============================================================
SOAP_STOCK_UPDATE_URL=https://team1-central-platform-eqajhdbjbggkfxhf.westeurope-01.azurewebsites.net/CentralServices
SOAP_ORDER_CREATION_URL=

# ============================================================
# AZURE EVENT HUB (SERVERLESS)
# ============================================================
# Request from Team 1 - DO NOT COMMIT TO GIT!
EVENT_HUB_CONNECTION_STRING=Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY_HERE
EVENT_HUB_INVENTORY_LOW=inventory-low-events
EVENT_HUB_ORDER_COMMANDS=order-commands

# ============================================================
# MONITORING & LOGGING
# ============================================================
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json  # json or plain
SENTRY_DSN=  # Optional: Error tracking

# ============================================================
# PERFORMANCE TUNING
# ============================================================
STOCK_MONITOR_INTERVAL=10  # seconds between checks
SOAP_TIMEOUT=30  # seconds
SOAP_MAX_RETRIES=3
```

**Secure the .env file:**
```bash
chmod 600 .env
chown $USER:$USER .env
```

### Step 3: Database Initialization

**Option A: Use Docker Volume (Recommended)**
```bash
# Database will initialize automatically from init.sql
# No manual steps required
```

**Option B: Manual PostgreSQL Setup**
```bash
# If using external PostgreSQL
psql -h your-db-host -U postgres -d hospital_db -f database/init.sql
psql -h your-db-host -U postgres -d hospital_db -f database/migrations/001_add_constraints_and_indexes.sql
```

---

## 3️⃣ Docker Deployment

### Production Docker Compose

**Create docker-compose.prod.yml:**
```yaml
services:
  database:
    image: postgres:15-alpine
    container_name: hospital-c-db-prod
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "127.0.0.1:5432:5432"  # Bind to localhost only
    volumes:
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - hospital-network
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  stockms:
    build:
      context: ./stockms
      dockerfile: Dockerfile
    container_name: hospital-c-stockms-prod
    depends_on:
      database:
        condition: service_healthy
    environment:
      - DB_HOST=database
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - HOSPITAL_ID=${HOSPITAL_ID}
      - EVENT_HUB_CONNECTION_STRING=${EVENT_HUB_CONNECTION_STRING}
    ports:
      - "127.0.0.1:8081:8081"  # Internal only
    networks:
      - hospital-network
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  orderms:
    build:
      context: ./orderms
      dockerfile: Dockerfile
    container_name: hospital-c-orderms-prod
    depends_on:
      database:
        condition: service_healthy
    environment:
      - DB_HOST=database
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - HOSPITAL_ID=${HOSPITAL_ID}
      - EVENT_HUB_CONNECTION_STRING=${EVENT_HUB_CONNECTION_STRING}
    ports:
      - "127.0.0.1:8082:8082"  # Internal only
    networks:
      - hospital-network
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
    driver: local

networks:
  hospital-network:
    driver: bridge
```

### Deployment Commands

**Build and Start Services:**
```bash
# Load environment variables
set -a
source .env
set +a

# Build images
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps
```

**Expected Output:**
```
NAME                      STATUS                   PORTS
hospital-c-db-prod        Up (healthy)             127.0.0.1:5432->5432/tcp
hospital-c-stockms-prod   Up                       127.0.0.1:8081->8081/tcp
hospital-c-orderms-prod   Up                       127.0.0.1:8082->8082/tcp
```

### Health Check Verification

```bash
# Database health
docker exec hospital-c-db-prod pg_isready -U postgres

# StockMS health
curl http://127.0.0.1:8081/health

# OrderMS health
curl http://127.0.0.1:8082/health

# Expected response:
# {"status": "UP", "service": "StockMS", "hospital": "Hospital-C"}
```

---

## 4️⃣ Security Hardening

### Container Security

**1. Run as Non-Root User**

Add to Dockerfile:
```dockerfile
# Create non-root user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

# Change ownership
RUN chown -R appuser:appuser /app

# Switch user
USER appuser
```

**2. Read-Only Root Filesystem**

```yaml
# In docker-compose.prod.yml
services:
  stockms:
    read_only: true
    tmpfs:
      - /tmp
```

**3. Limit Resources**

```yaml
services:
  stockms:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
```

### Network Security

**Firewall Configuration (UFW):**
```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Deny all inbound by default
sudo ufw default deny incoming

# Allow outbound
sudo ufw default allow outgoing

# Do NOT expose database or APIs to internet
# Access only via SSH tunnel if needed
```

**SSH Tunnel for Remote Access:**
```bash
# From local machine
ssh -L 5432:localhost:5432 user@production-server
ssh -L 8081:localhost:8081 user@production-server

# Now access via localhost:5432 and localhost:8081
```

### Secrets Management

**Option 1: Docker Secrets (Docker Swarm)**
```bash
# Create secrets
echo "your_strong_password" | docker secret create db_password -
echo "your_event_hub_connection" | docker secret create event_hub_conn -

# Use in docker-compose
secrets:
  - db_password
  - event_hub_conn
```

**Option 2: HashiCorp Vault**
```bash
# Install Vault
vault kv put secret/hospital-c \
  db_password="your_password" \
  event_hub_connection="your_connection_string"

# Retrieve in application
DB_PASSWORD=$(vault kv get -field=db_password secret/hospital-c)
```

**Option 3: AWS Secrets Manager**
```bash
# Store secret
aws secretsmanager create-secret \
  --name hospital-c/db-password \
  --secret-string "your_password"

# Retrieve in startup script
DB_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id hospital-c/db-password \
  --query SecretString --output text)
```

---

## 5️⃣ Monitoring & Observability

### Log Management

**Centralized Logging with ELK Stack:**

**docker-compose.monitoring.yml:**
```yaml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

**View Logs:**
```bash
# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f stockms

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 orderms

# Grep for errors
docker-compose -f docker-compose.prod.yml logs | grep ERROR
```

### Metrics with Prometheus + Grafana

**docker-compose.monitoring.yml (add):**
```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  prometheus_data:
  grafana_data:
```

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'stockms'
    static_configs:
      - targets: ['stockms:8081']

  - job_name: 'orderms'
    static_configs:
      - targets: ['orderms:8082']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Health Monitoring Script

**health_check.sh:**
```bash
#!/bin/bash

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=== Hospital-C Health Check ==="
echo ""

# Check Docker containers
echo "Checking Docker containers..."
CONTAINERS=$(docker ps --filter "name=hospital-c" --format "{{.Names}}")
for container in $CONTAINERS; do
    STATUS=$(docker inspect -f '{{.State.Status}}' $container)
    if [ "$STATUS" == "running" ]; then
        echo -e "${GREEN}✓${NC} $container: $STATUS"
    else
        echo -e "${RED}✗${NC} $container: $STATUS"
    fi
done

echo ""

# Check database
echo "Checking database..."
DB_CHECK=$(docker exec hospital-c-db-prod pg_isready -U postgres 2>&1)
if [[ $DB_CHECK == *"accepting connections"* ]]; then
    echo -e "${GREEN}✓${NC} Database: accepting connections"
else
    echo -e "${RED}✗${NC} Database: $DB_CHECK"
fi

echo ""

# Check StockMS API
echo "Checking StockMS..."
STOCKMS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8081/health)
if [ "$STOCKMS_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✓${NC} StockMS: HTTP $STOCKMS_RESPONSE"
else
    echo -e "${RED}✗${NC} StockMS: HTTP $STOCKMS_RESPONSE"
fi

echo ""

# Check OrderMS API
echo "Checking OrderMS..."
ORDERMS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8082/health)
if [ "$ORDERMS_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✓${NC} OrderMS: HTTP $ORDERMS_RESPONSE"
else
    echo -e "${RED}✗${NC} OrderMS: HTTP $ORDERMS_RESPONSE"
fi

echo ""

# Check disk space
echo "Checking disk space..."
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓${NC} Disk usage: ${DISK_USAGE}%"
else
    echo -e "${RED}✗${NC} Disk usage: ${DISK_USAGE}% (Warning: >80%)"
fi

echo ""
echo "=== Health Check Complete ==="
```

**Schedule with Cron:**
```bash
# Add to crontab
crontab -e

# Run every 5 minutes
*/5 * * * * /opt/hospital-c/team4-hospital-c-main/health_check.sh >> /var/log/hospital-c-health.log 2>&1
```

---

## 6️⃣ Backup & Disaster Recovery

### Database Backup Strategy

**Automated Daily Backup Script:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="/opt/backups/hospital-c"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="hospital_db_$DATE.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Dump database
docker exec hospital-c-db-prod pg_dump -U postgres hospital_db | gzip > $BACKUP_DIR/$BACKUP_FILE

# Verify backup
if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo "✓ Backup created: $BACKUP_FILE"

    # Upload to S3 (optional)
    aws s3 cp $BACKUP_DIR/$BACKUP_FILE s3://hospital-c-backups/

    # Delete backups older than 30 days
    find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
else
    echo "✗ Backup failed!"
    exit 1
fi
```

**Schedule Daily Backup:**
```bash
# Add to crontab
crontab -e

# Run at 2 AM daily
0 2 * * * /opt/hospital-c/team4-hospital-c-main/backup_database.sh
```

### Restore Procedure

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore from backup
gunzip < /opt/backups/hospital-c/hospital_db_20260108_020000.sql.gz | \
  docker exec -i hospital-c-db-prod psql -U postgres hospital_db

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify data
docker exec hospital-c-db-prod psql -U postgres -d hospital_db -c "SELECT COUNT(*) FROM stock;"
```

### Disaster Recovery Plan

**RTO (Recovery Time Objective):** 1 hour
**RPO (Recovery Point Objective):** 24 hours

**Recovery Steps:**

1. **Provision New Server** (15 minutes)
   ```bash
   # Use infrastructure as code (Terraform/Ansible)
   terraform apply
   ```

2. **Install Prerequisites** (10 minutes)
   ```bash
   # Automated via cloud-init
   ```

3. **Clone Repository** (5 minutes)
   ```bash
   git clone https://github.com/your-org/team4-hospital-c-main.git
   ```

4. **Restore Database** (20 minutes)
   ```bash
   # Download from S3
   aws s3 cp s3://hospital-c-backups/latest.sql.gz .

   # Restore
   gunzip < latest.sql.gz | docker exec -i hospital-c-db-prod psql -U postgres hospital_db
   ```

5. **Start Services** (10 minutes)
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

**Total Recovery Time:** 60 minutes

---

## 7️⃣ Scaling Guidelines

### Horizontal Scaling (Multiple Instances)

**Docker Swarm Configuration:**
```yaml
services:
  stockms:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
```

**Load Balancer (Nginx):**
```nginx
upstream stockms_backend {
    least_conn;
    server stockms1:8081;
    server stockms2:8081;
    server stockms3:8081;
}

server {
    listen 80;
    location / {
        proxy_pass http://stockms_backend;
    }
}
```

### Vertical Scaling (Resource Increase)

**Identify Bottlenecks:**
```bash
# CPU usage
docker stats

# Memory usage
docker exec hospital-c-stockms-prod ps aux

# Database connections
docker exec hospital-c-db-prod psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"
```

**Increase Resources:**
```yaml
services:
  stockms:
    deploy:
      resources:
        limits:
          cpus: '4'      # Increase from 2
          memory: 2G     # Increase from 1G
```

---

## 8️⃣ CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy.yml:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pytest pytest-cov
          pip install -r stockms/requirements.txt

      - name: Run tests
        run: pytest tests/ -v --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/hospital-c/team4-hospital-c-main
            git pull origin main
            docker-compose -f docker-compose.prod.yml build
            docker-compose -f docker-compose.prod.yml up -d
```

---

## 9️⃣ Troubleshooting

### Common Issues

**Issue 1: Container Won't Start**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs stockms

# Common causes:
# - Missing environment variable
# - Port already in use
# - Database not ready

# Solution: Check .env and health checks
```

**Issue 2: Database Connection Refused**
```bash
# Check database status
docker exec hospital-c-db-prod pg_isready

# Check network
docker network inspect hospital-network

# Verify connection string
echo $DB_HOST
```

**Issue 3: High Memory Usage**
```bash
# Check memory
docker stats

# Solution: Restart containers
docker-compose -f docker-compose.prod.yml restart

# Or increase limits in docker-compose.prod.yml
```

---

## 🔟 Maintenance Procedures

### Regular Maintenance Tasks

**Daily:**
- [ ] Check health monitoring dashboard
- [ ] Review error logs
- [ ] Verify backups completed

**Weekly:**
- [ ] Review performance metrics
- [ ] Check disk space
- [ ] Update dependencies (security patches)

**Monthly:**
- [ ] Test disaster recovery procedure
- [ ] Review and rotate logs
- [ ] Update documentation

### Update Procedure

```bash
# 1. Pull latest changes
git pull origin main

# 2. Rebuild images
docker-compose -f docker-compose.prod.yml build

# 3. Rolling update (zero downtime)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build stockms

# 4. Verify health
curl http://127.0.0.1:8081/health

# 5. Update other services
docker-compose -f docker-compose.prod.yml up -d --no-deps --build orderms
```

---

## 📞 Support & Escalation

### Contact Information

**Team 4 - Hospital-C:**
- Primary: team4-hospitalc@example.com
- On-call: +1-555-HOSPITAL

**Team 1 - Central Platform:**
- SOAP Service: team1-support@example.com
- Event Hub: team1-eventhub@example.com

### Escalation Matrix

| Severity | Response Time | Resolution Time | Contact |
|----------|--------------|-----------------|---------|
| P1 (Critical) | 15 minutes | 2 hours | On-call engineer |
| P2 (High) | 1 hour | 8 hours | Team lead |
| P3 (Medium) | 4 hours | 24 hours | Developer |
| P4 (Low) | 24 hours | 7 days | Backlog |

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-08
**Author:** Team 4 - Hospital-C
**Course:** COMP 464


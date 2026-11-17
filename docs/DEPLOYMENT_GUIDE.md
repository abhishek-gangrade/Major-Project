# AdaptivePrep Production Deployment Guide

**Project Title:** AdaptivePrep: A Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
**Document:** `/docs/DEPLOYMENT_GUIDE.md`  
**Target Environments:** Local Bare-Metal / Docker Compose / Cloud Virtual Machine (AWS EC2 / GCP Compute Engine / DigitalOcean Droplet)  
**Date:** November 17, 2026  

---

## 1. System Architecture in Production

In production, AdaptivePrep is architected with three isolated, scalable containers:

```mermaid
graph TD
    Client["HTTPS Clients (Desktop & Mobile Browsers)"] --> ReverseProxy["Nginx / Cloudflare Edge Proxy (Port 443 / 80)"]
    ReverseProxy -->|Static Assets & SPA Routing| Frontend["adaptiveprep_frontend (Nginx Alpine + Built Dist)"]
    ReverseProxy -->|API Proxy (/api/* & /docs)| Backend["adaptiveprep_backend (FastAPI / Uvicorn Workers)"]
    Backend --> DB[(adaptiveprep_db: PostgreSQL 16)]
    Backend --> Logs[(Persistent Recommendation & Attempt Logs)]
```

---

## 2. Prerequisites

- **Docker:** Engine 24.0+ and Docker Compose v2.20+
- **Host Ports:** Ensure ports `80` (or `5173`), `8000`, and `5432` are available.
- **Hardware:** Minimum 2 vCPUs, 2 GB RAM, 10 GB SSD storage.

---

## 3. One-Command Docker Compose Deployment

The repository includes a battle-tested `docker-compose.yml` that provisions PostgreSQL 16, runs Alembic migrations, seeds placement questions, builds the React 18 production bundle, and serves the application:

```bash
# 1. Clone repository and navigate to root
cd /path/to/AdaptivePrep

# 2. Build and launch all containers in detached mode
docker compose up -d --build

# 3. Inspect container health
docker compose ps
```

### Accessing the Running Services:
- **Web Application (Frontend):** `http://localhost:5173` (or port `80` in cloud deployment)
- **FastAPI REST API Gateway:** `http://localhost:8000/api/v1`
- **Interactive OpenAPI Documentation (Swagger UI):** `http://localhost:8000/docs`
- **Alternative API Reference (ReDoc):** `http://localhost:8000/redoc`

---

## 4. Local Bare-Metal Development Setup (Without Docker)

If developing locally without Docker, follow these instructions using the built-in SQLite database engine:

### 4.1 Backend Setup
```bash
# 1. Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install pinned dependencies
pip install -r backend/requirements.txt

# 3. Run Alembic schema migrations
cd backend
alembic upgrade head
cd ..

# 4. Seed placement question inventory and demo cohorts
PYTHONPATH=. python backend/app/db/seed.py

# 5. Launch FastAPI development server
PYTHONPATH=. uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4.2 Frontend Setup
```bash
# 1. Navigate to frontend directory and install dependencies
cd frontend
npm install

# 2. Start Vite development server
npm run dev -- --host 0.0.0.0
```
Open `http://localhost:5173` in your browser.

---

## 5. Production Environment Variables Reference

Configure environment variables via `.env` file in the project root or in container orchestration manifests:

| Environment Variable | Required | Default Value | Production Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `sqlite:////Users/apple/Desktop/AdaptivePrep/adaptiveprep.db` | PostgreSQL connection string: `postgresql+psycopg://user:password@host:5432/dbname` |
| `SECRET_KEY` | Yes | `development-secret-key-change-in-production` | 64-character cryptographically secure hexadecimal random key for signing JWT tokens |
| `ENVIRONMENT` | Yes | `development` | Set to `production` |
| `BACKEND_CORS_ORIGINS` | Yes | `["http://localhost:5173"]` | JSON array of whitelisted origin URLs (e.g. `["https://adaptiveprep.medicaps.ac.in"]`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` (24 hours) | Token lifetime in minutes |
| `ALGORITHM_VERSION` | No | `v1.0.0` | Active recommendation algorithm release tag |

---

## 6. Database Maintenance & Operations

### 6.1 Executing Alembic Migrations
```bash
# From repository root with virtual environment activated:
cd backend
alembic upgrade head
```

### 6.2 Backing Up PostgreSQL Data
```bash
# Snapshot entire PostgreSQL database from running container
docker exec -t adaptiveprep_db pg_dump -U postgres -d adaptiveprep -F c -b -v -f /var/lib/postgresql/data/backup_$(date +%F_%T).dump
```

### 6.3 Restoring from Backup
```bash
docker exec -i adaptiveprep_db pg_restore -U postgres -d adaptiveprep -v /var/lib/postgresql/data/backup_target.dump
```

---

## 7. Operational Health Checks & Telemetry

- **Liveness Probe:** `GET /health` returns HTTP 200:
  ```json
  {
    "status": "healthy",
    "service": "AdaptivePrep",
    "environment": "production",
    "algorithm_version": "v1.0.0"
  }
  ```
- **Process Timing Header:** Every HTTP response includes `X-Process-Time: <seconds>`.
- **Log Inspection:**
  ```bash
  # View backend logs in real time
  docker compose logs -f backend

  # View database logs
  docker compose logs -f db
  ```

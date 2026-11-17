# AdaptivePrep — Adaptive Placement Preparation Platform

> **Full Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
> **Institution:** Medi-Caps University, Indore  
> **Department:** Department of Computer Science & Engineering  
> **Project Team:** Abhishek Gangrade, Aastha Jain  
> **Project Guide:** Prof. HarshPratap Singh  
> **Document Version:** 2.0 (Production-Verified Release)  

[![Tests](https://img.shields.io/badge/tests-31%20passed-emerald?style=flat-square)](docs/TESTING_REPORT.md)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%200.115+-teal?style=flat-square)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript%20%7C%20Tailwind-cyan?style=flat-square)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016%20%2F%20SQLite-blue?style=flat-square)](https://www.postgresql.org)
[![Alembic](https://img.shields.io/badge/Migrations-Alembic%201.14+-orange?style=flat-square)](https://alembic.sqlalchemy.org)

---

## 1. Project Overview

AdaptivePrep is an educational web application designed to prepare university engineering students for campus placement examinations (e.g. TCS, Infosys, Wipro, Amazon, Cognizant, Accenture).

Unlike static question-bank portals that serve predetermined linear question lists or random problems, AdaptivePrep continuously evaluates a student's prior practice history, estimates proficiency independently across technical placement domains, and recommends questions matched to the learner's frontier of competence.

### Core Capabilities
- **Multi-Factor Adaptive Recommendation:** Computes topic proficiency $S = 100 \times (0.45A + 0.25R + 0.20D + 0.10E)$, dynamically balancing historical accuracy ($A$), recent momentum ($R$), problem difficulty ($D$), and solving efficiency ($E$).
- **Persistent Recommendation Logging:** Every algorithmic recommendation records an immutable audit log with learner-state snapshots ($\{A, R, D, E, n\}$) in `recommendation_logs`.
- **Explainable Recommendations:** Transparently explains why each question was selected based on actual performance metrics.
- **Question Lifecycle & Versioning:** Full admin editorial pipeline (`draft` $\to$ `in_review` $\to$ `published` $\to$ `archived`) with automatic question version incrementing on statement modifications.
- **Answer Key Privacy:** Server-side correctness evaluation prevents client-side answer key inspection.
- **Idempotency & Anti-Gaming Safeguards:** 5-second duplicate attempt submission protection and anti-guessing penalties on rushed incorrect responses.
- **Comprehensive Analytics:** Recharts visualizes topic proficiency radar/bars, rolling accuracy curves, and difficulty breakdown.
- **Research & Evaluation Framework:** 3-arm experimental evaluation module (Multi-Factor Adaptive vs. Accuracy-Only vs. Random baseline) with factor ablation support and de-identified CSV dataset export.

---

## 2. Technology Stack

- **Frontend:** React 18, TypeScript 5, Vite 5, Tailwind CSS (Teal `#167D74`), React Router v6, Recharts, Lucide React.
- **Backend:** Python 3.12 / 3.14, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, Psycopg (PostgreSQL), SQLite fallback, NumPy, Pandas, Pytest.
- **Security:** bcrypt password hashing (12 rounds), JWT Bearer tokens, role-based authorization (Student & Admin), sliding-window auth rate limiting (15 req/min), strict HTTP security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`).
- **Deployment:** Docker, Docker Compose, Nginx.

---

## 3. Quick Start: Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm

### Step 1: Start Backend
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Run Alembic schema migrations
cd backend
alembic upgrade head
cd ..

# 4. Seed question bank and demo cohorts
PYTHONPATH=. python backend/app/db/seed.py

# 5. Launch FastAPI server (Runs on http://localhost:8000)
PYTHONPATH=. uvicorn backend.app.main:app --reload --port 8000
```

### Step 2: Start Frontend
In a separate terminal window:
```bash
# Install frontend dependencies
npm install --prefix frontend

# Launch Vite development server (Runs on http://localhost:5173)
npm run dev --prefix frontend -- --host 0.0.0.0
```

Open **`http://localhost:5173`** in your browser.

---

## 4. Default Demo Accounts

The seed script creates pre-configured accounts with instant one-click login buttons on the login screen:

| Role | Email | Password | Details |
|---|---|---|---|
| **Student (Lead Profile)** | `student@adaptiveprep.edu` | `StudentPass123!` | Abhishek Gangrade (has seeded performance telemetry) |
| **Student 2** | `aastha@adaptiveprep.edu` | `StudentPass123!` | Aastha Jain |
| **Faculty / Admin** | `admin@adaptiveprep.edu` | `AdminPass123!` | Prof. HarshPratap Singh (Question Bank Manager & System Stats) |

---

## 5. Docker Compose Deployment

To deploy the entire production stack including PostgreSQL 16:

```bash
docker compose up -d --build
```
- **Frontend SPA:** `http://localhost:5173`
- **FastAPI REST API:** `http://localhost:8000/api/v1`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **PostgreSQL Database:** `localhost:5432`

---

## 6. Automated Testing & Verification

Execute the complete automated test suite:

```bash
# Run 31 automated backend tests (Unit, Integration, Security, Lifecycle, Ablation)
source .venv/bin/activate
PYTHONPATH=. pytest backend/app/tests/ -v

# Run production frontend build
npm run build --prefix frontend
```

**Verified Test Results:**
- 15/15 Unit Tests Passing (`test_adaptive_engine.py`)
- 16/16 Integration Tests Passing (`test_api_endpoints.py`)
- Frontend: 2,386 modules compiled cleanly with 0 TypeScript/Vite errors.

---

## 7. Comprehensive Project Documentation

The complete engineering documentation is maintained in the `/docs` directory:

1. [Project Codebase Audit (`docs/PROJECT_AUDIT.md`)](docs/PROJECT_AUDIT.md): 18-dimension exhaustive architectural audit.
2. [Master Implementation Plan (`docs/IMPLEMENTATION_PLAN.md`)](docs/IMPLEMENTATION_PLAN.md): 6-phase enhancement roadmap.
3. [Technical Debt Catalog (`docs/TECHNICAL_DEBT.md`)](docs/TECHNICAL_DEBT.md): Catalog of resolved items TD-01 through TD-08.
4. [System Architecture (`docs/ARCHITECTURE.md`)](docs/ARCHITECTURE.md): Component diagrams, service boundaries, and data flow.
5. [Database Schema (`docs/DATABASE_SCHEMA.md`)](docs/DATABASE_SCHEMA.md): Complete ER diagram, table schemas, indexes, and migrations.
6. [REST API Specification (`docs/API_DOCUMENTATION.md`)](docs/API_DOCUMENTATION.md): Endpoint routes, request/response models, rate limiting, and status codes.
7. [Adaptive Recommendation Engine (`docs/RECOMMENDATION_ENGINE.md`)](docs/RECOMMENDATION_ENGINE.md): Mathematical formulations, smoothing safeguards, and factor ablation.
8. [Research Protocol & Methodology (`docs/RESEARCH_METHODOLOGY.md`)](docs/RESEARCH_METHODOLOGY.md): Experimental study design, 3-strategy evaluation, and pseudonymized dataset schema.
9. [Security Review (`docs/SECURITY_REVIEW.md`)](docs/SECURITY_REVIEW.md): Threat modeling, password hashing, JWT RBAC, answer key concealment, and rate limiting.
10. [Testing & QA Report (`docs/TESTING_REPORT.md`)](docs/TESTING_REPORT.md): Test execution matrix, coverage, and build verification.
11. [Deployment Guide (`docs/DEPLOYMENT_GUIDE.md`)](docs/DEPLOYMENT_GUIDE.md): Production deployment via Docker Compose, bare-metal setup, environment variables, and backups.

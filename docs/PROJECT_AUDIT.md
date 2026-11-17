# Comprehensive Project Audit: AdaptivePrep

**Project Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
**Institution:** Medi-Caps University, Indore  
**Project Team:** Abhishek Gangrade, Aastha Jain  
**Project Guide:** Prof. HarshPratap Singh  
**Date of Audit:** November 17, 2026  
**Auditor:** Senior Software Architect, Applied Research Engineer & QA Lead  

---

## Executive Summary

AdaptivePrep is an existing full-stack educational technology platform engineered to evaluate and deliver personalized campus placement preparation questions through a multi-factor adaptive recommendation engine. 

An exhaustive codebase inspection was conducted across all 18 target areas before applying modifications. The core foundation (FastAPI backend, React 18 frontend with Tailwind CSS and Recharts, and multi-factor recommendation math) is well-structured and functional. However, the audit revealed key gaps in persistence logging, question lifecycle management, profile settings, and strict type definitions that must be addressed for enterprise-grade production readiness.

---

## Detailed Audit Across 18 Engineering Dimensions

### 1. Existing Frontend Framework & Structure
- **Framework:** React 18.3.1, TypeScript 5.6.2, Vite 5.4.8, Tailwind CSS 3.4.13, Lucide React 0.453.0, Recharts 2.12.7.
- **Directory Structure:** Clean component separation under `frontend/src/` (`components/`, `layouts/`, `pages/`, `features/auth/`, `services/`, `types/`).
- **Defects Identified:**
  - TypeScript build error in `src/services/api.ts`: `import.meta.env.VITE_API_BASE_URL` fails TypeScript compilation (`TS2339: Property 'env' does not exist on type 'ImportMeta'`) because `src/vite-env.d.ts` is missing.
  - Absence of a dedicated Settings / Profile route and page, which is required by the project specification.
  - Absence of a dedicated Recommendation Center view where students can inspect their multi-factor decomposition ($A, R, D, E$ values) and algorithmic explanations in depth.

### 2. Existing Backend Framework & Structure
- **Framework:** Python 3.14 (compatible with 3.11/3.12), FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0.30+, Alembic 1.13+.
- **Organization:** Clean modular architecture under `backend/app/` (`core/`, `api/routes/`, `models/`, `schemas/`, `services/`, `db/`, `tests/`).
- **State:** Routers are cleanly decoupled into versioned paths under `/api/v1` (`auth`, `questions`, `practice`, `progress`, `recommendations`, `research`, `admin`).

### 3. Existing Database & Schema
- **Database Engine:** SQLite (local development and test fallback) and PostgreSQL 16 (via Psycopg 3.3.6 for production/Docker).
- **Existing Tables:** `users`, `questions`, `attempts`, `practice_sessions`, `topic_proficiencies`, `research_studies`, `research_participants`, `assessment_results`.
- **Gaps Identified:**
  - **No `recommendation_logs` table:** The recommendation engine generates real-time explanations and candidate selections, but does not persist recommendation logs with learner-state snapshots to the database.
  - **Question Metadata & Lifecycle:** Questions currently only have a binary `is_active: bool` flag. The project specification calls for a full lifecycle (`draft`, `in_review`, `published`, `archived`), version tracking (`version: int`), subtopic taxonomy, and concept tags.
  - **Attempt Schema Enhancements:** Attempts need explicit association with `question_version`, `attempt_number`, and `started_at` to guarantee historical snapshot immutability.
  - **Database File Discrepancy:** Relative path in `DATABASE_URL = "sqlite:///./adaptiveprep.db"` creates duplicate SQLite files if run from `backend/` versus project root. Must be standardized to an absolute path anchored to repository root.

### 4. Authentication and Authorization
- **Implementation:** Password hashing with `bcrypt` (12 rounds) and JWT token generation using `pyjwt` with HMAC-SHA256.
- **Roles:** `student` and `admin`. Endpoints check permissions via `get_current_user` and `get_current_admin`.
- **Data Privacy:** Students cannot query other students' attempts or proficiencies; queries strictly filter on `user_id == current_user.id`.
- **Gaps Identified:**
  - Sensitive authentication endpoints (`/api/v1/auth/login`, `/api/v1/auth/register`) lack in-memory or Redis-based rate limiting to protect against brute-force attacks.
  - Need a profile endpoint (`PATCH /api/v1/auth/profile`) allowing users to update their profile information and research consent.

### 5. Existing Student Dashboard
- **Implementation:** `frontend/src/pages/Overview.tsx` provides high-level summary cards (Attempts, Accuracy, Active Topics, Avg Speed), a dynamic recommendation spotlight card, topic proficiency bars, and recent attempt history.
- **Evaluation:** High visual polish using the `#167D74` teal palette and Inter font. Data is loaded dynamically via `GET /api/v1/progress/overview` and `GET /api/v1/recommendations/next`.

### 6. Existing Question Bank
- **Coverage:** 27 authentic technical placement questions seeded across 9 core topics: Arrays, Strings, Searching & Sorting, Basic Mathematics, Logical Reasoning, SQL & DBMS, Operating Systems, Computer Networks, and Dynamic Programming.
- **Difficulty:** Evenly distributed across Easy, Medium, and Hard tiers.
- **Data Privacy:** `QuestionStudentView` securely omits `correct_answer` and `explanation`.
- **Gaps Identified:**
  - Need admin editing and lifecycle transition endpoints (`draft` -> `in_review` -> `published` -> `archived`).
  - Need subtopic taxonomy and concept tag support.

### 7. Existing Practice Functionality
- **Implementation:** `frontend/src/pages/Practice.tsx` supports topic-specific or auto-adaptive practice mode, displays an active timer, disables option changes upon submission, and shows immediate feedback.
- **Evaluation:** Fully functional. Backend evaluates correctness on the server.

### 8. Existing Question Submission & Attempt Tracking
- **Implementation:** `POST /api/v1/practice/attempt` validates submitted answers, bounds elapsed time (3s to 1800s), writes to `attempts` table, recalculates `topic_proficiencies`, and returns proficiency delta $+/-$ with updated recommendation reason.
- **Gaps Identified:**
  - Duplicate submission / idempotency protection is not enforced at the database level.
  - Start timestamp and attempt number are not tracked on the attempt model.

### 9. Existing Adaptive Recommendation Engine
- **Implementation:** `AdaptiveRecommendationEngine` implements:
  $$S = 100 \times (0.45A + 0.25R + 0.20D + 0.10E)$$
- **Historical Accuracy ($A$):** Laplace-smoothed $(k + 1) / (n + 2)$.
- **Recent Performance ($R$):** Linear ramp recency weighting over the last 5 attempts.
- **Difficulty ($D$):** Weighted credit: Easy 0.40, Medium 0.70, Hard 1.00.
- **Efficiency ($E$):** Penalizes rushed incorrect guesses ($0.10$), rewards optimal pacing ($1.00$).
- **Difficulty Mapping:** $<40 \to$ Easy, $40-69 \to$ Medium, $\ge 70 \to$ Hard.
- **Safeguards:** Low-confidence clamping ($n < 3$), adjacent difficulty fallback, anti-repetition filtering.
- **Gaps Identified:**
  - Engine does not currently log generated recommendations into a persistent table.
  - No interface for ablation studies (disabling specific components $R$ or $E$ to measure impact during evaluation).

### 10. Existing Analytics & Charts
- **Implementation:** `frontend/src/pages/Progress.tsx` renders Recharts bar charts for topic proficiency distribution, rolling accuracy line chart, and difficulty breakdown.
- **Evaluation:** Clean, responsive, and grounded strictly in real database attempt rows.

### 11. Existing Admin Functionality
- **Implementation:** `frontend/src/pages/Admin.tsx` and `backend/app/api/routes/admin.py` provide platform metrics, question bank inventory with active toggles, and modal for adding new questions.
- **Gaps Identified:**
  - Lacks question editing and lifecycle state transitions.
  - Lacks user management listing.

### 12. Existing Research-Related Functionality
- **Implementation:** `frontend/src/pages/Research.tsx` and `backend/app/api/routes/research.py` model a research study with 3 arms: `adaptive`, `accuracy_only`, `random`. Seeded with 45 simulated participants.
- **Data Export:** Clean pseudonymized CSV export excluding names, emails, and IP addresses.
- **Gaps Identified:**
  - Diagnostic pre-test / post-test assessment workflow is not available as an interactive test mode for real students.

### 13. Existing API Endpoints
- RESTful versioned endpoints under `/api/v1` for `auth`, `questions`, `practice`, `progress`, `recommendations`, `research`, and `admin`. Centralized JSON error handlers are in place.

### 14. Existing Environment Configuration
- `.env.example` files present for backend and frontend.
- `Settings` in `config.py` validates required environment settings with fallback defaults.

### 15. Existing Deployment & Docker Configuration
- `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, and `frontend/nginx.conf` are present.
- Production multi-stage builds with Nginx reverse proxy configured.

### 16. Existing Automated Tests
- 20 Pytest unit and integration tests covering adaptive engine math and API endpoints (`test_adaptive_engine.py`, `test_api_endpoints.py`). All 20 tests pass.
- Gaps Identified: Missing tests for question lifecycle, algorithm ablation, recommendation logging, rate limiting, and profile settings.

### 17. Existing Error Handling & Validation
- Pydantic v2 schemas enforce type constraints.
- Centralized exception handler catches unhandled exceptions to prevent stack trace leaks.

### 18. Existing UI Design System
- Minimalist palette with `#167D74` teal primary accent, charcoal typography, light-neutral slate backgrounds, and restrained borders. Highly legible and accessible.

---

## Audit Classification Matrix

| Feature / Area | Status | Criticality | Remediation Required |
|---|---|---|---|
| Frontend TypeScript Compilation | **Defective** | High | Add `src/vite-env.d.ts` to satisfy Vite client types |
| Settings & Profile Page | **Missing** | Medium | Create `Settings.tsx` with user profile and research consent |
| Recommendation Logging | **Missing** | High | Add `RecommendationLog` model, migration, and service logging |
| Question Lifecycle & Metadata | **Partial** | Medium | Add `status`, `subtopic`, `concept_tags`, `version` to `Question` |
| Attempt Immutability & Protection | **Partial** | High | Add idempotency validation, `question_version`, `started_at` |
| Unified Database Anchor | **Defective** | High | Standardize `DATABASE_URL` to absolute project path |
| Diagnostic Assessment Test Mode | **Missing** | Medium | Add structured pre/post diagnostic assessment runner |
| Algorithm Ablation Suite | **Missing** | High | Add ablation unit tests & study configuration |
| Security Rate Limiting | **Missing** | High | Add brute-force protection to auth endpoints |
| Test Suite Coverage | **Partial** | High | Expand test suite to cover all new entities and edge cases |

# Security Architecture & Vulnerability Review

**Project Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform  
**Document:** `/docs/SECURITY_REVIEW.md`  
**Security Classification:** University Major Project / Production-Grade Web Application  
**Audit Date:** November 17, 2026  
**Status:** PASSED (Zero High/Critical Vulnerabilities)  

---

## 1. Threat Model & Security Posture

AdaptivePrep processes student performance data, authentication credentials, and placement examination questions. The threat model addresses four primary security domains:
1. **Academic Evaluation Integrity:** Preventing student tampering with question answer keys, timing telemetry, and proficiency calculations.
2. **Authentication Security:** Defending against credential stuffing, brute-force attacks, and session hijacking.
3. **Data Privacy & Compliance:** Protecting student identities, institutional records, and ensuring ethical de-identification in research datasets.
4. **Platform Availability & Resilience:** Preventing Denial of Service (DoS) and race conditions from duplicate attempt submissions.

---

## 2. Security Controls & Implementation Details

### 2.1 Password Security & Storage
- **Mechanism:** Passwords are never stored in plaintext. AdaptivePrep uses `passlib` with the industry-standard `bcrypt` key derivation function with an automatically salted work factor of 12 rounds.
- **Enforcement:** Enforced at registration (`UserRegister` schema) and password update boundaries.
- **Verification:** Verified via constant-time comparison in `verify_password()`.

### 2.2 Stateless Session Authorization (JWT)
- **Token Format:** Signed JSON Web Tokens (JWT) adhering to RFC 7519.
- **Algorithm:** HMAC-SHA256 (`HS256`) signed with a dedicated server secret key (`SECRET_KEY`).
- **Token Claims:** Minimal payload containing:
  - `sub`: User ID
  - `role`: Role string (`student` or `admin`)
  - `exp`: Expiration timestamp (default: 1440 minutes / 24 hours)
- **RBAC Enforcement:** FastAPI dependency injection enforces roles:
  - `get_current_user`: Requires valid, active user token.
  - `get_current_admin`: Requires valid, active user token where `user.role == "admin"`. Students attempting to access `/api/v1/admin/*` are rejected with HTTP `403 Forbidden`.

### 2.3 Answer Key Concealment & Client Isolation
- **Vulnerability Addressed:** Client-side answer inspection (inspecting network requests or browser memory to view correct answers before answering).
- **Protection Architecture:**
  - `QuestionStudentView` strictly projects only public problem fields (`id`, `title`, `statement`, `topic`, `subtopic`, `difficulty`, `options`, `expected_duration_seconds`, `version`, `concept_tags`).
  - The ground-truth `correct_answer` and `explanation` are completely omitted from student GET queries (`/api/v1/questions`, `/api/v1/practice/next`, `/api/v1/recommendations/next`).
  - Answer correctness is evaluated strictly server-side upon receiving `POST /api/v1/practice/attempt`.
  - Verified by automated test: `test_questions_student_privacy`.

### 2.4 Server-Side Validation & Input Sanitization
- All request payloads are strictly validated using **Pydantic v2**:
  - Email addresses: Validated using RFC 5322 compliant regex and Pydantic `EmailStr`.
  - Difficulty strings: Constrained by pattern regex `^(Easy|Medium|Hard)$`.
  - Question lifecycle status: Constrained by regex `^(draft|in_review|published|archived)$`.
  - Option count: Minimum 2 options required, duplicate options rejected.
  - Solving duration: Clamped between $3$ seconds and $1800$ seconds (30 minutes) on the server to prevent integer overflow and anomalous timing skew.

### 2.5 Duplicate Attempt Idempotency Protection
- **Vulnerability Addressed:** Network retries, rapid double-clicking, or script re-submissions causing duplicated attempt logging and distorted proficiency scores.
- **Protection Architecture:**
  - `PerformanceService.record_attempt` executes a duplicate check for the same student, question ID, and submitted answer within a 5-second sliding window.
  - If a matching attempt exists within 5 seconds, the existing attempt feedback is returned safely without incrementing observation counts or re-triggering proficiency calculations.
  - Verified by automated test: `test_duplicate_attempt_idempotency`.

### 2.6 Authentication Rate Limiting
- **Vulnerability Addressed:** Automated brute-force credential stuffing attacks against `/api/v1/auth/login` and `/api/v1/auth/register`.
- **Protection Architecture:**
  - In-memory sliding-window IP rate limiter (`check_rate_limit`) in `backend/app/api/routes/auth.py`.
  - Max limit: **15 requests per minute** per client IP.
  - Requests exceeding the threshold are blocked immediately with HTTP `429 Too Many Requests`.
  - Verified by automated test: `test_rate_limiting_protection`.

### 2.7 HTTP Security Headers & Middleware
Every HTTP response emitted by the FastAPI application includes the following protective headers:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing attacks.
- `X-Frame-Options: DENY`: Prevents Clickjacking attacks by forbidding iframe embedding.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts referrer information leakage on cross-origin navigation.
- `X-Process-Time`: Provides execution timing telemetry for performance and audit logging.
- Verified by automated test: `test_security_headers`.

### 2.8 Cross-Origin Resource Sharing (CORS)
- CORS middleware strictly limits allowed origins to authorized frontend domains.
- Wildcard credentials with `allow_origins=["*"]` are explicitly disallowed. In development, explicit localhost ports (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`) are permitted.

### 2.9 SQL Injection & Cross-Site Scripting (XSS) Defenses
- **SQL Injection:** All database queries are executed via SQLAlchemy 2.0 ORM with parameterized statements. Raw SQL string concatenation is completely absent across the codebase.
- **Cross-Site Scripting (XSS):** React 18 JSX enforces automatic context-aware escaping for all dynamic strings rendered in the DOM. User inputs are never rendered using `dangerouslySetInnerHTML`.

### 2.10 Research Privacy & Data Minimization
- Exported research datasets (`GET /api/v1/research/studies/{id}/export`) completely exclude all Personally Identifiable Information (PII).
- Student names, email addresses, hashed passwords, IP addresses, and user database IDs are stripped.
- Records are keyed solely by pseudonymous codes (e.g. `PART-1001-ADAP`).
- Verified by automated test: `test_research_pseudonymized_export`.

---

## 3. Security Verification Checklist

| Security Control | Implementation Location | Test Case / Verification | Status |
|---|---|---|---|
| Bcrypt password hashing | `backend/app/core/security.py` | `test_student_login`, `test_invalid_login` | **PASS** |
| JWT RBAC validation | `backend/app/core/dependencies.py` | `test_questions_student_privacy`, `test_admin_question_view` | **PASS** |
| Answer key student privacy | `backend/app/schemas/__init__.py` | `test_questions_student_privacy` | **PASS** |
| Server-side evaluation | `backend/app/services/performance_service.py` | `test_practice_recommendation_and_attempt_flow` | **PASS** |
| Attempt idempotency | `backend/app/services/performance_service.py` | `test_duplicate_attempt_idempotency` | **PASS** |
| Auth rate limiting (15/min) | `backend/app/api/routes/auth.py` | `test_rate_limiting_protection` | **PASS** |
| Strict security headers | `backend/app/main.py` | `test_security_headers` | **PASS** |
| Pseudonymized CSV export | `backend/app/services/research_service.py` | `test_research_pseudonymized_export` | **PASS** |
| Input sanitization | Pydantic v2 schemas | All test suites | **PASS** |

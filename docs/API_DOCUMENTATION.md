# AdaptivePrep REST API Specification

**Project Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform  
**Document:** `/docs/API_DOCUMENTATION.md`  
**Base URL:** `/api/v1`  
**Interactive Docs:** Swagger UI at `http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`  
**Date:** November 17, 2026  

---

## 1. Global Standards & Conventions

- **Authentication:** Bearer JWT in `Authorization: Bearer <token>` header.
- **Content-Type:** `application/json` for requests and responses (except CSV exports).
- **Security Headers Included on All Responses:**
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `X-Process-Time: <seconds>`
- **Rate Limiting:** Authentication routes (`/auth/login`, `/auth/register`) are throttled to 15 requests per minute per IP address. Breaching the threshold returns HTTP `429 Too Many Requests`.

---

## 2. Authentication & Profile Endpoints (`/api/v1/auth`)

### `POST /api/v1/auth/register`
Creates a new student account.
- **Rate Limited:** Yes (15 req/min)
- **Request Body:**
  ```json
  {
    "display_name": "Aastha Jain",
    "email": "aastha@adaptiveprep.edu",
    "password": "StrongPassword123!",
    "college": "Medi-Caps University",
    "target_role": "Software Development Engineer (SDE)",
    "research_consent": true
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": 3,
      "email": "aastha@adaptiveprep.edu",
      "display_name": "Aastha Jain",
      "role": "student",
      "is_active": true,
      "college": "Medi-Caps University",
      "target_role": "Software Development Engineer (SDE)",
      "research_consent": true,
      "created_at": "2026-11-17T08:00:00Z"
    }
  }
  ```

### `POST /api/v1/auth/login`
Authenticates user credentials and issues a stateless access token.
- **Rate Limited:** Yes (15 req/min)
- **Request Body:**
  ```json
  {
    "email": "student@adaptiveprep.edu",
    "password": "StudentPass123!"
  }
  ```
- **Response (200 OK):** Token object with embedded user profile.
- **Response (401 Unauthorized):** Invalid credentials.
- **Response (429 Too Many Requests):** Rate limit exceeded.

### `GET /api/v1/auth/me`
Fetches the currently authenticated user's profile.
- **Headers:** `Authorization: Bearer <token>`
- **Response (200 OK):** `UserOut` model.

### `PATCH /api/v1/auth/profile`
Updates profile details, target career role, or research consent preferences.
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:**
  ```json
  {
    "display_name": "Aastha Jain",
    "college": "Medi-Caps University, Indore",
    "target_role": "Full Stack Engineer",
    "research_consent": true
  }
  ```
- **Response (200 OK):** Updated `UserOut` model.

---

## 3. Practice & Attempt Endpoints (`/api/v1/practice`)

### `GET /api/v1/practice/next`
Returns the next adaptively selected question based on student proficiency.
- **Headers:** `Authorization: Bearer <token>`
- **Query Parameters:** `topic` (optional string, e.g. `Arrays`)
- **Response (200 OK):**
  ```json
  {
    "question": {
      "id": 14,
      "title": "Two Sum Problem",
      "statement": "Given an array of integers nums and an integer target...",
      "topic": "Arrays",
      "subtopic": "Hash Maps & Two Pointers",
      "difficulty": "Easy",
      "question_type": "multiple_choice",
      "options": ["O(N^2) brute force", "O(N) with Hash Map", "O(N log N) sorting", "O(1) space"],
      "expected_duration_seconds": 90,
      "version": 1,
      "concept_tags": ["arrays", "hash-table"]
    },
    "recommendation_reason": "Recommended to calibrate confidence in Arrays based on baseline proficiency (50.0).",
    "topic": "Arrays",
    "difficulty": "Easy"
  }
  ```
- *Note:* `correct_answer` and `explanation` are deliberately omitted to preserve academic evaluation integrity.

### `POST /api/v1/practice/attempt`
Submits a student's answer, performs server-side evaluation, updates topic proficiency, and returns immediate feedback.
- **Headers:** `Authorization: Bearer <token>`
- **Idempotency Protection:** Consecutive duplicate submissions for the same question within 5 seconds return existing feedback without double-counting.
- **Request Body:**
  ```json
  {
    "question_id": 14,
    "submitted_answer": "O(N) with Hash Map",
    "time_taken_seconds": 65,
    "started_at": "2026-11-17T08:10:00Z"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "attempt_id": 28,
    "question_id": 14,
    "submitted_answer": "O(N) with Hash Map",
    "is_correct": true,
    "correct_answer": "O(N) with Hash Map",
    "explanation": "Using a hash table provides amortized O(1) lookups yielding O(N) total runtime.",
    "time_taken_seconds": 65,
    "topic": "Arrays",
    "difficulty": "Easy",
    "updated_proficiency": 58.2,
    "proficiency_delta": 8.2,
    "next_recommendation_reason": "Demonstrated steady progress. Moving toward Medium difficulty.",
    "next_question": { ... }
  }
  ```

---

## 4. Recommendations & Explainability (`/api/v1/recommendations`)

### `GET /api/v1/recommendations/next`
Returns the next question along with the complete 4-factor component breakdown ($A, R, D, E$).
- **Response (200 OK):**
  ```json
  {
    "question": { ... },
    "estimated_proficiency": 64.5,
    "target_difficulty": "Medium",
    "confidence_level": "moderate",
    "observation_count": 5,
    "reason": "Maintaining consistent accuracy; practicing Medium questions to solidify proficiency.",
    "topic": "Dynamic Programming",
    "algorithm_version": "v1.0.0",
    "component_breakdown": {
      "A": 0.65,
      "R": 0.72,
      "D": 0.58,
      "E": 0.85
    }
  }
  ```

### `GET /api/v1/recommendations/history`
Retrieves the student's chronological audit log of recommendations.
- **Query Parameters:** `limit` (int, default 20, max 100)
- **Response (200 OK):**
  ```json
  [
    {
      "id": 12,
      "question_id": 14,
      "question_version": 1,
      "target_topic": "Arrays",
      "target_difficulty": "Medium",
      "estimated_proficiency": 58.2,
      "confidence_level": "moderate",
      "selection_reason": "Advancing to Medium tier following consistent Easy problem mastery.",
      "learner_state_snapshot": {
        "A": 0.62,
        "R": 0.70,
        "D": 0.55,
        "E": 0.80,
        "n": 4
      },
      "algorithm_version": "v1.0.0",
      "created_at": "2026-11-17T08:12:00Z"
    }
  ]
  ```

### `GET /api/v1/recommendations/explanation`
Returns detailed algorithmic diagnostic explanation for a given topic.
- **Query Parameters:** `topic` (string, required)
- **Response (200 OK):** Score, formula, component breakdown, weights, and detailed prose explanation.

---

## 5. Progress & Analytics Endpoints (`/api/v1/progress`)

### `GET /api/v1/progress/overview`
Aggregated telemetry for the authenticated student.
- **Response (200 OK):**
  - `total_attempts`: Total questions answered
  - `overall_accuracy`: Percentage accuracy
  - `topic_proficiencies`: Array of all 9 topics with estimated proficiency ($S$), confidence level, and observation counts
  - `accuracy_trend`: Chronological rolling accuracy points
  - `difficulty_breakdown`: Easy, Medium, Hard attempt distributions

---

## 6. Question Bank Endpoints (`/api/v1/questions`)

### `GET /api/v1/questions/topics/all`
Returns all 9 placement topic domains.

### `GET /api/v1/questions`
Lists questions filtered by topic and difficulty.
- **Role Enforcement:** Non-admin students only receive `status = 'published'` and `is_active = true` questions without `correct_answer`. Admins receive all questions including answer keys and explanations.

---

## 7. Administrative Endpoints (`/api/v1/admin`)
*Requires Admin role (`role == 'admin'`)*

### `GET /api/v1/admin/stats`
Platform-wide statistics: total users, student count, active questions, total attempts, platform accuracy, and topic distributions.

### `GET /api/v1/admin/users`
Lists registered users with pagination (`skip`, `limit`).

### `POST /api/v1/admin/questions`
Creates a new question with subtopic, concept tags, expected duration, and initial status (`draft` or `published`).

### `PUT /api/v1/admin/questions/{question_id}`
Updates problem statement, options, or answer key. If content or answer changes, question `version` is automatically incremented.

### `PATCH /api/v1/admin/questions/{question_id}/status`
Transitions question lifecycle stage (`new_status` must be `draft`, `in_review`, `published`, or `archived`).

### `PATCH /api/v1/admin/questions/{question_id}/toggle-active`
Toggles active state.

---

## 8. Research & Evaluation Endpoints (`/api/v1/research`)

### `GET /api/v1/research/studies`
Lists registered research evaluation studies.

### `GET /api/v1/research/studies/{study_id}/summary`
Comparative metrics across the 3 experimental strategies:
1. `adaptive` (Multi-Factor $S$-score)
2. `accuracy_only` (Traditional percentage)
3. `random` (Uniform random baseline)

### `GET /api/v1/research/studies/{study_id}/export`
Downloads pseudonymized participant evaluation dataset as a CSV file for statistical analysis (e.g. SPSS, R, Python pandas). Excludes student names and email addresses.

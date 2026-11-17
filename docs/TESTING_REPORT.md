# AdaptivePrep Test Execution & Quality Assurance Report

**Project Title:** AdaptivePrep: An Explainable, Performance-Driven Adaptive Learning Platform for Personalized Placement Preparation  
**Document:** `/docs/TESTING_REPORT.md`  
**Test Framework:** Pytest 9.2.0 + HTTPX TestClient (Backend) & TypeScript / Vite 5 (Frontend)  
**Execution Date:** November 17, 2026  
**Overall Status:** **100% PASSED (31/31 Tests Passing)**  

---

## 1. Test Suite Summary & Matrix

The automated quality assurance matrix spans unit, integration, algorithmic, regression, security, and build verification:

| Category | Test File | Tests Run | Passed | Failed | Execution Time |
|---|---|---|---|---|---|
| **Mathematical & Algorithmic Unit Tests** | `backend/app/tests/test_adaptive_engine.py` | 15 | 15 | 0 | 0.10s |
| **API & Workflow Integration Tests** | `backend/app/tests/test_api_endpoints.py` | 16 | 16 | 0 | 3.33s |
| **Frontend TypeScript & Vite Compilation** | `frontend/` (`npm run build`) | 2,386 modules | Pass | 0 | 1.99s |
| **Database Migrations** | `alembic upgrade head` | 2 revisions | Pass | 0 | 0.45s |
| **Total Automated Tests** | **Full Suite** | **31** | **31** | **0** | **3.43s** |

---

## 2. Unit Test Specifications (`test_adaptive_engine.py`)

15 unit tests rigorously verify the mathematical soundness of the multi-factor recommendation engine:

1. `test_no_prior_attempts`: Verifies cold-start behavior ($n=0$ attempts), returning diagnostic baseline score ($S \in [40, 60]$), low confidence, and Medium difficulty recommendation.
2. `test_one_correct_attempt_safeguard`: Proves Laplace smoothing prevents a single correct attempt from artificially spiking proficiency to 100 ($A = (1+1)/(1+2) = 0.667$, score bounded below 90).
3. `test_one_incorrect_attempt_safeguard`: Proves a single incorrect attempt does not crash score to 0 ($A = (0+1)/(1+2) = 0.333$, score remains above 10).
4. `test_strong_recent_improvement`: Verifies that recent success after historical struggles elevates the recency component ($R > A$) and transitions the explanation to highlight steady improvement.
5. `test_declining_recent_performance`: Verifies that recent failures lower $R < A$, prompting remediation recommendations.
6. `test_difficulty_thresholds`: Validates transitions across Easy ($<40$), Medium ($40-69$), and Hard ($\ge 70$).
7. `test_solving_efficiency_safeguards`: Proves that rushed errors ($t < 0.4 t_{\text{expected}}$ and wrong) are severely penalized ($E \le 0.20$), while optimal answers receive $E = 1.00$.
8. `test_candidate_selection_anti_repetition`: Ensures previously attempted questions are filtered out of candidate pools.
9. `test_candidate_selection_fallback_when_difficulty_exhausted`: Proves that when target difficulty questions are exhausted, the engine falls back to the adjacent difficulty tier rather than failing.
10. `test_reproducibility`: Confirms that identical attempt histories produce mathematically identical scores, component values, and explanations.
11. `test_factor_ablation_recency_disabled`: Proves disabling $R$ prevents recent momentum from dominating the score.
12. `test_factor_ablation_efficiency_disabled`: Proves proficiency calculation operates deterministically without efficiency $E$.
13. `test_factor_ablation_accuracy_only`: Proves ablating $R, D, E$ collapses the model to pure Laplace-smoothed accuracy ($A$).
14. `test_timing_boundary_safeguards`: Confirms negative durations, 0 duration, and extreme durations ($t > 2000$s) are safely clamped without throwing exceptions.
15. `test_difficulty_weight_differential`: Confirms solving Hard questions earns greater $D$ credit than solving Easy questions ($1.00$ vs $0.40$).

---

## 3. Integration Test Specifications (`test_api_endpoints.py`)

16 integration tests verify end-to-end service workflows, authentication, data privacy, and security controls:

1. `test_health_endpoint`: Asserts `/health` returns status `healthy` and algorithm version `v1.0.0`.
2. `test_root_endpoint`: Asserts root `/` returns institutional metadata for Medi-Caps University, Indore.
3. `test_student_login`: Validates successful student authentication, password verification, and JWT bearer token issuance.
4. `test_invalid_login`: Validates rejection of bad credentials with HTTP 401.
5. `test_questions_student_privacy`: **Critical Privacy Check:** Ensures student question views never expose `correct_answer` or `explanation`.
6. `test_admin_question_view`: Confirms staff/admin users can view full question details including answer keys.
7. `test_practice_recommendation_and_attempt_flow`: Executes the complete student practice loop (fetch next recommended question, submit answer, receive server-calculated correctness, explanation, and proficiency delta).
8. `test_progress_overview`: Confirms progress telemetry aggregates attempt count, accuracy, and all 9 topic proficiencies.
9. `test_research_study_summary`: Validates research study summary across the 3 arms: `adaptive`, `accuracy_only`, and `random`.
10. `test_research_pseudonymized_export`: **Ethical Privacy Check:** Confirms CSV export is formatted properly with pseudonymous codes and strictly strips names, emails, and student identities.
11. `test_security_headers`: Confirms responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, and `X-Process-Time`.
12. `test_user_profile_update`: Tests `PATCH /api/v1/auth/profile` updating college, target role, and research consent.
13. `test_recommendation_history_and_logging`: Validates that generating recommendations creates persistent records in `recommendation_logs` with learner state snapshots.
14. `test_question_lifecycle_and_versioning`: Tests question creation, version incrementing on statement update, and lifecycle status transitions (`draft` $\to$ `in_review` $\to$ `published` $\to$ `archived`).
15. `test_duplicate_attempt_idempotency`: Verifies that rapid duplicate submissions within 5 seconds return the existing attempt feedback without double-counting attempts.
16. `test_rate_limiting_protection`: Validates that exceeding 15 authentication attempts within 60 seconds triggers HTTP 429 Too Many Requests.

---

## 4. Test Execution Output (Exact Console Transcript)

```text
platform darwin -- Python 3.14.3, pytest-9.2.0, pluggy-1.7.0 -- /Users/apple/Desktop/AdaptivePrep/.venv/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/apple/Desktop/AdaptivePrep
plugins: asyncio-1.4.1, anyio-4.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 31 items

backend/app/tests/test_adaptive_engine.py::test_no_prior_attempts PASSED [  3%]
backend/app/tests/test_adaptive_engine.py::test_one_correct_attempt_safeguard PASSED [  6%]
backend/app/tests/test_adaptive_engine.py::test_one_incorrect_attempt_safeguard PASSED [  9%]
backend/app/tests/test_adaptive_engine.py::test_strong_recent_improvement PASSED [ 12%]
backend/app/tests/test_adaptive_engine.py::test_declining_recent_performance PASSED [ 16%]
backend/app/tests/test_adaptive_engine.py::test_difficulty_thresholds PASSED [ 19%]
backend/app/tests/test_adaptive_engine.py::test_solving_efficiency_safeguards PASSED [ 22%]
backend/app/tests/test_adaptive_engine.py::test_candidate_selection_anti_repetition PASSED [ 25%]
backend/app/tests/test_adaptive_engine.py::test_candidate_selection_fallback_when_difficulty_exhausted PASSED [ 29%]
backend/app/tests/test_adaptive_engine.py::test_reproducibility PASSED   [ 32%]
backend/app/tests/test_adaptive_engine.py::test_factor_ablation_recency_disabled PASSED [ 35%]
backend/app/tests/test_adaptive_engine.py::test_factor_ablation_efficiency_disabled PASSED [ 38%]
backend/app/tests/test_adaptive_engine.py::test_factor_ablation_accuracy_only PASSED [ 41%]
backend/app/tests/test_adaptive_engine.py::test_timing_boundary_safeguards PASSED [ 45%]
backend/app/tests/test_adaptive_engine.py::test_difficulty_weight_differential PASSED [ 48%]
backend/app/tests/test_api_endpoints.py::test_health_endpoint PASSED     [ 51%]
backend/app/tests/test_api_endpoints.py::test_root_endpoint PASSED       [ 54%]
backend/app/tests/test_api_endpoints.py::test_student_login PASSED       [ 58%]
backend/app/tests/test_api_endpoints.py::test_invalid_login PASSED       [ 61%]
backend/app/tests/test_api_endpoints.py::test_questions_student_privacy PASSED [ 64%]
backend/app/tests/test_api_endpoints.py::test_admin_question_view PASSED [ 67%]
backend/app/tests/test_api_endpoints.py::test_practice_recommendation_and_attempt_flow PASSED [ 70%]
backend/app/tests/test_api_endpoints.py::test_progress_overview PASSED   [ 74%]
backend/app/tests/test_api_endpoints.py::test_research_study_summary PASSED [ 77%]
backend/app/tests/test_api_endpoints.py::test_research_pseudonymized_export PASSED [ 80%]
backend/app/tests/test_api_endpoints.py::test_security_headers PASSED    [ 83%]
backend/app/tests/test_api_endpoints.py::test_user_profile_update PASSED [ 87%]
backend/app/tests/test_api_endpoints.py::test_recommendation_history_and_logging PASSED [ 90%]
backend/app/tests/test_api_endpoints.py::test_question_lifecycle_and_versioning PASSED [ 93%]
backend/app/tests/test_api_endpoints.py::test_duplicate_attempt_idempotency PASSED [ 96%]
backend/app/tests/test_api_endpoints.py::test_rate_limiting_protection PASSED [100%]

======================== 31 passed, 1 warning in 3.43s =========================
```

---

## 5. Frontend Production Build Verification

```text
$ npm run build --prefix frontend

> adaptiveprep-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
✓ 2386 modules transformed.
dist/index.html                   1.06 kB │ gzip:   0.60 kB
dist/assets/index-CAJE_PZK.css   26.72 kB │ gzip:   5.37 kB
dist/assets/index-p6AmguC2.js   645.24 kB │ gzip: 180.77 kB
✓ built in 1.99s
```
- **TypeScript Errors:** 0
- **Bundle Generation:** Complete and verified in `frontend/dist/`.

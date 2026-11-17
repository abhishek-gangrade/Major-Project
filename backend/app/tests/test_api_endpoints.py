import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.core.database import Base, get_db
from backend.app.db.seed import seed_database
from backend.app.core.security import create_access_token

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "algorithm_version" in data


def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "AdaptivePrep" in data["message"]
    assert "Medi-Caps University, Indore" in data["institution"]


def test_student_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "student@adaptiveprep.edu"
    assert data["user"]["role"] == "student"


def test_invalid_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "detail" in res.json()


def test_questions_student_privacy():
    """Verify that student view NEVER exposes correct_answer or explanation."""
    # Login as student
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/questions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) > 0
    first_q = questions[0]
    assert "title" in first_q
    assert "statement" in first_q
    assert "options" in first_q
    # PRIVACY CHECK:
    assert "correct_answer" not in first_q
    assert "explanation" not in first_q


def test_admin_question_view():
    """Verify that admin can view full question details including correct_answer."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@adaptiveprep.edu",
        "password": "AdminPass123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/questions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    questions = res.json()
    assert len(questions) > 0
    first_q = questions[0]
    assert "correct_answer" in first_q
    assert "explanation" in first_q


def test_practice_recommendation_and_attempt_flow():
    """Verify complete practice cycle: get recommended question, submit answer, verify feedback."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch next practice question
    next_res = client.get("/api/v1/practice/next?topic=Arrays", headers=headers)
    assert next_res.status_code == 200
    rec = next_res.json()
    assert "question" in rec
    assert "recommendation_reason" in rec
    q_id = rec["question"]["id"]
    options = rec["question"]["options"]

    # 2. Submit an answer (server calculates correctness)
    submit_res = client.post("/api/v1/practice/attempt", json={
        "question_id": q_id,
        "submitted_answer": options[0],
        "time_taken_seconds": 65
    }, headers=headers)
    assert submit_res.status_code == 200
    feedback = submit_res.json()
    assert "is_correct" in feedback
    assert "correct_answer" in feedback
    assert "explanation" in feedback
    assert "updated_proficiency" in feedback
    assert "proficiency_delta" in feedback
    assert "next_recommendation_reason" in feedback


def test_progress_overview():
    """Verify that progress overview loads aggregated metrics for the student."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/progress/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_attempts"] > 0
    assert "overall_accuracy" in data
    assert "topic_proficiencies" in data
    assert len(data["topic_proficiencies"]) == 9  # all 9 placement topics represented
    assert "accuracy_trend" in data
    assert "difficulty_breakdown" in data


def test_research_study_summary():
    """Verify research study metrics compare Adaptive, Accuracy-Only, and Random strategies."""
    res = client.get("/api/v1/research/studies")
    assert res.status_code == 200
    studies = res.json()
    assert len(studies) > 0
    study_id = studies[0]["id"]

    summary_res = client.get(f"/api/v1/research/studies/{study_id}/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert "strategies" in summary
    assert len(summary["strategies"]) == 3
    strat_names = [s["strategy"] for s in summary["strategies"]]
    assert "adaptive" in strat_names
    assert "accuracy_only" in strat_names
    assert "random" in strat_names
    assert "data_dictionary" in summary
    assert "assumptions_and_limitations" in summary


def test_research_pseudonymized_export():
    """Verify CSV export is properly formatted and excludes personal identifiers."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    export_res = client.get("/api/v1/research/studies/1/export", headers=headers)
    assert export_res.status_code == 200
    assert export_res.headers["content-type"].startswith("text/csv")
    csv_text = export_res.text
    # Check headers
    assert "participant_code" in csv_text
    assert "assigned_strategy" in csv_text
    assert "score_gain_percentage_points" in csv_text
    # Ensure no emails or student names leaked in CSV
    assert "student@adaptiveprep.edu" not in csv_text
    assert "Abhishek" not in csv_text


def test_security_headers():
    """Verify that every HTTP response carries strict production security headers."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "x-process-time" in res.headers


def test_user_profile_update():
    """Verify student profile and research consent updates via PATCH /auth/profile."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    update_payload = {
        "display_name": "Aastha Jain (Student)",
        "college": "Medi-Caps University, Indore",
        "target_role": "Full Stack Engineer",
        "research_consent": True,
    }
    patch_res = client.patch("/api/v1/auth/profile", json=update_payload, headers=headers)
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["display_name"] == "Aastha Jain (Student)"
    assert data["college"] == "Medi-Caps University, Indore"
    assert data["target_role"] == "Full Stack Engineer"
    assert data["research_consent"] is True


def test_recommendation_history_and_logging():
    """Verify recommendation generation creates persistent RecommendationLog entries with learner snapshots."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger recommendation
    rec_res = client.get("/api/v1/recommendations/next?topic=Strings", headers=headers)
    assert rec_res.status_code == 200

    # Verify log entry exists in audit history
    hist_res = client.get("/api/v1/recommendations/history", headers=headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) > 0
    latest_log = history[0]
    assert "question_id" in latest_log
    assert "target_difficulty" in latest_log
    assert "selection_reason" in latest_log
    assert "learner_state_snapshot" in latest_log
    assert "estimated_proficiency" in latest_log
    assert latest_log["algorithm_version"] is not None


def test_question_lifecycle_and_versioning():
    """Verify admin question creation, content update version incrementing, and status transitions."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "admin@adaptiveprep.edu",
        "password": "AdminPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a draft question
    new_q = {
        "title": "Reverse Words in a String III",
        "statement": "Given a string s, reverse the order of characters in each word.",
        "topic": "Strings",
        "subtopic": "Two Pointers",
        "difficulty": "Easy",
        "expected_duration_seconds": 90,
        "options": ["Split and reverse", "Two pointer swap", "Stack reversal", "Bit manipulation"],
        "correct_answer": "Two pointer swap",
        "explanation": "Using two pointers between whitespace delimiters provides O(N) time and O(1) extra space.",
        "concept_tags": ["two-pointers", "string-manipulation"],
        "status": "draft",
    }
    create_res = client.post("/api/v1/admin/questions", json=new_q, headers=headers)
    assert create_res.status_code == 201
    q_data = create_res.json()
    q_id = q_data["id"]
    assert q_data["version"] == 1
    assert q_data["subtopic"] == "Two Pointers"

    # 2. Update question statement -> triggers version increment to 2
    update_payload = {
        "statement": "Given a string s, reverse the order of characters in each word while preserving whitespace.",
    }
    update_res = client.put(f"/api/v1/admin/questions/{q_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_q = update_res.json()
    assert updated_q["version"] == 2
    assert "preserving whitespace" in updated_q["statement"]

    # 3. Transition status from draft -> in_review -> published
    review_res = client.patch(f"/api/v1/admin/questions/{q_id}/status?new_status=in_review", headers=headers)
    assert review_res.status_code == 200
    assert review_res.json()["status"] == "in_review"

    pub_res = client.patch(f"/api/v1/admin/questions/{q_id}/status?new_status=published", headers=headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "published"
    assert pub_res.json()["is_active"] is True

    # 4. Transition to archived
    archive_res = client.patch(f"/api/v1/admin/questions/{q_id}/status?new_status=archived", headers=headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "archived"
    assert archive_res.json()["is_active"] is False


def test_duplicate_attempt_idempotency():
    """Rapid duplicate submissions within 5s return the same attempt record without double-counting."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "student@adaptiveprep.edu",
        "password": "StudentPass123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    next_res = client.get("/api/v1/practice/next?topic=Arrays", headers=headers)
    q_id = next_res.json()["question"]["id"]
    options = next_res.json()["question"]["options"]

    payload = {
        "question_id": q_id,
        "submitted_answer": options[0],
        "time_taken_seconds": 45,
    }

    # First attempt
    res1 = client.post("/api/v1/practice/attempt", json=payload, headers=headers)
    assert res1.status_code == 200
    attempt1_id = res1.json()["attempt_id"]

    # Immediate second identical attempt
    res2 = client.post("/api/v1/practice/attempt", json=payload, headers=headers)
    assert res2.status_code == 200
    attempt2_id = res2.json()["attempt_id"]

    # Must return the same attempt id (idempotent, no double calculation)
    assert attempt1_id == attempt2_id


def test_rate_limiting_protection():
    """Verify that rapid authentication requests trigger HTTP 429 Too Many Requests."""
    from backend.app.api.routes.auth import _LOGIN_ATTEMPTS
    _LOGIN_ATTEMPTS.clear()

    try:
        status_codes = []
        for i in range(16):
            res = client.post("/api/v1/auth/login", json={
                "email": "rate_limit_test@adaptiveprep.edu",
                "password": f"DummyPass{i}!"
            })
            status_codes.append(res.status_code)

        assert 429 in status_codes
        assert status_codes[-1] == 429
    finally:
        _LOGIN_ATTEMPTS.clear()



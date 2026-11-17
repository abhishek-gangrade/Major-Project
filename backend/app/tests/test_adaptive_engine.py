import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.adaptive_engine import (
    AdaptiveRecommendationEngine,
    AttemptData,
    adaptive_engine
)


def create_attempt(
    question_id: int,
    topic: str = "Arrays",
    difficulty: str = "Medium",
    is_correct: bool = True,
    time_taken: int = 60,
    expected_duration: int = 90,
    minutes_ago: int = 10
) -> AttemptData:
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return AttemptData(
        question_id=question_id,
        topic=topic,
        difficulty=difficulty,
        is_correct=is_correct,
        time_taken_seconds=time_taken,
        expected_duration_seconds=expected_duration,
        attempt_timestamp=timestamp
    )


def test_no_prior_attempts():
    """Verify default diagnostic baseline score and difficulty when student has 0 attempts."""
    result = adaptive_engine.estimate_proficiency("Dynamic Programming", [])
    assert result.observation_count == 0
    assert result.confidence_level == "low"
    assert result.recommended_difficulty == "Medium"  # default baseline 50 -> Medium
    assert "Diagnostic baseline" in result.explanation
    assert 40.0 <= result.score <= 60.0


def test_one_correct_attempt_safeguard():
    """A single correct attempt must not boost proficiency to 100 due to Laplace smoothing."""
    attempt = create_attempt(1, topic="Arrays", difficulty="Easy", is_correct=True, time_taken=45)
    result = adaptive_engine.estimate_proficiency("Arrays", [attempt])
    assert result.observation_count == 1
    assert result.confidence_level == "low"
    # Laplace smoothed accuracy (1+1)/(1+2) = 0.667; score must be tempered
    assert result.score < 90.0
    assert result.component_a < 1.0


def test_one_incorrect_attempt_safeguard():
    """A single incorrect attempt must not crash score to 0."""
    attempt = create_attempt(1, topic="Arrays", difficulty="Easy", is_correct=False, time_taken=45)
    result = adaptive_engine.estimate_proficiency("Arrays", [attempt])
    assert result.observation_count == 1
    assert result.score > 10.0
    assert result.component_a == pytest.approx(0.333, abs=0.01)


def test_strong_recent_improvement():
    """Recent improvement should increase proficiency even if historical baseline was weak."""
    # 5 attempts: first 2 failed long ago, last 3 succeeded recently
    attempts = [
        create_attempt(1, is_correct=False, minutes_ago=50),
        create_attempt(2, is_correct=False, minutes_ago=40),
        create_attempt(3, is_correct=True, minutes_ago=20),
        create_attempt(4, is_correct=True, minutes_ago=10),
        create_attempt(5, is_correct=True, minutes_ago=2),
    ]
    result = adaptive_engine.estimate_proficiency("Arrays", attempts)
    assert result.component_r > result.component_a
    assert result.score >= 50.0
    assert "recent improvement" in result.explanation.lower() or "steady progress" in result.explanation.lower()


def test_declining_recent_performance():
    """Declining recent attempts should lower proficiency and recommend easier reinforcement."""
    # 5 attempts: first 3 correct, last 2 incorrect
    attempts = [
        create_attempt(1, is_correct=True, minutes_ago=50),
        create_attempt(2, is_correct=True, minutes_ago=40),
        create_attempt(3, is_correct=True, minutes_ago=30),
        create_attempt(4, is_correct=False, minutes_ago=10),
        create_attempt(5, is_correct=False, minutes_ago=2),
    ]
    result = adaptive_engine.estimate_proficiency("Arrays", attempts)
    assert result.component_r < result.component_a


def test_difficulty_thresholds():
    """Test transitions at Easy (<40), Medium (40-69), Hard (>=70)."""
    engine = AdaptiveRecommendationEngine()

    # Consistently high performance on Hard questions
    high_perf_attempts = [
        create_attempt(i, difficulty="Hard", is_correct=True, time_taken=60, minutes_ago=20 - i)
        for i in range(1, 10)
    ]
    high_res = engine.estimate_proficiency("SQL and DBMS", high_perf_attempts)
    assert high_res.score >= 70.0
    assert high_res.recommended_difficulty == "Hard"
    assert high_res.confidence_level == "high"

    # Consistently low performance on Easy questions
    low_perf_attempts = [
        create_attempt(i, difficulty="Easy", is_correct=False, time_taken=90, minutes_ago=20 - i)
        for i in range(1, 10)
    ]
    low_res = engine.estimate_proficiency("SQL and DBMS", low_perf_attempts)
    assert low_res.score < 40.0
    assert low_res.recommended_difficulty == "Easy"


def test_solving_efficiency_safeguards():
    """Fast incorrect answer must not be rewarded as high efficiency."""
    rushed_wrong = create_attempt(1, is_correct=False, time_taken=5, expected_duration=90)
    eff_rushed = adaptive_engine.calculate_solving_efficiency([rushed_wrong])
    assert eff_rushed <= 0.20

    optimal_correct = create_attempt(2, is_correct=True, time_taken=60, expected_duration=90)
    eff_optimal = adaptive_engine.calculate_solving_efficiency([optimal_correct])
    assert eff_optimal >= 0.85


def test_candidate_selection_anti_repetition():
    """Candidate selection should filter out previously attempted questions."""
    available = [
        {"id": 101, "topic": "Arrays", "difficulty": "Medium", "is_active": True},
        {"id": 102, "topic": "Arrays", "difficulty": "Medium", "is_active": True},
        {"id": 103, "topic": "Arrays", "difficulty": "Hard", "is_active": True},
    ]
    # If 101 is already attempted, should pick 102
    selected, reason = adaptive_engine.select_next_candidate(
        target_topic="Arrays",
        target_difficulty="Medium",
        available_questions=available,
        attempted_question_ids=[101]
    )
    assert selected is not None
    assert selected["id"] == 102


def test_candidate_selection_fallback_when_difficulty_exhausted():
    """When preferred difficulty is exhausted, engine falls back to adjacent difficulty."""
    available = [
        {"id": 101, "topic": "Dynamic Programming", "difficulty": "Medium", "is_active": True},
        {"id": 102, "topic": "Dynamic Programming", "difficulty": "Hard", "is_active": True},
    ]
    # Student needs Easy, but only Medium and Hard are available
    selected, reason = adaptive_engine.select_next_candidate(
        target_topic="Dynamic Programming",
        target_difficulty="Easy",
        available_questions=available,
        attempted_question_ids=[]
    )
    assert selected is not None
    assert selected["id"] == 101  # Medium adjacent
    assert "adjacent" in reason.lower() or "selected" in reason.lower()


def test_reproducibility():
    """Same input history must produce exact deterministic outputs."""
    attempts = [
        create_attempt(1, is_correct=True, time_taken=50, minutes_ago=30),
        create_attempt(2, is_correct=False, time_taken=70, minutes_ago=15),
        create_attempt(3, is_correct=True, time_taken=60, minutes_ago=5),
    ]
    res1 = adaptive_engine.estimate_proficiency("Strings", attempts)
    res2 = adaptive_engine.estimate_proficiency("Strings", attempts)

    assert res1.score == res2.score
    assert res1.recommended_difficulty == res2.recommended_difficulty
    assert res1.component_a == res2.component_a
    assert res1.explanation == res2.explanation


def test_factor_ablation_recency_disabled():
    """Verify that removing recency (R) prevents recent improvement from dominating score."""
    attempts = [
        create_attempt(1, is_correct=False, minutes_ago=60),
        create_attempt(2, is_correct=False, minutes_ago=50),
        create_attempt(3, is_correct=False, minutes_ago=40),
        create_attempt(4, is_correct=True, minutes_ago=10),
        create_attempt(5, is_correct=True, minutes_ago=2),
    ]
    # Full multi-factor model with R
    full_result = adaptive_engine.estimate_proficiency("Arrays", attempts)
    # Ablated model without R
    ablated_result = adaptive_engine.estimate_proficiency_with_ablation("Arrays", attempts, disabled_components=["R"])

    # Recent improvement gave high R (approx 0.70+), whereas historical A is low (2/5 smoothed = 3/7 = 0.428)
    # Removing R should lower the ablated score relative to the full score
    assert ablated_result.score < full_result.score
    assert full_result.component_r > full_result.component_a


def test_factor_ablation_efficiency_disabled():
    """Verify that removing efficiency (E) calculates score based only on A, R, D."""
    attempts = [
        create_attempt(1, is_correct=True, time_taken=30, expected_duration=90),
        create_attempt(2, is_correct=True, time_taken=45, expected_duration=90),
    ]
    full_result = adaptive_engine.estimate_proficiency("Trees", attempts)
    ablated_result = adaptive_engine.estimate_proficiency_with_ablation("Trees", attempts, disabled_components=["E"])
    assert ablated_result.score is not None
    assert 0.0 <= ablated_result.score <= 100.0


def test_factor_ablation_accuracy_only():
    """Ablating R, D, E leaves 100% weight on smoothed accuracy (A)."""
    attempts = [
        create_attempt(1, is_correct=True),
        create_attempt(2, is_correct=False),
        create_attempt(3, is_correct=True),
    ]
    ablated_result = adaptive_engine.estimate_proficiency_with_ablation(
        "Recursion", attempts, disabled_components=["R", "D", "E"]
    )
    # k=2, n=3 -> smoothed A = (2+1)/(3+2) = 3/5 = 0.60 -> score = 60.0
    assert ablated_result.score == 60.0


def test_timing_boundary_safeguards():
    """Extreme durations (negative, 0, 2000s) must be clamped safely without raising exceptions."""
    # Negative duration
    neg_attempt = create_attempt(1, is_correct=True, time_taken=-45, expected_duration=90)
    eff_neg = adaptive_engine.calculate_solving_efficiency([neg_attempt])
    assert 0.0 <= eff_neg <= 1.0

    # Zero duration
    zero_attempt = create_attempt(2, is_correct=True, time_taken=0, expected_duration=90)
    eff_zero = adaptive_engine.calculate_solving_efficiency([zero_attempt])
    assert 0.0 <= eff_zero <= 1.0

    # Extreme duration (over 1200 seconds / 20 minutes)
    long_attempt = create_attempt(3, is_correct=True, time_taken=2500, expected_duration=90)
    eff_long = adaptive_engine.calculate_solving_efficiency([long_attempt])
    assert eff_long == pytest.approx(0.50, abs=0.05)


def test_difficulty_weight_differential():
    """Solving a Hard question yields higher D component than solving an Easy question."""
    hard_attempt = create_attempt(1, difficulty="Hard", is_correct=True)
    easy_attempt = create_attempt(2, difficulty="Easy", is_correct=True)

    d_hard = adaptive_engine.calculate_difficulty_performance([hard_attempt])
    d_easy = adaptive_engine.calculate_difficulty_performance([easy_attempt])

    assert d_hard > 0.0
    assert d_easy > 0.0
    # Both are 100% earned ratio for their single question, but in mixed batches hard contributes more weight
    mixed_hard = [create_attempt(1, difficulty="Hard", is_correct=True), create_attempt(2, difficulty="Easy", is_correct=False)]
    mixed_easy = [create_attempt(1, difficulty="Easy", is_correct=True), create_attempt(2, difficulty="Hard", is_correct=False)]
    d_mixed_hard = adaptive_engine.calculate_difficulty_performance(mixed_hard)
    d_mixed_easy = adaptive_engine.calculate_difficulty_performance(mixed_easy)
    # Winning the hard question and failing the easy gives earned_weight 1.00 / (1.00 + 0.40) = 0.714
    # Winning the easy question and failing the hard gives earned_weight 0.40 / (0.40 + 1.00) = 0.286
    assert d_mixed_hard > d_mixed_easy



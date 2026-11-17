from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.proficiency import TopicProficiency
from backend.app.schemas import RecommendationOut, RecommendationLogOut
from backend.app.services.performance_service import performance_service
from backend.app.services.adaptive_engine import adaptive_engine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/next", response_model=RecommendationOut)
def get_recommendation(
    topic: Optional[str] = Query(None, description="Optional target topic"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the next recommended question along with multi-factor proficiency breakdown,
    confidence level, and transparent explainability rationale.
    """
    question_view, reason = performance_service.get_next_practice_question(
        db, user=current_user, target_topic=topic
    )
    if not question_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eligible practice questions found."
        )

    prof = (
        db.query(TopicProficiency)
        .filter(TopicProficiency.user_id == current_user.id, TopicProficiency.topic == question_view.topic)
        .first()
    )

    score = prof.estimated_proficiency if prof else 50.0
    conf = prof.confidence_level if prof else "low"
    obs = prof.observation_count if prof else 0
    components = {
        "A": prof.historical_accuracy if prof else 0.5,
        "R": prof.recent_performance if prof else 0.5,
        "D": prof.difficulty_score if prof else 0.5,
        "E": prof.efficiency_score if prof else 0.5,
    }

    return RecommendationOut(
        question=question_view,
        estimated_proficiency=score,
        target_difficulty=question_view.difficulty,
        confidence_level=conf,
        observation_count=obs,
        reason=reason,
        topic=question_view.topic,
        algorithm_version=settings.ALGORITHM_VERSION,
        component_breakdown=components,
    )


@router.get("/history", response_model=List[RecommendationLogOut])
def get_recommendation_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns chronological audit log of recommendations generated for the student."""
    logs = performance_service.get_recommendation_history(db, current_user, limit=limit)
    return [RecommendationLogOut.model_validate(log) for log in logs]


@router.get("/explanation")
def get_recommendation_explanation(
    topic: str = Query(..., description="Target placement topic"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns detailed algorithmic diagnostic explanation for a specific topic."""
    attempts = performance_service.get_topic_attempts(db, current_user.id, topic)
    result = adaptive_engine.estimate_proficiency(topic, attempts)
    return {
        "topic": topic,
        "score": result.score,
        "recommended_difficulty": result.recommended_difficulty,
        "confidence_level": result.confidence_level,
        "observation_count": result.observation_count,
        "formula": "S = 100 * (0.45A + 0.25R + 0.20D + 0.10E)",
        "components": {
            "historical_accuracy_A": result.component_a,
            "recent_performance_R": result.component_r,
            "difficulty_performance_D": result.component_d,
            "solving_efficiency_E": result.component_e,
        },
        "weights": {
            "A_weight": settings.WEIGHT_ACCURACY,
            "R_weight": settings.WEIGHT_RECENCY,
            "D_weight": settings.WEIGHT_DIFFICULTY,
            "E_weight": settings.WEIGHT_EFFICIENCY,
        },
        "explanation": result.explanation,
    }

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.attempt import Attempt
from backend.app.models.question import Question
from backend.app.schemas import (
    OverallProgressOut,
    TopicProficiencyOut,
    AttemptHistoryItem,
)
from backend.app.services.performance_service import performance_service

router = APIRouter(prefix="/progress", tags=["Progress & Analytics"])


@router.get("/overview", response_model=OverallProgressOut)
def get_progress_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns complete progress metrics, accuracy trend, difficulty breakdown,
    and topic proficiency estimates for the authenticated student.
    """
    return performance_service.get_student_progress(db, current_user)


@router.get("/topics", response_model=List[TopicProficiencyOut])
def get_topic_proficiencies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns topic-wise proficiency scores and confidence levels."""
    progress = performance_service.get_student_progress(db, current_user)
    return progress.topic_proficiencies


@router.get("/history", response_model=List[AttemptHistoryItem])
def get_attempt_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns chronological attempt history for the authenticated student."""
    attempts = (
        db.query(Attempt, Question.title, Question.topic)
        .join(Question, Attempt.question_id == Question.id)
        .filter(Attempt.user_id == current_user.id)
        .order_by(Attempt.attempt_timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        AttemptHistoryItem(
            id=a.id,
            question_id=a.question_id,
            question_title=title,
            topic=topic,
            difficulty=a.difficulty_at_attempt,
            submitted_answer=a.submitted_answer,
            is_correct=a.is_correct,
            time_taken_seconds=a.time_taken_seconds,
            attempt_timestamp=a.attempt_timestamp,
        )
        for a, title, topic in attempts
    ]


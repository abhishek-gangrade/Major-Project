from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_admin
from backend.app.models.user import User
from backend.app.models.question import Question
from backend.app.models.attempt import Attempt
from backend.app.models.proficiency import TopicProficiency
from backend.app.schemas import (
    QuestionCreate,
    QuestionUpdate,
    QuestionAdminView,
    UserOut,
)
from backend.app.services.question_service import question_service

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/stats")
def get_system_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Returns platform-wide summary metrics for administrator view."""
    total_users = db.query(User).count()
    student_count = db.query(User).filter(User.role == "student").count()
    total_questions = db.query(Question).count()
    active_questions = db.query(Question).filter(Question.is_active == True, Question.status == "published").count()
    total_attempts = db.query(Attempt).count()
    correct_attempts = db.query(Attempt).filter(Attempt.is_correct == True).count()
    platform_accuracy = (
        round((correct_attempts / total_attempts) * 100, 1) if total_attempts > 0 else 0.0
    )

    topic_counts = (
        db.query(Question.topic, func.count(Question.id))
        .group_by(Question.topic)
        .all()
    )

    status_counts = (
        db.query(Question.status, func.count(Question.id))
        .group_by(Question.status)
        .all()
    )

    return {
        "total_users": total_users,
        "student_count": student_count,
        "total_questions": total_questions,
        "active_questions": active_questions,
        "total_attempts": total_attempts,
        "platform_accuracy": platform_accuracy,
        "topic_distribution": {t: c for t, c in topic_counts},
        "status_distribution": {s or "published": c for s, c in status_counts},
    }


@router.get("/users", response_model=List[UserOut])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Lists registered users on the platform."""
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("/questions", response_model=QuestionAdminView, status_code=status.HTTP_201_CREATED)
def create_question(
    q_in: QuestionCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Creates a new question in the question bank."""
    if q_in.correct_answer not in q_in.options:
        raise HTTPException(
            status_code=400,
            detail="The correct_answer must match one of the available options."
        )

    q = question_service.create_question(db, q_in)
    return question_service.to_admin_view(q)


@router.put("/questions/{question_id}", response_model=QuestionAdminView)
def update_question(
    question_id: int,
    q_in: QuestionUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Updates an existing question, incrementing version if problem statement or solution changes."""
    question = question_service.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    if q_in.correct_answer and q_in.options and q_in.correct_answer not in q_in.options:
        raise HTTPException(
            status_code=400,
            detail="The correct_answer must match one of the options."
        )

    updated = question_service.update_question(db, question, q_in)
    return question_service.to_admin_view(updated)


@router.patch("/questions/{question_id}/status", response_model=QuestionAdminView)
def update_question_status(
    question_id: int,
    new_status: str = Query(..., pattern="^(draft|in_review|published|archived)$"),
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Transitions question lifecycle status (draft -> in_review -> published -> archived)."""
    question = question_service.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.status = new_status
    if new_status == "archived":
        question.is_active = False
    elif new_status == "published":
        question.is_active = True
    db.commit()
    db.refresh(question)
    return question_service.to_admin_view(question)


@router.patch("/questions/{question_id}/toggle-active", response_model=QuestionAdminView)
def toggle_question_active(
    question_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggles active/inactive status of a question."""
    q = question_service.get_question_by_id(db, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    q.is_active = not q.is_active
    db.commit()
    db.refresh(q)
    return question_service.to_admin_view(q)

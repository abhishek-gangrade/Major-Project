from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, oauth2_scheme
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.models.question import Question
from backend.app.services.question_service import question_service
from backend.app.schemas import QuestionStudentView, QuestionAdminView

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/topics/all", response_model=List[str])
def get_all_topics(db: Session = Depends(get_db)):
    """Returns all active placement topics."""
    return question_service.get_topics(db)


@router.get("", response_model=List[Union[QuestionStudentView, QuestionAdminView]])
def list_questions(
    topic: Optional[str] = Query(None, description="Filter by topic"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Lists questions in the question bank.
    Correct answers and explanations are omitted unless authenticated user is an administrator.
    """
    is_admin = False
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("role") == "admin":
            is_admin = True

    if is_admin:
        questions = question_service.get_questions(
            db, topic=topic, difficulty=difficulty, skip=skip, limit=limit
        )
        return [question_service.to_admin_view(q) for q in questions]
    
    questions = question_service.get_questions(
        db, topic=topic, difficulty=difficulty, status_filter="published", is_active=True, skip=skip, limit=limit
    )
    return [question_service.to_student_view(q) for q in questions]


@router.get("/{question_id}", response_model=Union[QuestionStudentView, QuestionAdminView])
def get_question(
    question_id: int,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    question = question_service.get_question_by_id(db, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_admin = False
    if token:
        payload = decode_access_token(token)
        if payload and payload.get("role") == "admin":
            is_admin = True

    if is_admin:
        return question_service.to_admin_view(question)
    return question_service.to_student_view(question)


from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.attempt import PracticeSession
from backend.app.schemas import (
    AttemptSubmit,
    AttemptFeedback,
    QuestionStudentView,
)
from backend.app.services.performance_service import performance_service

router = APIRouter(prefix="/practice", tags=["Practice"])


@router.get("/next")
def get_next_question(
    topic: Optional[str] = Query(None, description="Optional target topic"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves the next adaptive practice question for the authenticated student.
    Selects question difficulty matching the student's current proficiency in the target topic.
    """
    question_view, reason = performance_service.get_next_practice_question(
        db, user=current_user, target_topic=topic
    )
    if not question_view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for the selected topic/difficulty."
        )

    return {
        "question": question_view,
        "recommendation_reason": reason,
        "topic": question_view.topic,
        "difficulty": question_view.difficulty,
    }


@router.post("/attempt", response_model=AttemptFeedback)
def submit_attempt(
    submission: AttemptSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates student answer on server, stores attempt, updates topic proficiency,
    and returns comprehensive feedback including explanation and next recommendation.
    """
    try:
        feedback = performance_service.record_attempt(
            db, user=current_user, submission=submission
        )
        return feedback
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@router.post("/session/start")
def start_session(
    practice_mode: str = Query("adaptive", pattern="^(adaptive|topic)$"),
    topic: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = PracticeSession(
        user_id=current_user.id,
        practice_mode=practice_mode,
        topic=topic,
        started_at=datetime.now(timezone.utc),
        is_completed=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.id, "started_at": session.started_at}


@router.post("/session/{session_id}/complete")
def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = (
        db.query(PracticeSession)
        .filter(PracticeSession.id == session_id, PracticeSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    session.is_completed = True
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Session completed successfully", "session_id": session.id}

from typing import List, Optional
import random
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.dependencies import get_current_user, get_current_admin
from backend.app.models.user import User
from backend.app.models.research import ResearchStudy, ResearchParticipant, AssessmentResult
from backend.app.schemas import (
    ResearchStudyOut,
    StudySummaryOut,
)
from backend.app.services.research_service import research_service

router = APIRouter(prefix="/research", tags=["Research & Evaluation"])


@router.get("/studies", response_model=List[ResearchStudyOut])
def get_studies(db: Session = Depends(get_db)):
    """Returns list of active placement research studies."""
    studies = db.query(ResearchStudy).all()
    results = []
    for s in studies:
        p_count = db.query(ResearchParticipant).filter(ResearchParticipant.study_id == s.id).count()
        results.append(
            ResearchStudyOut(
                id=s.id,
                title=s.title,
                description=s.description,
                protocol_version=s.protocol_version,
                status=s.status,
                target_sample_size=s.target_sample_size,
                participants_count=p_count,
                created_at=s.created_at,
            )
        )
    return results


@router.get("/studies/{study_id}/summary", response_model=StudySummaryOut)
def get_study_summary(study_id: int, db: Session = Depends(get_db)):
    """
    Returns comparative evaluation summary for the study:
    Multi-Factor Adaptive vs Accuracy-Only vs Random Question Selection.
    """
    try:
        return research_service.get_study_summary(db, study_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/studies/{study_id}/export")
def export_research_data(
    study_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports pseudonymized, de-identified evaluation records in CSV format.
    Ensures student privacy: excludes names, emails, credentials, and IP addresses.
    Requires authenticated user.
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Research study not found")

    csv_data = research_service.export_pseudonymized_csv(db, study_id)
    filename = f"adaptiveprep_study_{study_id}_pseudonymized_export.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/studies/{study_id}/simulate-participant")
def simulate_participant(
    study_id: int,
    strategy: str = Query(..., pattern="^(adaptive|accuracy_only|random)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulates enrollment and trial completion of a participant under the selected condition.
    Enables interactive research evaluation and live statistical metric updates.
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")

    count = db.query(ResearchParticipant).filter(ResearchParticipant.study_id == study_id).count()
    p_code = f"PART-{2000 + count + 1}-{strategy[:4].upper()}"

    p = ResearchParticipant(
        study_id=study.id,
        participant_code=p_code,
        assigned_strategy=strategy,
        enrollment_metadata={"source": "interactive_simulation"},
        consent_given=True,
        status="completed",
        enrolled_at=datetime.now(timezone.utc),
    )
    db.add(p)
    db.commit()
    db.refresh(p)

    base_pre = random.randint(48, 65)
    if strategy == "adaptive":
        gain = random.randint(19, 29)
    elif strategy == "accuracy_only":
        gain = random.randint(11, 19)
    else:
        gain = random.randint(3, 11)

    post_score = min(100, base_pre + gain)

    pre = AssessmentResult(
        study_id=study.id,
        participant_id=p.id,
        assessment_type="pre_test",
        score=float(base_pre),
        max_score=100.0,
        percentage=float(base_pre),
        time_taken_seconds=random.randint(600, 850),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    post = AssessmentResult(
        study_id=study.id,
        participant_id=p.id,
        assessment_type="post_test",
        score=float(post_score),
        max_score=100.0,
        percentage=float(post_score),
        time_taken_seconds=random.randint(520, 780),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(pre)
    db.add(post)
    db.commit()

    return {
        "message": f"Simulated participant {p_code} enrolled and evaluated under {strategy} strategy",
        "pre_test_score": base_pre,
        "post_test_score": post_score,
        "score_gain": post_score - base_pre,
    }

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class ResearchStudy(Base):
    __tablename__ = "research_studies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    protocol_version = Column(String(50), default="v1.0", nullable=False)
    strategy_configuration = Column(JSON, nullable=False)  # comparison strategies & weights
    status = Column(String(20), default="active", nullable=False)  # "draft", "active", "completed"
    target_sample_size = Column(Integer, default=60, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    participants = relationship("ResearchParticipant", back_populates="study", cascade="all, delete-orphan")
    assessment_results = relationship("AssessmentResult", back_populates="study", cascade="all, delete-orphan")


class ResearchParticipant(Base):
    __tablename__ = "research_participants"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("research_studies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    participant_code = Column(String(50), unique=True, index=True, nullable=False)  # Pseudonym
    assigned_strategy = Column(String(50), nullable=False)  # "adaptive", "accuracy_only", "random"
    enrollment_metadata = Column(JSON, nullable=True)
    consent_given = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # "enrolled", "active", "completed"
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    study = relationship("ResearchStudy", back_populates="participants")
    assessment_results = relationship("AssessmentResult", back_populates="participant", cascade="all, delete-orphan")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("research_studies.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id = Column(Integer, ForeignKey("research_participants.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(String(20), nullable=False)  # "pre_test", "post_test"
    score = Column(Float, nullable=False)
    max_score = Column(Float, default=100.0, nullable=False)
    percentage = Column(Float, nullable=False)
    time_taken_seconds = Column(Integer, nullable=False)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    study = relationship("ResearchStudy", back_populates="assessment_results")
    participant = relationship("ResearchParticipant", back_populates="assessment_results")


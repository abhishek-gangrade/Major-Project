from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    statement = Column(Text, nullable=False)
    topic = Column(String(50), nullable=False, index=True)
    subtopic = Column(String(100), nullable=True)
    difficulty = Column(String(20), nullable=False, index=True)  # "Easy", "Medium", "Hard"
    question_type = Column(String(20), default="mcq", nullable=False)
    options = Column(JSON, nullable=False)  # List of strings: ["Option A", "Option B", ...]
    correct_answer = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    concept_tags = Column(JSON, nullable=True, default=list)
    expected_duration_seconds = Column(Integer, default=90, nullable=False)
    status = Column(String(20), default="published", index=True, nullable=False)  # "draft", "in_review", "published", "archived"
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    attempts = relationship("Attempt", back_populates="question")
    recommendation_logs = relationship("RecommendationLog", back_populates="question")

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_version = Column(Integer, default=1, nullable=False)
    target_topic = Column(String(50), nullable=False, index=True)
    target_difficulty = Column(String(20), nullable=False)
    estimated_proficiency = Column(Float, nullable=False)
    confidence_level = Column(String(20), default="low", nullable=False)
    selection_reason = Column(Text, nullable=False)
    learner_state_snapshot = Column(JSON, nullable=True)
    algorithm_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="recommendation_logs")
    question = relationship("Question", back_populates="recommendation_logs")

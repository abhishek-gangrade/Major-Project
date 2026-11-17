from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class TopicProficiency(Base):
    __tablename__ = "topic_proficiencies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(50), nullable=False, index=True)
    estimated_proficiency = Column(Float, default=50.0, nullable=False)
    observation_count = Column(Integer, default=0, nullable=False)
    confidence_level = Column(String(20), default="low", nullable=False)  # "low", "moderate", "high"
    historical_accuracy = Column(Float, default=0.0, nullable=False)
    recent_performance = Column(Float, default=0.0, nullable=False)
    difficulty_score = Column(Float, default=0.0, nullable=False)
    efficiency_score = Column(Float, default=0.0, nullable=False)
    last_calculated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    algorithm_version = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_user_topic_proficiency"),
    )

    # Relationships
    user = relationship("User", back_populates="proficiencies")


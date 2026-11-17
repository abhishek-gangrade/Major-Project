from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.question import Question
from backend.app.schemas import QuestionCreate, QuestionUpdate, QuestionStudentView, QuestionAdminView


class QuestionService:
    @staticmethod
    def get_questions(
        db: Session,
        topic: Optional[str] = None,
        difficulty: Optional[str] = None,
        status_filter: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Question]:
        query = db.query(Question)
        if is_active is not None:
            query = query.filter(Question.is_active == is_active)
        if status_filter:
            query = query.filter(Question.status == status_filter)
        if topic:
            query = query.filter(Question.topic == topic)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        return query.order_by(Question.id.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_question_by_id(db: Session, question_id: int) -> Optional[Question]:
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def get_topics(db: Session) -> List[str]:
        topics = (
            db.query(Question.topic)
            .filter(Question.is_active == True, Question.status == "published")
            .distinct()
            .order_by(Question.topic)
            .all()
        )
        return [t[0] for t in topics]

    @staticmethod
    def to_student_view(question: Question) -> QuestionStudentView:
        return QuestionStudentView(
            id=question.id,
            title=question.title,
            statement=question.statement,
            topic=question.topic,
            subtopic=question.subtopic,
            difficulty=question.difficulty,
            question_type=question.question_type,
            options=question.options,
            concept_tags=question.concept_tags or [],
            expected_duration_seconds=question.expected_duration_seconds,
            version=question.version or 1,
        )

    @staticmethod
    def to_admin_view(question: Question) -> QuestionAdminView:
        return QuestionAdminView(
            id=question.id,
            title=question.title,
            statement=question.statement,
            topic=question.topic,
            subtopic=question.subtopic,
            difficulty=question.difficulty,
            question_type=question.question_type,
            options=question.options,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            concept_tags=question.concept_tags or [],
            expected_duration_seconds=question.expected_duration_seconds,
            status=question.status or "published",
            version=question.version or 1,
            is_active=question.is_active,
            created_at=question.created_at,
            updated_at=question.updated_at,
        )

    @staticmethod
    def create_question(db: Session, q_in: QuestionCreate) -> Question:
        question = Question(
            title=q_in.title,
            statement=q_in.statement,
            topic=q_in.topic,
            subtopic=q_in.subtopic,
            difficulty=q_in.difficulty,
            question_type=q_in.question_type,
            options=q_in.options,
            correct_answer=q_in.correct_answer,
            explanation=q_in.explanation,
            concept_tags=q_in.concept_tags or [],
            expected_duration_seconds=q_in.expected_duration_seconds,
            status=q_in.status or "published",
            version=1,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question

    @staticmethod
    def update_question(db: Session, question: Question, q_in: QuestionUpdate) -> Question:
        # If content, options, or answer change, increment question version for attempt immutability
        increment_version = False
        if q_in.statement is not None and q_in.statement != question.statement:
            increment_version = True
        if q_in.correct_answer is not None and q_in.correct_answer != question.correct_answer:
            increment_version = True
        if q_in.options is not None and q_in.options != question.options:
            increment_version = True

        for field, value in q_in.model_dump(exclude_unset=True).items():
            setattr(question, field, value)

        if increment_version:
            question.version = (question.version or 1) + 1

        question.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(question)
        return question


question_service = QuestionService()

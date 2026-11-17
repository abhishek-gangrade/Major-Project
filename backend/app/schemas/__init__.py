from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==================== User & Auth Schemas ====================

class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(..., min_length=2, max_length=100)


class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128)
    college: Optional[str] = Field("Medi-Caps University", max_length=150)
    target_role: Optional[str] = Field("Software Development Engineer (SDE)", max_length=100)
    research_consent: Optional[bool] = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=2, max_length=100)
    college: Optional[str] = Field(None, max_length=150)
    target_role: Optional[str] = Field(None, max_length=100)
    research_consent: Optional[bool] = None


class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    college: str = "Medi-Caps University"
    target_role: str = "Software Development Engineer (SDE)"
    research_consent: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ==================== Question Schemas ====================

class QuestionStudentView(BaseModel):
    id: int
    title: str
    statement: str
    topic: str
    subtopic: Optional[str] = None
    difficulty: str
    question_type: str
    options: List[str]
    concept_tags: Optional[List[str]] = None
    expected_duration_seconds: int
    version: int = 1

    model_config = ConfigDict(from_attributes=True)


class QuestionAdminView(QuestionStudentView):
    correct_answer: str
    explanation: str
    status: str = "published"
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class QuestionCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    statement: str = Field(..., min_length=10)
    topic: str = Field(..., min_length=2, max_length=50)
    subtopic: Optional[str] = Field(None, max_length=100)
    difficulty: str = Field(..., pattern="^(Easy|Medium|Hard)$")
    question_type: str = "mcq"
    options: List[str] = Field(..., min_length=2)
    correct_answer: str = Field(..., min_length=1)
    explanation: str = Field(..., min_length=10)
    concept_tags: Optional[List[str]] = None
    expected_duration_seconds: int = Field(90, ge=10, le=900)
    status: Optional[str] = Field("published", pattern="^(draft|in_review|published|archived)$")


class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    statement: Optional[str] = Field(None, min_length=10)
    topic: Optional[str] = Field(None, min_length=2, max_length=50)
    subtopic: Optional[str] = None
    difficulty: Optional[str] = Field(None, pattern="^(Easy|Medium|Hard)$")
    options: Optional[List[str]] = Field(None, min_length=2)
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    concept_tags: Optional[List[str]] = None
    expected_duration_seconds: Optional[int] = Field(None, ge=10, le=900)
    status: Optional[str] = Field(None, pattern="^(draft|in_review|published|archived)$")
    is_active: Optional[bool] = None


# ==================== Attempt Schemas ====================

class AttemptSubmit(BaseModel):
    question_id: int
    submitted_answer: str
    time_taken_seconds: int = Field(..., ge=1, le=1800)
    session_id: Optional[int] = None
    started_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None


class AttemptFeedback(BaseModel):
    attempt_id: int
    question_id: int
    submitted_answer: str
    is_correct: bool
    correct_answer: str
    explanation: str
    time_taken_seconds: int
    topic: str
    difficulty: str
    updated_proficiency: float
    proficiency_delta: float
    next_recommendation_reason: str
    next_question: Optional[QuestionStudentView] = None


class AttemptHistoryItem(BaseModel):
    id: int
    question_id: int
    question_title: str
    question_version: int = 1
    attempt_number: int = 1
    topic: str
    difficulty: str
    submitted_answer: str
    is_correct: bool
    time_taken_seconds: int
    attempt_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Proficiency & Recommendation Schemas ====================

class TopicProficiencyOut(BaseModel):
    topic: str
    estimated_proficiency: float
    observation_count: int
    confidence_level: str
    historical_accuracy: float
    recent_performance: float
    difficulty_score: float
    efficiency_score: float
    recommended_difficulty: str
    last_calculated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationOut(BaseModel):
    question: QuestionStudentView
    estimated_proficiency: float
    target_difficulty: str
    confidence_level: str
    observation_count: int
    reason: str
    topic: str
    algorithm_version: str
    component_breakdown: Optional[Dict[str, float]] = None


class RecommendationLogOut(BaseModel):
    id: int
    question_id: int
    question_version: int
    target_topic: str
    target_difficulty: str
    estimated_proficiency: float
    confidence_level: str
    selection_reason: str
    learner_state_snapshot: Optional[Dict[str, Any]] = None
    algorithm_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Progress & Analytics Schemas ====================

class AccuracyTrendPoint(BaseModel):
    attempt_index: int
    topic: str
    is_correct: bool
    rolling_accuracy: float
    timestamp: datetime


class OverallProgressOut(BaseModel):
    total_attempts: int
    correct_attempts: int
    incorrect_attempts: int
    overall_accuracy: float
    average_time_seconds: float
    active_topics_count: int
    unique_questions_attempted: int
    topic_proficiencies: List[TopicProficiencyOut]
    recent_attempts: List[AttemptHistoryItem]
    accuracy_trend: List[AccuracyTrendPoint]
    difficulty_breakdown: dict


# ==================== Research Schemas ====================

class ResearchStudyOut(BaseModel):
    id: int
    title: str
    description: str
    protocol_version: str
    status: str
    target_sample_size: int
    participants_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrategyStat(BaseModel):
    strategy: str
    participant_count: int
    pre_test_mean: float
    post_test_mean: float
    absolute_change_mean: float
    percentage_improvement_mean: float
    completion_rate: float
    avg_solving_time_seconds: float


class StudySummaryOut(BaseModel):
    study: ResearchStudyOut
    strategies: List[StrategyStat]
    total_participants: int
    overall_completion_rate: float
    data_dictionary: dict
    assumptions_and_limitations: List[str]

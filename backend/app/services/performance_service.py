from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.question import Question
from backend.app.models.attempt import Attempt, PracticeSession
from backend.app.models.proficiency import TopicProficiency
from backend.app.models.recommendation_log import RecommendationLog
from backend.app.services.adaptive_engine import (
    adaptive_engine,
    AttemptData,
    ProficiencyResult,
)
from backend.app.schemas import (
    AttemptSubmit,
    AttemptFeedback,
    AttemptHistoryItem,
    TopicProficiencyOut,
    OverallProgressOut,
    AccuracyTrendPoint,
    QuestionStudentView,
)
from backend.app.services.question_service import question_service


class PerformanceService:
    @staticmethod
    def get_topic_attempts(db: Session, user_id: int, topic: str) -> List[AttemptData]:
        """Fetches all past attempts of a user for a specific topic, joined with Question expected durations."""
        rows = (
            db.query(Attempt, Question.expected_duration_seconds)
            .join(Question, Attempt.question_id == Question.id)
            .filter(Attempt.user_id == user_id, Question.topic == topic)
            .order_by(Attempt.attempt_timestamp.asc())
            .all()
        )

        return [
            AttemptData(
                question_id=attempt.question_id,
                topic=topic,
                difficulty=attempt.difficulty_at_attempt,
                is_correct=attempt.is_correct,
                time_taken_seconds=attempt.time_taken_seconds,
                expected_duration_seconds=expected_dur,
                attempt_timestamp=attempt.attempt_timestamp,
            )
            for attempt, expected_dur in rows
        ]

    @staticmethod
    def recalculate_topic_proficiency(
        db: Session, user_id: int, topic: str
    ) -> TopicProficiency:
        """Recalculates and persists a user's TopicProficiency using the adaptive engine."""
        attempts = PerformanceService.get_topic_attempts(db, user_id, topic)
        res: ProficiencyResult = adaptive_engine.estimate_proficiency(topic, attempts)

        prof = (
            db.query(TopicProficiency)
            .filter(TopicProficiency.user_id == user_id, TopicProficiency.topic == topic)
            .first()
        )

        if not prof:
            prof = TopicProficiency(
                user_id=user_id,
                topic=topic,
                estimated_proficiency=res.score,
                observation_count=res.observation_count,
                confidence_level=res.confidence_level,
                historical_accuracy=res.component_a,
                recent_performance=res.component_r,
                difficulty_score=res.component_d,
                efficiency_score=res.component_e,
                last_calculated_at=datetime.now(timezone.utc),
                algorithm_version=settings.ALGORITHM_VERSION,
            )
            db.add(prof)
        else:
            prof.estimated_proficiency = res.score
            prof.observation_count = res.observation_count
            prof.confidence_level = res.confidence_level
            prof.historical_accuracy = res.component_a
            prof.recent_performance = res.component_r
            prof.difficulty_score = res.component_d
            prof.efficiency_score = res.component_e
            prof.last_calculated_at = datetime.now(timezone.utc)
            prof.algorithm_version = settings.ALGORITHM_VERSION

        db.commit()
        db.refresh(prof)
        return prof

    @staticmethod
    def record_attempt(
        db: Session, user: User, submission: AttemptSubmit
    ) -> AttemptFeedback:
        """Evaluates answer correctness on server, records attempt, recalculates proficiency, and generates feedback."""
        question = db.query(Question).filter(Question.id == submission.question_id).first()
        if not question:
            raise ValueError(f"Question {submission.question_id} not found")

        # Evaluate correctness strictly on server
        submitted_clean = submission.submitted_answer.strip()
        correct_clean = question.correct_answer.strip()
        is_correct = submitted_clean.lower() == correct_clean.lower()

        # Sanitize time bounds: between 3s and 1800s
        time_taken = max(3, min(submission.time_taken_seconds, 1800))

        # Check for duplicate submission within 5 seconds to provide idempotency protection
        recent_duplicate = (
            db.query(Attempt)
            .filter(
                Attempt.user_id == user.id,
                Attempt.question_id == question.id,
                Attempt.submitted_answer == submitted_clean,
                Attempt.attempt_timestamp >= datetime.now(timezone.utc) - timedelta(seconds=5),
            )
            .first()
        )
        if recent_duplicate:
            # Return feedback from the existing attempt without duplicate counting
            prof_record = (
                db.query(TopicProficiency)
                .filter(TopicProficiency.user_id == user.id, TopicProficiency.topic == question.topic)
                .first()
            )
            next_q_view, next_reason = PerformanceService.get_next_practice_question(
                db, user, target_topic=question.topic
            )
            return AttemptFeedback(
                attempt_id=recent_duplicate.id,
                question_id=question.id,
                submitted_answer=recent_duplicate.submitted_answer,
                is_correct=recent_duplicate.is_correct,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
                time_taken_seconds=recent_duplicate.time_taken_seconds,
                topic=question.topic,
                difficulty=question.difficulty,
                updated_proficiency=prof_record.estimated_proficiency if prof_record else 50.0,
                proficiency_delta=0.0,
                next_recommendation_reason=next_reason,
                next_question=next_q_view,
            )

        # Get old proficiency before attempt
        old_prof_record = (
            db.query(TopicProficiency)
            .filter(TopicProficiency.user_id == user.id, TopicProficiency.topic == question.topic)
            .first()
        )
        old_score = old_prof_record.estimated_proficiency if old_prof_record else 50.0

        # Calculate attempt number for this question by the user
        prior_attempts_count = (
            db.query(Attempt)
            .filter(Attempt.user_id == user.id, Attempt.question_id == question.id)
            .count()
        )
        attempt_number = prior_attempts_count + 1

        # Save Attempt with version, attempt number, and timestamps
        attempt = Attempt(
            user_id=user.id,
            question_id=question.id,
            question_version=question.version or 1,
            session_id=submission.session_id,
            attempt_number=attempt_number,
            submitted_answer=submitted_clean,
            is_correct=is_correct,
            time_taken_seconds=time_taken,
            difficulty_at_attempt=question.difficulty,
            algorithm_version=settings.ALGORITHM_VERSION,
            started_at=submission.started_at,
            attempt_timestamp=datetime.now(timezone.utc),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)

        # Recalculate proficiency
        updated_prof = PerformanceService.recalculate_topic_proficiency(
            db, user.id, question.topic
        )
        score_delta = round(updated_prof.estimated_proficiency - old_score, 1)

        # Get next recommended question and log recommendation
        next_q_view, next_reason = PerformanceService.get_next_practice_question(
            db, user, target_topic=question.topic
        )

        return AttemptFeedback(
            attempt_id=attempt.id,
            question_id=question.id,
            submitted_answer=submitted_clean,
            is_correct=is_correct,
            correct_answer=question.correct_answer,
            explanation=question.explanation,
            time_taken_seconds=time_taken,
            topic=question.topic,
            difficulty=question.difficulty,
            updated_proficiency=updated_prof.estimated_proficiency,
            proficiency_delta=score_delta,
            next_recommendation_reason=next_reason,
            next_question=next_q_view,
        )

    @staticmethod
    def get_next_practice_question(
        db: Session, user: User, target_topic: Optional[str] = None
    ) -> Tuple[Optional[QuestionStudentView], str]:
        """
        Determines the student's next practice question:
        - If target_topic is None, selects the topic with the lowest proficiency or least practiced.
        - Obtains recommended difficulty for that topic based on proficiency score.
        - Excludes questions previously attempted by the user.
        - Saves an audit record in `recommendation_logs`.
        """
        all_topics = question_service.get_topics(db)
        if not all_topics:
            return None, "No active topics available."

        if not target_topic or target_topic not in all_topics:
            # Pick topic with lowest proficiency or 0 attempts to balance remediation
            prof_dict = {
                p.topic: p.estimated_proficiency
                for p in db.query(TopicProficiency).filter(TopicProficiency.user_id == user.id).all()
            }
            # Topics with no records get default 45.0 priority
            target_topic = min(all_topics, key=lambda t: prof_dict.get(t, 45.0))

        # Get proficiency and recommended difficulty for target topic
        attempts = PerformanceService.get_topic_attempts(db, user.id, target_topic)
        res = adaptive_engine.estimate_proficiency(target_topic, attempts)
        score = res.score
        conf = res.confidence_level

        # Map to difficulty
        if score < settings.THRESHOLD_EASY_UPPER:
            target_difficulty = "Easy"
        elif score < settings.THRESHOLD_MEDIUM_UPPER:
            target_difficulty = "Medium"
        else:
            target_difficulty = "Hard"

        # Fetch questions in bank: only published questions
        raw_questions = (
            db.query(Question)
            .filter(
                Question.topic == target_topic,
                Question.is_active == True,
                Question.status == "published",
            )
            .all()
        )
        dict_questions = [
            {
                "id": q.id,
                "title": q.title,
                "statement": q.statement,
                "topic": q.topic,
                "subtopic": q.subtopic,
                "difficulty": q.difficulty,
                "question_type": q.question_type,
                "options": q.options,
                "concept_tags": q.concept_tags or [],
                "expected_duration_seconds": q.expected_duration_seconds,
                "version": q.version or 1,
                "is_active": q.is_active,
            }
            for q in raw_questions
        ]

        attempted_ids = [
            a[0]
            for a in db.query(Attempt.question_id)
            .filter(Attempt.user_id == user.id)
            .all()
        ]

        candidate, selection_reason = adaptive_engine.select_next_candidate(
            target_topic=target_topic,
            target_difficulty=target_difficulty,
            available_questions=dict_questions,
            attempted_question_ids=attempted_ids,
        )

        if not candidate:
            return None, selection_reason

        # Persist recommendation log with learner-state snapshot
        rec_log = RecommendationLog(
            user_id=user.id,
            question_id=candidate["id"],
            question_version=candidate.get("version", 1),
            target_topic=target_topic,
            target_difficulty=candidate.get("difficulty", target_difficulty),
            estimated_proficiency=score,
            confidence_level=conf,
            selection_reason=selection_reason,
            learner_state_snapshot={
                "component_a": res.component_a,
                "component_r": res.component_r,
                "component_d": res.component_d,
                "component_e": res.component_e,
                "observation_count": res.observation_count,
            },
            algorithm_version=settings.ALGORITHM_VERSION,
            created_at=datetime.now(timezone.utc),
        )
        db.add(rec_log)
        db.commit()

        return QuestionStudentView(**candidate), selection_reason

    @staticmethod
    def get_recommendation_history(
        db: Session, user: User, limit: int = 20
    ) -> List[RecommendationLog]:
        """Returns chronological list of recommendation logs with learner-state snapshots."""
        return (
            db.query(RecommendationLog)
            .filter(RecommendationLog.user_id == user.id)
            .order_by(RecommendationLog.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_student_progress(db: Session, user: User) -> OverallProgressOut:
        """Aggregates comprehensive dashboard metrics for the student."""
        attempts = (
            db.query(Attempt, Question.title, Question.topic)
            .join(Question, Attempt.question_id == Question.id)
            .filter(Attempt.user_id == user.id)
            .order_by(Attempt.attempt_timestamp.asc())
            .all()
        )

        total_attempts = len(attempts)
        correct_attempts = sum(1 for a, _, _ in attempts if a.is_correct)
        incorrect_attempts = total_attempts - correct_attempts
        overall_accuracy = (
            round((correct_attempts / total_attempts) * 100, 1)
            if total_attempts > 0
            else 0.0
        )
        avg_time = (
            round(sum(a.time_taken_seconds for a, _, _ in attempts) / total_attempts, 1)
            if total_attempts > 0
            else 0.0
        )

        unique_questions = len(set(a.question_id for a, _, _ in attempts))

        # Difficulty breakdown
        diff_counts = {
            "Easy": {"total": 0, "correct": 0},
            "Medium": {"total": 0, "correct": 0},
            "Hard": {"total": 0, "correct": 0},
        }
        for a, _, _ in attempts:
            diff = a.difficulty_at_attempt
            if diff in diff_counts:
                diff_counts[diff]["total"] += 1
                if a.is_correct:
                    diff_counts[diff]["correct"] += 1

        # Accuracy trend points (rolling accuracy)
        trend_points = []
        running_correct = 0
        for idx, (a, _, topic) in enumerate(attempts, start=1):
            if a.is_correct:
                running_correct += 1
            trend_points.append(
                AccuracyTrendPoint(
                    attempt_index=idx,
                    topic=topic,
                    is_correct=a.is_correct,
                    rolling_accuracy=round((running_correct / idx) * 100, 1),
                    timestamp=a.attempt_timestamp,
                )
            )

        # Recent attempts (last 10 in reverse order)
        recent_items = [
            AttemptHistoryItem(
                id=a.id,
                question_id=a.question_id,
                question_title=title,
                question_version=a.question_version or 1,
                attempt_number=a.attempt_number or 1,
                topic=topic,
                difficulty=a.difficulty_at_attempt,
                submitted_answer=a.submitted_answer,
                is_correct=a.is_correct,
                time_taken_seconds=a.time_taken_seconds,
                attempt_timestamp=a.attempt_timestamp,
            )
            for a, title, topic in reversed(attempts[-10:])
        ]

        # Topic proficiencies
        all_topics = question_service.get_topics(db)
        prof_records = {
            p.topic: p
            for p in db.query(TopicProficiency).filter(TopicProficiency.user_id == user.id).all()
        }

        topic_outs = []
        for topic in all_topics:
            p = prof_records.get(topic)
            if p:
                diff = (
                    "Easy"
                    if p.estimated_proficiency < settings.THRESHOLD_EASY_UPPER
                    else ("Medium" if p.estimated_proficiency < settings.THRESHOLD_MEDIUM_UPPER else "Hard")
                )
                topic_outs.append(
                    TopicProficiencyOut(
                        topic=topic,
                        estimated_proficiency=p.estimated_proficiency,
                        observation_count=p.observation_count,
                        confidence_level=p.confidence_level,
                        historical_accuracy=p.historical_accuracy,
                        recent_performance=p.recent_performance,
                        difficulty_score=p.difficulty_score,
                        efficiency_score=p.efficiency_score,
                        recommended_difficulty=diff,
                        last_calculated_at=p.last_calculated_at,
                    )
                )
            else:
                topic_outs.append(
                    TopicProficiencyOut(
                        topic=topic,
                        estimated_proficiency=50.0,
                        observation_count=0,
                        confidence_level="low",
                        historical_accuracy=0.5,
                        recent_performance=0.5,
                        difficulty_score=0.5,
                        efficiency_score=0.5,
                        recommended_difficulty="Medium",
                        last_calculated_at=None,
                    )
                )

        active_topics = sum(1 for t in topic_outs if t.observation_count > 0)

        return OverallProgressOut(
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            incorrect_attempts=incorrect_attempts,
            overall_accuracy=overall_accuracy,
            average_time_seconds=avg_time,
            active_topics_count=active_topics,
            unique_questions_attempted=unique_questions,
            topic_proficiencies=topic_outs,
            recent_attempts=recent_items,
            accuracy_trend=trend_points,
            difficulty_breakdown=diff_counts,
        )


performance_service = PerformanceService()

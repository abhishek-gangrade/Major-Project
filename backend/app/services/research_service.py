import io
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.research import ResearchStudy, ResearchParticipant, AssessmentResult
from backend.app.schemas import (
    ResearchStudyOut,
    StudySummaryOut,
    StrategyStat,
)


class ResearchService:
    @staticmethod
    def get_or_create_default_study(db: Session) -> ResearchStudy:
        """Ensures the primary placement evaluation study exists."""
        study = db.query(ResearchStudy).first()
        if not study:
            study = ResearchStudy(
                title="Evaluation of Multi-Factor Adaptive Recommendation vs Random and Accuracy-Only Baselines",
                description=(
                    "An experimental research study at Medi-Caps University evaluating the pedagogical "
                    "efficiency, score gain, and question targeting of the proposed multi-factor adaptive "
                    "recommendation engine against accuracy-only and random question selection strategies."
                ),
                protocol_version="MEDICAPS-AP-2026.1",
                strategy_configuration={
                    "strategies": ["adaptive", "accuracy_only", "random"],
                    "allocation_ratio": "1:1:1",
                    "pre_test_question_count": 10,
                    "post_test_question_count": 10,
                    "target_practice_sessions": 3,
                },
                status="active",
                target_sample_size=60,
                created_at=datetime.now(timezone.utc),
            )
            db.add(study)
            db.commit()
            db.refresh(study)
        return study

    @staticmethod
    def get_study_summary(db: Session, study_id: int) -> StudySummaryOut:
        """Calculates outcome comparison metrics across assigned strategies."""
        study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
        if not study:
            raise ValueError(f"Study {study_id} not found")

        participants = (
            db.query(ResearchParticipant)
            .filter(ResearchParticipant.study_id == study_id)
            .all()
        )

        total_participants = len(participants)
        completed_count = sum(1 for p in participants if p.status == "completed")
        overall_completion_rate = (
            round((completed_count / total_participants) * 100, 1)
            if total_participants > 0
            else 0.0
        )

        # Query assessments
        assessments = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.study_id == study_id)
            .all()
        )

        # Group assessments by participant
        participant_tests: Dict[int, Dict[str, AssessmentResult]] = {}
        for a in assessments:
            if a.participant_id not in participant_tests:
                participant_tests[a.participant_id] = {}
            participant_tests[a.participant_id][a.assessment_type] = a

        strategy_records: Dict[str, List[Dict[str, float]]] = {
            "adaptive": [],
            "accuracy_only": [],
            "random": [],
        }

        for p in participants:
            strat = p.assigned_strategy
            if strat not in strategy_records:
                strategy_records[strat] = []

            p_assessments = participant_tests.get(p.id, {})
            pre = p_assessments.get("pre_test")
            post = p_assessments.get("post_test")

            if pre and post:
                pre_pct = pre.percentage
                post_pct = post.percentage
                abs_change = post_pct - pre_pct
                pct_improvement = (
                    ((post_pct - pre_pct) / pre_pct) * 100 if pre_pct > 0 else 0.0
                )
                avg_time = (pre.time_taken_seconds + post.time_taken_seconds) / 2.0

                strategy_records[strat].append({
                    "pre": pre_pct,
                    "post": post_pct,
                    "delta": abs_change,
                    "pct_imp": pct_improvement,
                    "time": avg_time,
                })

        strategy_stats: List[StrategyStat] = []
        for strat, records in strategy_records.items():
            strat_participants = [p for p in participants if p.assigned_strategy == strat]
            p_count = len(strat_participants)
            completed_strat = sum(1 for p in strat_participants if p.status == "completed")
            completion_rate = (
                round((completed_strat / p_count) * 100, 1) if p_count > 0 else 0.0
            )

            if records:
                pre_mean = round(float(np.mean([r["pre"] for r in records])), 1)
                post_mean = round(float(np.mean([r["post"] for r in records])), 1)
                delta_mean = round(float(np.mean([r["delta"] for r in records])), 1)
                imp_mean = round(float(np.mean([r["pct_imp"] for r in records])), 1)
                time_mean = round(float(np.mean([r["time"] for r in records])), 1)
            else:
                pre_mean = 0.0
                post_mean = 0.0
                delta_mean = 0.0
                imp_mean = 0.0
                time_mean = 0.0

            strategy_stats.append(
                StrategyStat(
                    strategy=strat,
                    participant_count=p_count,
                    pre_test_mean=pre_mean,
                    post_test_mean=post_mean,
                    absolute_change_mean=delta_mean,
                    percentage_improvement_mean=imp_mean,
                    completion_rate=completion_rate,
                    avg_solving_time_seconds=time_mean,
                )
            )

        data_dict = {
            "participant_code": "Unique pseudonymous identifier assigned to participant (e.g., P-XXXX-ADAPT)",
            "assigned_strategy": "Experimental condition: 'adaptive' (multi-factor), 'accuracy_only', or 'random'",
            "pre_test_percentage": "Pre-intervention diagnostic placement score (0-100%)",
            "post_test_percentage": "Post-intervention placement assessment score (0-100%)",
            "score_gain": "Absolute difference: Post-Test % - Pre-Test %",
            "completion_status": "Study protocol completion state ('completed', 'active', 'enrolled')",
        }

        limitations = [
            "Sample records in the demo environment are simulated for evaluation pipeline testing.",
            "Generalizability to all computer science placement exams requires multi-institutional replication.",
            "Pre-test and post-test forms must be calibrated for equal item difficulty using Item Response Theory.",
            "Student motivation and external coaching outside the platform may act as confounding factors.",
        ]

        study_out = ResearchStudyOut(
            id=study.id,
            title=study.title,
            description=study.description,
            protocol_version=study.protocol_version,
            status=study.status,
            target_sample_size=study.target_sample_size,
            participants_count=total_participants,
            created_at=study.created_at,
        )

        return StudySummaryOut(
            study=study_out,
            strategies=strategy_stats,
            total_participants=total_participants,
            overall_completion_rate=overall_completion_rate,
            data_dictionary=data_dict,
            assumptions_and_limitations=limitations,
        )

    @staticmethod
    def export_pseudonymized_csv(db: Session, study_id: int) -> str:
        """
        Generates a de-identified, privacy-preserving CSV export.
        Excludes names, emails, passwords, and IP addresses.
        Uses pseudonymous participant codes.
        """
        participants = (
            db.query(ResearchParticipant)
            .filter(ResearchParticipant.study_id == study_id)
            .all()
        )

        assessments = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.study_id == study_id)
            .all()
        )

        participant_tests: Dict[int, Dict[str, AssessmentResult]] = {}
        for a in assessments:
            if a.participant_id not in participant_tests:
                participant_tests[a.participant_id] = {}
            participant_tests[a.participant_id][a.assessment_type] = a

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "participant_code",
            "assigned_strategy",
            "status",
            "pre_test_score",
            "pre_test_max",
            "pre_test_percentage",
            "pre_test_duration_sec",
            "post_test_score",
            "post_test_max",
            "post_test_percentage",
            "post_test_duration_sec",
            "score_gain_percentage_points",
            "enrolled_timestamp",
        ])

        for p in participants:
            p_tests = participant_tests.get(p.id, {})
            pre = p_tests.get("pre_test")
            post = p_tests.get("post_test")

            pre_score = pre.score if pre else ""
            pre_max = pre.max_score if pre else ""
            pre_pct = pre.percentage if pre else ""
            pre_dur = pre.time_taken_seconds if pre else ""

            post_score = post.score if post else ""
            post_max = post.max_score if post else ""
            post_pct = post.percentage if post else ""
            post_dur = post.time_taken_seconds if post else ""

            gain = (
                round(post.percentage - pre.percentage, 2)
                if (pre and post)
                else ""
            )

            writer.writerow([
                p.participant_code,
                p.assigned_strategy,
                p.status,
                pre_score,
                pre_max,
                pre_pct,
                pre_dur,
                post_score,
                post_max,
                post_pct,
                post_dur,
                gain,
                p.enrolled_at.isoformat() if p.enrolled_at else "",
            ])

        return output.getvalue()


research_service = ResearchService()


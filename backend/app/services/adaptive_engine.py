"""
Adaptive Recommendation Engine for AdaptivePrep.

Implements the multi-factor proficiency estimation:
S = 100 * (0.45 * A + 0.25 * R + 0.20 * D + 0.10 * E)

Where:
- S: Estimated topic proficiency (0 - 100)
- A: Normalized historical accuracy (smoothed)
- R: Normalized recent performance (recency-weighted)
- D: Normalized difficulty performance
- E: Normalized solving efficiency (safeguarded against fast errors and time anomalies)
"""

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import math

from backend.app.core.config import settings


@dataclass
class AttemptData:
    question_id: int
    topic: str
    difficulty: str  # "Easy", "Medium", "Hard"
    is_correct: bool
    time_taken_seconds: int
    expected_duration_seconds: int
    attempt_timestamp: datetime


@dataclass
class ProficiencyResult:
    topic: str
    score: float  # 0 to 100
    recommended_difficulty: str  # "Easy", "Medium", "Hard"
    confidence_level: str  # "low", "moderate", "high"
    observation_count: int
    component_a: float  # Historical accuracy (0-1)
    component_r: float  # Recent performance (0-1)
    component_d: float  # Difficulty performance (0-1)
    component_e: float  # Solving efficiency (0-1)
    explanation: str


class AdaptiveRecommendationEngine:
    def __init__(
        self,
        weight_a: float = settings.WEIGHT_ACCURACY,
        weight_r: float = settings.WEIGHT_RECENCY,
        weight_d: float = settings.WEIGHT_DIFFICULTY,
        weight_e: float = settings.WEIGHT_EFFICIENCY,
        threshold_easy: float = settings.THRESHOLD_EASY_UPPER,
        threshold_medium: float = settings.THRESHOLD_MEDIUM_UPPER,
        recency_window: int = settings.RECENCY_WINDOW_SIZE,
        algorithm_version: str = settings.ALGORITHM_VERSION,
    ):
        self.w_a = weight_a
        self.w_r = weight_r
        self.w_d = weight_d
        self.w_e = weight_e
        self.threshold_easy = threshold_easy
        self.threshold_medium = threshold_medium
        self.recency_window = recency_window
        self.algorithm_version = algorithm_version

        # Difficulty weight multiplier
        self.diff_weights = {
            "Easy": 0.40,
            "Medium": 0.70,
            "Hard": 1.00,
        }

    def calculate_historical_accuracy(self, attempts: List[AttemptData]) -> float:
        """
        Historical accuracy with Laplace smoothing (alpha=1, beta=1)
        Prior expectation is 0.5 when no attempts exist.
        Prevents a single attempt from causing 1.0 or 0.0 extreme proficiency.
        """
        if not attempts:
            return 0.50

        k = sum(1 for a in attempts if a.is_correct)
        n = len(attempts)
        # Laplace smoothed: (k + 1) / (n + 2)
        smoothed = (k + 1.0) / (n + 2.0)
        return min(max(smoothed, 0.0), 1.0)

    def calculate_recent_performance(self, attempts: List[AttemptData]) -> float:
        """
        Recency-weighted performance over the most recent `recency_window` attempts.
        Linear ramp weights: earlier in window have lower weight, most recent has highest weight.
        """
        if not attempts:
            return 0.50

        # Sort attempts by timestamp ascending, take last N
        sorted_attempts = sorted(attempts, key=lambda a: a.attempt_timestamp)
        recent = sorted_attempts[-self.recency_window :]
        m = len(recent)

        if m == 0:
            return 0.50

        # Weights: 1, 2, ..., m
        weights = [i + 1 for i in range(m)]
        total_weight = sum(weights)

        weighted_correct = sum(
            weights[i] * (1.0 if recent[i].is_correct else 0.0)
            for i in range(m)
        )
        return min(max(weighted_correct / total_weight, 0.0), 1.0)

    def calculate_difficulty_performance(self, attempts: List[AttemptData]) -> float:
        """
        Difficulty capability score:
        Evaluates performance weighted by difficulty level.
        Correct answers at Hard/Medium contribute substantially;
        incorrect answers at Easy decrease the score.
        """
        if not attempts:
            return 0.50

        total_weight = 0.0
        earned_weight = 0.0

        for a in attempts:
            w = self.diff_weights.get(a.difficulty, 0.60)
            total_weight += w
            if a.is_correct:
                earned_weight += w
            else:
                # Slight partial credit penalty retention
                earned_weight += 0.0

        if total_weight <= 0.0:
            return 0.50

        ratio = earned_weight / total_weight
        return min(max(ratio, 0.0), 1.0)

    def calculate_solving_efficiency(self, attempts: List[AttemptData]) -> float:
        """
        Solving efficiency compares actual time to expected time.
        Safeguards:
        - Fast incorrect guesses receive no efficiency reward (neutral/low: 0.20).
        - Correct answers in reasonable time (0.4x - 1.2x expected) earn high efficiency (0.80 - 1.0).
        - Slower correct answers (> 1.2x expected) earn 0.50 - 0.70.
        - Extreme times (< 3s or > 1800s) are bounded.
        """
        if not attempts:
            return 0.50

        efficiency_scores = []
        for a in attempts:
            t_actual = max(3, min(a.time_taken_seconds, 1200))
            t_expected = max(15, a.expected_duration_seconds)

            ratio = t_actual / t_expected

            if not a.is_correct:
                # Fast incorrect guesses get low score; thoughtful wrong answers get neutral
                if ratio < 0.4:
                    score = 0.10  # rushed error
                else:
                    score = 0.35  # standard error
            else:
                # Correct answer
                if ratio < 0.3:
                    # suspiciously fast correct or easy recall
                    score = 0.85
                elif 0.3 <= ratio <= 1.1:
                    # optimal solving zone
                    score = 1.00
                elif 1.1 < ratio <= 1.8:
                    # slightly slow but solid
                    score = 0.70
                else:
                    # overtime
                    score = 0.50

            efficiency_scores.append(score)

        return min(max(sum(efficiency_scores) / len(efficiency_scores), 0.0), 1.0)

    def determine_confidence(self, observation_count: int) -> str:
        if observation_count < settings.MIN_OBSERVATION_THRESHOLD:
            return "low"
        elif observation_count < 8:
            return "moderate"
        else:
            return "high"

    def estimate_proficiency(self, topic: str, attempts: List[AttemptData]) -> ProficiencyResult:
        """
        Calculates topic proficiency score S and maps to recommended difficulty.
        """
        n = len(attempts)
        conf = self.determine_confidence(n)

        A = self.calculate_historical_accuracy(attempts)
        R = self.calculate_recent_performance(attempts)
        D = self.calculate_difficulty_performance(attempts)
        E = self.calculate_solving_efficiency(attempts)

        # Multi-factor formula: S = 100 * (0.45A + 0.25R + 0.20D + 0.10E)
        raw_score = 100.0 * (
            (self.w_a * A) +
            (self.w_r * R) +
            (self.w_d * D) +
            (self.w_e * E)
        )
        score = round(min(max(raw_score, 0.0), 100.0), 1)

        # Determine difficulty level
        if score < self.threshold_easy:
            difficulty = "Easy"
        elif score < self.threshold_medium:
            difficulty = "Medium"
        else:
            difficulty = "Hard"

        # Apply transition safeguard if there is previous history:
        # Avoid stepping from Easy to Hard in 1 step if confidence is low
        if conf == "low" and difficulty == "Hard":
            difficulty = "Medium"

        explanation = self.generate_proficiency_explanation(
            topic=topic,
            score=score,
            difficulty=difficulty,
            conf=conf,
            n=n,
            A=A,
            R=R
        )

        return ProficiencyResult(
            topic=topic,
            score=score,
            recommended_difficulty=difficulty,
            confidence_level=conf,
            observation_count=n,
            component_a=round(A, 3),
            component_r=round(R, 3),
            component_d=round(D, 3),
            component_e=round(E, 3),
            explanation=explanation,
        )

    def estimate_proficiency_with_ablation(
        self,
        topic: str,
        attempts: List[AttemptData],
        disabled_components: Optional[List[str]] = None,
    ) -> ProficiencyResult:
        """
        Calculates topic proficiency under factor ablation for research evaluation.
        Allows removing 'R' (recency), 'E' (efficiency), 'D' (difficulty), or 'A' (historical accuracy),
        renormalizing remaining weights to sum to 1.0.
        """
        disabled = set(disabled_components or [])
        wa = 0.0 if "A" in disabled else self.w_a
        wr = 0.0 if "R" in disabled else self.w_r
        wd = 0.0 if "D" in disabled else self.w_d
        we = 0.0 if "E" in disabled else self.w_e
        total_w = wa + wr + wd + we
        if total_w > 0:
            wa /= total_w
            wr /= total_w
            wd /= total_w
            we /= total_w
        else:
            wa = 1.0

        n = len(attempts)
        conf = self.determine_confidence(n)
        A = self.calculate_historical_accuracy(attempts)
        R = self.calculate_recent_performance(attempts)
        D = self.calculate_difficulty_performance(attempts)
        E = self.calculate_solving_efficiency(attempts)

        raw_score = 100.0 * ((wa * A) + (wr * R) + (wd * D) + (we * E))
        score = round(min(max(raw_score, 0.0), 100.0), 1)

        if score < self.threshold_easy:
            difficulty = "Easy"
        elif score < self.threshold_medium:
            difficulty = "Medium"
        else:
            difficulty = "Hard"

        if conf == "low" and difficulty == "Hard":
            difficulty = "Medium"

        explanation = self.generate_proficiency_explanation(
            topic=topic,
            score=score,
            difficulty=difficulty,
            conf=conf,
            n=n,
            A=A,
            R=R
        )
        return ProficiencyResult(
            topic=topic,
            score=score,
            recommended_difficulty=difficulty,
            confidence_level=conf,
            observation_count=n,
            component_a=round(A, 3),
            component_r=round(R, 3),
            component_d=round(D, 3),
            component_e=round(E, 3),
            explanation=explanation,
        )

    def generate_proficiency_explanation(
        self,
        topic: str,
        score: float,
        difficulty: str,
        conf: str,
        n: int,
        A: float,
        R: float
    ) -> str:
        """
        Generates a human-readable, transparent explanation for the recommendation.
        Grounds every claim strictly in actual data.
        """
        if n == 0:
            return (
                f"Diagnostic baseline for {topic}: No prior attempts recorded. "
                f"Starting at {difficulty} to establish your initial placement profile."
            )

        if conf == "low":
            return (
                f"Preliminary estimate for {topic} ({score:.0f}/100) based on {n} initial attempt(s). "
                f"Recommending {difficulty} to calibrate confidence and establish reliable mastery."
            )

        acc_pct = int(round(A * 100))
        rec_pct = int(round(R * 100))

        if score >= self.threshold_medium:
            return (
                f"High proficiency in {topic} ({score:.0f}/100) with {acc_pct}% historical accuracy "
                f"and {rec_pct}% recent trend. Recommended {difficulty} to challenge placement-level problem solving."
            )
        elif score >= self.threshold_easy:
            if rec_pct > acc_pct:
                return (
                    f"Steady progress in {topic} ({score:.0f}/100) with recent improvement to {rec_pct}%. "
                    f"Recommended {difficulty} to consolidate intermediate concepts."
                )
            else:
                return (
                    f"Moderate proficiency in {topic} ({score:.0f}/100). "
                    f"Recommended {difficulty} to strengthen consistency before advancing."
                )
        else:
            return (
                f"Targeted remediation for {topic} ({score:.0f}/100, recent accuracy {rec_pct}%). "
                f"Recommended {difficulty} to reinforce fundamental concepts and rebuild accuracy."
            )

    def select_next_candidate(
        self,
        target_topic: str,
        target_difficulty: str,
        available_questions: List[Dict[str, Any]],
        attempted_question_ids: List[int],
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Selects the next eligible question for practice:
        1. Filters available questions by topic and target difficulty.
        2. Excludes already attempted questions where alternatives exist.
        3. If target difficulty is exhausted, gracefully falls back to adjacent difficulty.
        4. If all questions in the topic are attempted, re-surfaces the least recently attempted question.
        """
        topic_questions = [
            q for q in available_questions
            if q.get("topic") == target_topic and q.get("is_active", True)
        ]

        if not topic_questions:
            # Fallback to any active question
            if available_questions:
                fallback_q = available_questions[0]
                return fallback_q, f"Topic '{target_topic}' has no active questions. Fallback question selected."
            return None, "No active questions found in the question bank."

        # Filter by target difficulty
        diff_matches = [
            q for q in topic_questions
            if q.get("difficulty") == target_difficulty
        ]

        # Exclude attempted questions
        unattempted_matches = [
            q for q in diff_matches
            if q.get("id") not in attempted_question_ids
        ]

        if unattempted_matches:
            # Return deterministic first candidate or lowest ID
            selected = sorted(unattempted_matches, key=lambda x: x["id"])[0]
            return selected, (
                f"Selected {target_difficulty} question in {target_topic} "
                f"to match your current estimated proficiency."
            )

        # Fallback 1: Adjacent difficulty within the same topic
        diff_order = ["Easy", "Medium", "Hard"]
        target_idx = diff_order.index(target_difficulty) if target_difficulty in diff_order else 1
        
        # Try adjacent difficulties (e.g. Medium if Hard exhausted, Easy if Medium exhausted)
        adjacent_difficulties = []
        if target_idx > 0:
            adjacent_difficulties.append(diff_order[target_idx - 1])
        if target_idx < len(diff_order) - 1:
            adjacent_difficulties.append(diff_order[target_idx + 1])

        for alt_diff in adjacent_difficulties:
            alt_unattempted = [
                q for q in topic_questions
                if q.get("difficulty") == alt_diff and q.get("id") not in attempted_question_ids
            ]
            if alt_unattempted:
                selected = sorted(alt_unattempted, key=lambda x: x["id"])[0]
                return selected, (
                    f"Target difficulty '{target_difficulty}' fully covered. "
                    f"Selected adjacent '{alt_diff}' question in {target_topic} for continuous practice."
                )

        # Fallback 2: Any unattempted question in this topic
        any_unattempted = [
            q for q in topic_questions
            if q.get("id") not in attempted_question_ids
        ]
        if any_unattempted:
            selected = sorted(any_unattempted, key=lambda x: x["id"])[0]
            return selected, (
                f"Selected available unattempted question in {target_topic}."
            )

        # Fallback 3: All questions in this topic have been attempted; cycle through for revision
        cycle_selected = sorted(topic_questions, key=lambda x: x["id"])[0]
        return cycle_selected, (
            f"You have practiced all available questions in {target_topic}. "
            f"Recommending a revision question to consolidate long-term retention."
        )


# Global singleton instance of the adaptive engine
adaptive_engine = AdaptiveRecommendationEngine()


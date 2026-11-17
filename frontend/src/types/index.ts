export interface User {
  id: number;
  email: string;
  display_name: string;
  role: 'student' | 'admin';
  is_active: boolean;
  college?: string;
  target_role?: string;
  research_consent?: boolean;
  created_at: string;
}

export interface Question {
  id: number;
  title: string;
  statement: string;
  topic: string;
  subtopic?: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  question_type: string;
  options: string[];
  concept_tags?: string[];
  expected_duration_seconds: number;
  version?: number;
  // Admin-only fields (undefined in student mode)
  correct_answer?: string;
  explanation?: string;
  status?: 'draft' | 'in_review' | 'published' | 'archived';
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface AttemptFeedback {
  attempt_id: number;
  question_id: number;
  submitted_answer: string;
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  time_taken_seconds: number;
  topic: string;
  difficulty: string;
  updated_proficiency: number;
  proficiency_delta: number;
  next_recommendation_reason: string;
  next_question?: Question;
}

export interface AttemptHistoryItem {
  id: number;
  question_id: number;
  question_title: string;
  question_version?: number;
  attempt_number?: number;
  topic: string;
  difficulty: string;
  submitted_answer: string;
  is_correct: boolean;
  time_taken_seconds: number;
  attempt_timestamp: string;
}

export interface TopicProficiency {
  topic: string;
  estimated_proficiency: number;
  observation_count: number;
  confidence_level: 'low' | 'moderate' | 'high';
  historical_accuracy: number;
  recent_performance: number;
  difficulty_score: number;
  efficiency_score: number;
  recommended_difficulty: string;
  last_calculated_at: string | null;
}

export interface AccuracyTrendPoint {
  attempt_index: number;
  topic: string;
  is_correct: boolean;
  rolling_accuracy: number;
  timestamp: string;
}

export interface OverallProgress {
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  overall_accuracy: number;
  average_time_seconds: number;
  active_topics_count: number;
  unique_questions_attempted: number;
  topic_proficiencies: TopicProficiency[];
  recent_attempts: AttemptHistoryItem[];
  accuracy_trend: AccuracyTrendPoint[];
  difficulty_breakdown: {
    Easy: { total: number; correct: number };
    Medium: { total: number; correct: number };
    Hard: { total: number; correct: number };
  };
}

export interface Recommendation {
  question: Question;
  estimated_proficiency: number;
  target_difficulty: string;
  confidence_level: string;
  observation_count: number;
  reason: string;
  topic: string;
  algorithm_version: string;
  component_breakdown?: {
    A: number;
    R: number;
    D: number;
    E: number;
  };
}

export interface RecommendationLog {
  id: number;
  question_id: number;
  question_version: number;
  target_topic: string;
  target_difficulty: string;
  estimated_proficiency: number;
  confidence_level: string;
  selection_reason: string;
  learner_state_snapshot?: {
    component_a: number;
    component_r: number;
    component_d: number;
    component_e: number;
    observation_count: number;
  };
  algorithm_version: string;
  created_at: string;
}

export interface StrategyStat {
  strategy: string;
  participant_count: number;
  pre_test_mean: number;
  post_test_mean: number;
  absolute_change_mean: number;
  percentage_improvement_mean: number;
  completion_rate: number;
  avg_solving_time_seconds: number;
}

export interface ResearchStudy {
  id: number;
  title: string;
  description: string;
  protocol_version: string;
  status: string;
  target_sample_size: number;
  participants_count: number;
  created_at: string;
}

export interface StudySummary {
  study: ResearchStudy;
  strategies: StrategyStat[];
  total_participants: number;
  overall_completion_rate: number;
  data_dictionary: Record<string, string>;
  assumptions_and_limitations: string[];
}

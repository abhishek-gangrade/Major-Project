import {
  User,
  Question,
  AttemptFeedback,
  OverallProgress,
  Recommendation,
  RecommendationLog,
  ResearchStudy,
  StudySummary,
} from '../types';

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? `${window.location.protocol}//${window.location.hostname}:8000/api/v1`
    : '/api/v1');

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('adaptiveprep_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    localStorage.removeItem('adaptiveprep_token');
    localStorage.removeItem('adaptiveprep_user');
  }

  if (!response.ok) {
    let errorMsg = `Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // ignore
    }
    throw new ApiError(errorMsg, response.status);
  }

  return response.json();
}

export const api = {
  auth: {
    login: async (email: string, password: string) => {
      const res = await request<{ access_token: string; user: User }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('adaptiveprep_token', res.access_token);
      localStorage.setItem('adaptiveprep_user', JSON.stringify(res.user));
      return res;
    },
    register: async (display_name: string, email: string, password: string, college?: string, target_role?: string) => {
      const res = await request<{ access_token: string; user: User }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ display_name, email, password, college, target_role }),
      });
      localStorage.setItem('adaptiveprep_token', res.access_token);
      localStorage.setItem('adaptiveprep_user', JSON.stringify(res.user));
      return res;
    },
    getMe: () => request<User>('/auth/me'),
    updateProfile: (data: {
      display_name?: string;
      college?: string;
      target_role?: string;
      research_consent?: boolean;
    }) =>
      request<User>('/auth/profile', {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    logout: () => {
      localStorage.removeItem('adaptiveprep_token');
      localStorage.removeItem('adaptiveprep_user');
    },
  },

  practice: {
    getNextQuestion: (topic?: string) => {
      const query = topic ? `?topic=${encodeURIComponent(topic)}` : '';
      return request<{
        question: Question;
        recommendation_reason: string;
        topic: string;
        difficulty: string;
      }>(`/practice/next${query}`);
    },
    submitAttempt: (data: {
      question_id: number;
      submitted_answer: string;
      time_taken_seconds: number;
      session_id?: number;
      started_at?: string;
    }) =>
      request<AttemptFeedback>('/practice/attempt', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  progress: {
    getOverview: () => request<OverallProgress>('/progress/overview'),
  },

  recommendations: {
    getNext: (topic?: string) => {
      const query = topic ? `?topic=${encodeURIComponent(topic)}` : '';
      return request<Recommendation>(`/recommendations/next${query}`);
    },
    getHistory: (limit: number = 20) =>
      request<RecommendationLog[]>(`/recommendations/history?limit=${limit}`),
    getExplanation: (topic: string) =>
      request<{
        topic: string;
        score: number;
        recommended_difficulty: string;
        confidence_level: string;
        formula: string;
        components: Record<string, number>;
        weights: Record<string, number>;
        explanation: string;
      }>(`/recommendations/explanation?topic=${encodeURIComponent(topic)}`),
  },

  questions: {
    getTopics: () => request<string[]>('/questions/topics/all'),
    list: (topic?: string, difficulty?: string) => {
      const params = new URLSearchParams();
      if (topic) params.append('topic', topic);
      if (difficulty) params.append('difficulty', difficulty);
      const query = params.toString() ? `?${params.toString()}` : '';
      return request<Question[]>(`/questions${query}`);
    },
  },

  research: {
    getStudies: () => request<ResearchStudy[]>('/research/studies'),
    getStudySummary: (studyId: number) => request<StudySummary>(`/research/studies/${studyId}/summary`),
    simulateParticipant: (studyId: number, strategy: string) =>
      request<{ message: string; pre_test_score: number; post_test_score: number; score_gain: number }>(
        `/research/studies/${studyId}/simulate-participant?strategy=${strategy}`,
        { method: 'POST' }
      ),
    exportCsvUrl: (studyId: number) => `${API_BASE}/research/studies/${studyId}/export`,
  },

  admin: {
    getStats: () =>
      request<{
        total_users: number;
        student_count: number;
        total_questions: number;
        active_questions: number;
        total_attempts: number;
        platform_accuracy: number;
        topic_distribution: Record<string, number>;
        status_distribution: Record<string, number>;
      }>('/admin/stats'),
    getUsers: (skip: number = 0, limit: number = 50) =>
      request<User[]>(`/admin/users?skip=${skip}&limit=${limit}`),
    createQuestion: (data: {
      title: string;
      statement: string;
      topic: string;
      subtopic?: string;
      difficulty: string;
      question_type?: string;
      options: string[];
      correct_answer: string;
      explanation: string;
      concept_tags?: string[];
      expected_duration_seconds?: number;
      status?: string;
    }) =>
      request<Question>('/admin/questions', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    updateQuestion: (
      questionId: number,
      data: {
        title?: string;
        statement?: string;
        topic?: string;
        subtopic?: string;
        difficulty?: string;
        options?: string[];
        correct_answer?: string;
        explanation?: string;
        concept_tags?: string[];
        expected_duration_seconds?: number;
        status?: string;
        is_active?: boolean;
      }
    ) =>
      request<Question>(`/admin/questions/${questionId}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    updateStatus: (questionId: number, newStatus: string) =>
      request<Question>(`/admin/questions/${questionId}/status?new_status=${newStatus}`, {
        method: 'PATCH',
      }),
    toggleActive: (questionId: number) =>
      request<Question>(`/admin/questions/${questionId}/toggle-active`, {
        method: 'PATCH',
      }),
  },
};

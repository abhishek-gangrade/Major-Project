import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Target,
  CheckCircle2,
  Clock,
  BookOpen,
  ArrowRight,
  TrendingUp,
  BrainCircuit,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import { OverallProgress, Recommendation } from '../types';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Overview: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [progress, setProgress] = useState<OverallProgress | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadOverviewData = async () => {
      try {
        setLoading(true);
        const [progressData, recData] = await Promise.all([
          api.progress.getOverview(),
          api.recommendations.getNext(),
        ]);
        setProgress(progressData);
        setRecommendation(recData);
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadOverviewData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Calibrating your placement proficiency profile..." />;
  }

  if (error || !progress) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <div>
          <p className="font-semibold">Unable to load dashboard</p>
          <p className="text-xs">{error || 'Please ensure the backend server is active.'}</p>
        </div>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Questions Attempted',
      value: progress.total_attempts,
      subtext: `${progress.unique_questions_attempted} unique questions`,
      icon: Target,
      color: 'text-teal-600 bg-teal-50',
    },
    {
      label: 'Overall Accuracy',
      value: `${progress.overall_accuracy}%`,
      subtext: `${progress.correct_attempts} correct / ${progress.incorrect_attempts} incorrect`,
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50',
    },
    {
      label: 'Active Placement Topics',
      value: `${progress.active_topics_count} / ${progress.topic_proficiencies.length}`,
      subtext: 'Curated technical areas',
      icon: BookOpen,
      color: 'text-indigo-600 bg-indigo-50',
    },
    {
      label: 'Avg. Solving Speed',
      value: `${progress.average_time_seconds}s`,
      subtext: 'Per attempted question',
      icon: Clock,
      color: 'text-amber-600 bg-amber-50',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-teal-700 to-teal-800 rounded-2xl p-6 text-white shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-medium tracking-wide uppercase">
              Placement Preparation
            </span>
            <span className="text-xs text-teal-100 flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> Adaptive Learning Engine
            </span>
          </div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">
            Welcome back, {user?.display_name}!
          </h1>
          <p className="text-xs md:text-sm text-teal-100 mt-1 max-w-2xl">
            AdaptivePrep calibrates your topic proficiency dynamically using correctness, recency, difficulty, and solving efficiency.
          </p>
        </div>
        <button
          onClick={() => navigate('/practice')}
          className="px-5 py-2.5 bg-white text-teal-800 hover:bg-teal-50 rounded-xl text-xs md:text-sm font-semibold transition shrink-0 shadow-sm flex items-center gap-2"
        >
          <span>Continue Adaptive Practice</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <Card key={i} className="p-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">{stat.label}</span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${stat.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-bold text-slate-800 tracking-tight">{stat.value}</span>
                <p className="text-[11px] text-slate-400 mt-0.5">{stat.subtext}</p>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Suggested Next Practice Action / Recommendation Spotlight */}
      {recommendation && (
        <Card
          className="border-teal-200 bg-gradient-to-br from-white to-teal-50/40"
          title="Recommended Next Practice Focus"
          subtitle="Generated dynamically from your current topic proficiency profile"
          headerAction={
            <Badge variant="teal" size="sm">
              Model: {recommendation.algorithm_version}
            </Badge>
          }
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-base font-bold text-slate-800">
                  {recommendation.topic}
                </span>
                <Badge
                  variant={
                    recommendation.target_difficulty === 'Easy'
                      ? 'easy'
                      : recommendation.target_difficulty === 'Medium'
                      ? 'medium'
                      : 'hard'
                  }
                  size="sm"
                >
                  Target Difficulty: {recommendation.target_difficulty}
                </Badge>
                <span className="text-xs font-semibold text-teal-700 bg-teal-100/60 px-2.5 py-0.5 rounded-full">
                  Proficiency: {recommendation.estimated_proficiency.toFixed(0)}/100
                </span>
                <span className="text-xs text-slate-400">
                  ({recommendation.observation_count} observations &bull; {recommendation.confidence_level} confidence)
                </span>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                <span className="font-semibold text-slate-700">Rationale: </span>
                {recommendation.reason}
              </p>
            </div>
            <button
              onClick={() => navigate(`/practice?topic=${encodeURIComponent(recommendation.topic)}`)}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-medium transition shrink-0 flex items-center gap-1.5 shadow-sm"
            >
              <BrainCircuit className="w-3.5 h-3.5" />
              <span>Practice {recommendation.topic}</span>
            </button>
          </div>
        </Card>
      )}

      {/* Topic Proficiency Breakdown */}
      <Card
        title="Placement Topic Proficiency Estimates"
        subtitle="Formula: S = 100 × (0.45A + 0.25R + 0.20D + 0.10E) with Dirichlet-Laplace smoothing"
        headerAction={
          <button
            onClick={() => navigate('/progress')}
            className="text-xs text-teal-700 hover:text-teal-800 font-medium flex items-center gap-1"
          >
            <span>View Full Analytics</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {progress.topic_proficiencies.map((topic) => {
            const score = Math.round(topic.estimated_proficiency);
            const isUncalibrated = topic.observation_count === 0;

            return (
              <div
                key={topic.topic}
                className="p-3.5 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 hover:bg-white transition flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-xs text-slate-800 truncate" title={topic.topic}>
                      {topic.topic}
                    </span>
                    <Badge
                      variant={
                        topic.recommended_difficulty === 'Easy'
                          ? 'easy'
                          : topic.recommended_difficulty === 'Medium'
                          ? 'medium'
                          : 'hard'
                      }
                      size="sm"
                    >
                      {topic.recommended_difficulty}
                    </Badge>
                  </div>

                  <div className="flex items-baseline justify-between text-xs mb-1">
                    <span className="text-slate-400 text-[11px]">
                      {isUncalibrated ? 'Baseline estimate' : `${topic.observation_count} attempts`}
                    </span>
                    <span className="font-bold text-slate-700">{score}/100</span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        score >= 70 ? 'bg-teal-600' : score >= 40 ? 'bg-amber-500' : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.max(5, score)}%` }}
                    />
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <span className="text-slate-400 capitalize">Confidence: {topic.confidence_level}</span>
                  <button
                    onClick={() => navigate(`/practice?topic=${encodeURIComponent(topic.topic)}`)}
                    className="text-teal-700 hover:text-teal-800 font-semibold"
                  >
                    Solve &rarr;
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Recent Attempts Table */}
      <Card
        title="Recent Practice History"
        subtitle="Latest problem-solving attempts recorded in the database"
      >
        {progress.recent_attempts.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-400">
            No attempts recorded yet. Click "Start Practice" to begin your first adaptive session!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="pb-2.5 font-medium">Question Title</th>
                  <th className="pb-2.5 font-medium">Topic</th>
                  <th className="pb-2.5 font-medium">Difficulty</th>
                  <th className="pb-2.5 font-medium">Result</th>
                  <th className="pb-2.5 font-medium">Duration</th>
                  <th className="pb-2.5 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {progress.recent_attempts.slice(0, 6).map((att) => (
                  <tr key={att.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 font-medium text-slate-800 pr-3 truncate max-w-[200px]">
                      {att.question_title}
                    </td>
                    <td className="py-2.5 text-slate-600 pr-3">{att.topic}</td>
                    <td className="py-2.5 pr-3">
                      <Badge
                        variant={
                          att.difficulty === 'Easy'
                            ? 'easy'
                            : att.difficulty === 'Medium'
                            ? 'medium'
                            : 'hard'
                        }
                        size="sm"
                      >
                        {att.difficulty}
                      </Badge>
                    </td>
                    <td className="py-2.5 pr-3">
                      {att.is_correct ? (
                        <span className="text-emerald-700 font-semibold flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                        </span>
                      ) : (
                        <span className="text-rose-600 font-medium">Incorrect</span>
                      )}
                    </td>
                    <td className="py-2.5 text-slate-500 pr-3">{att.time_taken_seconds}s</td>
                    <td className="py-2.5 text-slate-400">
                      {new Date(att.attempt_timestamp).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};


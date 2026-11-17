import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Cell,
} from 'recharts';
import {
  BarChart2,
  TrendingUp,
  Target,
  CheckCircle2,
  Layers,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { api } from '../services/api';
import { OverallProgress } from '../types';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Progress: React.FC = () => {
  const [progress, setProgress] = useState<OverallProgress | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        setLoading(true);
        const data = await api.progress.getOverview();
        setProgress(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load progress analytics');
      } finally {
        setLoading(false);
      }
    };
    fetchProgress();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Aggregating performance telemetry and learning curves..." />;
  }

  if (error || !progress) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <div>
          <p className="font-semibold">Unable to load progress analytics</p>
          <p className="text-xs">{error || 'Please ensure backend is reachable.'}</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const topicChartData = progress.topic_proficiencies.map((t) => ({
    topic: t.topic.length > 14 ? `${t.topic.slice(0, 12)}...` : t.topic,
    fullTopic: t.topic,
    score: Math.round(t.estimated_proficiency),
    difficulty: t.recommended_difficulty,
    attempts: t.observation_count,
  }));

  const trendChartData = progress.accuracy_trend.map((point) => ({
    attempt: `#${point.attempt_index}`,
    accuracy: point.rolling_accuracy,
    topic: point.topic,
    result: point.is_correct ? 'Correct' : 'Incorrect',
  }));

  const diffData = [
    {
      level: 'Easy',
      total: progress.difficulty_breakdown.Easy.total,
      correct: progress.difficulty_breakdown.Easy.correct,
      rate:
        progress.difficulty_breakdown.Easy.total > 0
          ? Math.round(
              (progress.difficulty_breakdown.Easy.correct /
                progress.difficulty_breakdown.Easy.total) *
                100
            )
          : 0,
      color: '#10b981',
    },
    {
      level: 'Medium',
      total: progress.difficulty_breakdown.Medium.total,
      correct: progress.difficulty_breakdown.Medium.correct,
      rate:
        progress.difficulty_breakdown.Medium.total > 0
          ? Math.round(
              (progress.difficulty_breakdown.Medium.correct /
                progress.difficulty_breakdown.Medium.total) *
                100
            )
          : 0,
      color: '#f59e0b',
    },
    {
      level: 'Hard',
      total: progress.difficulty_breakdown.Hard.total,
      correct: progress.difficulty_breakdown.Hard.correct,
      rate:
        progress.difficulty_breakdown.Hard.total > 0
          ? Math.round(
              (progress.difficulty_breakdown.Hard.correct /
                progress.difficulty_breakdown.Hard.total) *
                100
            )
          : 0,
      color: '#ef4444',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-xl font-bold text-slate-800 tracking-tight">Progress Analytics</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Topic-wise estimated proficiency, rolling accuracy trends, and historical solving telemetry.
        </p>
      </div>

      {/* Primary Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Topic-Wise Estimated Proficiency Bar Chart */}
        <Card
          title="Topic Proficiency Distribution"
          subtitle="Estimated proficiency score (0 - 100) per placement topic"
        >
          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicChartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis
                  dataKey="topic"
                  tick={{ fontSize: 10, fill: '#64748b' }}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
                <Tooltip
                  formatter={(val: any) => [`${val}/100`, 'Proficiency']}
                  labelFormatter={(_: any, payload: any) => {
                    if (payload && payload[0]) {
                      return payload[0].payload.fullTopic;
                    }
                    return '';
                  }}
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    borderRadius: '8px',
                    color: '#f8fafc',
                    fontSize: '12px',
                    border: 'none',
                  }}
                />
                <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                  {topicChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.score >= 70 ? '#167D74' : entry.score >= 40 ? '#f59e0b' : '#ef4444'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center justify-center gap-4 text-[11px] text-slate-500 mt-3 pt-2 border-t border-slate-100">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-[#167D74]"></span> Mastery (&ge;70)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-amber-500"></span> Intermediate (40-69)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-xs bg-rose-500"></span> Needs Review (&lt;40)
            </span>
          </div>
        </Card>

        {/* Rolling Accuracy Trend Line Chart */}
        <Card
          title="Cumulative Accuracy Trend"
          subtitle="Rolling correctness percentage over sequential practice attempts"
        >
          {trendChartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-xs text-slate-400">
              No attempt trend data available yet.
            </div>
          ) : (
            <div className="h-64 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendChartData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="attempt" tick={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} unit="%" />
                  <Tooltip
                    formatter={(val: any) => [`${val}%`, 'Accuracy']}
                    labelFormatter={(_: any, payload: any) => {
                      if (payload && payload[0]) {
                        return `${payload[0].payload.attempt} - ${payload[0].payload.topic} (${payload[0].payload.result})`;
                      }
                      return '';
                    }}
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '12px',
                      border: 'none',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="accuracy"
                    stroke="#167D74"
                    strokeWidth={2.5}
                    dot={{ fill: '#167D74', r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          <div className="text-center text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
            Latest overall accuracy: <strong className="text-slate-700">{progress.overall_accuracy}%</strong> across {progress.total_attempts} attempts
          </div>
        </Card>
      </div>

      {/* Difficulty Breakdown Grid */}
      <Card
        title="Performance by Difficulty Tier"
        subtitle="Attempt distribution and success rates across Easy, Medium, and Hard placement questions"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {diffData.map((tier) => (
            <div
              key={tier.level}
              className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Badge
                    variant={
                      tier.level === 'Easy'
                        ? 'easy'
                        : tier.level === 'Medium'
                        ? 'medium'
                        : 'hard'
                    }
                  >
                    {tier.level} Questions
                  </Badge>
                  <span className="text-xs font-bold text-slate-700">{tier.rate}% Correct</span>
                </div>
                <div className="flex items-baseline justify-between text-xs text-slate-500 mb-1">
                  <span>Attempts completed</span>
                  <span className="font-semibold">{tier.total}</span>
                </div>
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full transition-all duration-500"
                    style={{ width: `${tier.rate}%`, backgroundColor: tier.color }}
                  />
                </div>
              </div>
              <p className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
                {tier.correct} solved correctly out of {tier.total} attempts
              </p>
            </div>
          ))}
        </div>
      </Card>

      {/* Full Chronological Attempt History */}
      <Card
        title="Detailed Attempt Audit Trail"
        subtitle="Chronological record of student responses with timestamp and timing bounds"
      >
        {progress.recent_attempts.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-400">
            No history records found.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="pb-3 font-medium">Question</th>
                  <th className="pb-3 font-medium">Topic</th>
                  <th className="pb-3 font-medium">Difficulty</th>
                  <th className="pb-3 font-medium">Submitted Response</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Duration</th>
                  <th className="pb-3 font-medium">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {progress.recent_attempts.map((att) => (
                  <tr key={att.id} className="hover:bg-slate-50/50">
                    <td className="py-2.5 font-medium text-slate-800 pr-3 max-w-[220px] truncate">
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
                    <td className="py-2.5 text-slate-600 pr-3 max-w-[180px] truncate" title={att.submitted_answer}>
                      {att.submitted_answer}
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
                    <td className="py-2.5 text-slate-500 pr-3 font-mono">{att.time_taken_seconds}s</td>
                    <td className="py-2.5 text-slate-400 whitespace-nowrap">
                      {new Date(att.attempt_timestamp).toLocaleString(undefined, {
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


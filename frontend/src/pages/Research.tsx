import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  FlaskConical,
  Download,
  Users,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  Play,
  FileSpreadsheet,
  AlertCircle,
  HelpCircle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { api } from '../services/api';
import { ResearchStudy, StudySummary } from '../types';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Research: React.FC = () => {
  const [studies, setStudies] = useState<ResearchStudy[]>([]);
  const [selectedStudyId, setSelectedStudyId] = useState<number | null>(null);
  const [summary, setSummary] = useState<StudySummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simulationMsg, setSimulationMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load studies
  useEffect(() => {
    const fetchStudies = async () => {
      try {
        setLoading(true);
        const res = await api.research.getStudies();
        setStudies(res);
        if (res.length > 0) {
          setSelectedStudyId(res[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load research studies');
      } finally {
        setLoading(false);
      }
    };
    fetchStudies();
  }, []);

  // Load summary for selected study
  const loadSummary = async (studyId: number) => {
    try {
      const data = await api.research.getStudySummary(studyId);
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load study summary', err);
    }
  };

  useEffect(() => {
    if (selectedStudyId) {
      loadSummary(selectedStudyId);
    }
  }, [selectedStudyId]);

  const handleSimulate = async (strategy: string) => {
    if (!selectedStudyId) return;
    try {
      setSimulating(true);
      setSimulationMsg(null);
      const res = await api.research.simulateParticipant(selectedStudyId, strategy);
      setSimulationMsg(res.message);
      await loadSummary(selectedStudyId);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleExportCsv = () => {
    if (!selectedStudyId) return;
    const token = localStorage.getItem('adaptiveprep_token');
    const url = api.research.exportCsvUrl(selectedStudyId);
    // Trigger browser download via fetch with auth header
    fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => res.blob())
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `adaptiveprep_study_${selectedStudyId}_pseudonymized_export.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      })
      .catch((err) => alert(`Export failed: ${err.message}`));
  };

  if (loading) {
    return <LoadingSpinner message="Loading empirical research studies and comparative telemetry..." />;
  }

  if (error || !summary) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <div>
          <p className="font-semibold">Unable to load research module</p>
          <p className="text-xs">{error || 'Please ensure backend is running.'}</p>
        </div>
      </div>
    );
  }

  // Format chart data for comparison: Pre vs Post vs Absolute Delta
  const comparisonChartData = summary.strategies.map((s) => ({
    name:
      s.strategy === 'adaptive'
        ? 'Adaptive (Multi-Factor)'
        : s.strategy === 'accuracy_only'
        ? 'Accuracy-Only'
        : 'Random Selection',
    PreTest: s.pre_test_mean,
    PostTest: s.post_test_mean,
    ScoreGain: s.absolute_change_mean,
    rawStrategy: s.strategy,
  }));

  return (
    <div className="space-y-6">
      {/* Header with Export CTA */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">Research & Evaluation</h1>
            <Badge variant="teal" size="sm">
              Major Project Evaluation Protocol
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Empirical investigation of adaptive placement question selection against baseline strategies.
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="flex items-center space-x-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold transition shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Pseudonymized CSV</span>
        </button>
      </div>

      {/* Study Metadata Card */}
      <Card
        className="border-teal-100 bg-gradient-to-r from-teal-50/50 to-white"
        title={summary.study.title}
        subtitle={`Protocol Version: ${summary.study.protocol_version} • Target N: ${summary.study.target_sample_size}`}
        headerAction={
          <Badge variant="success" size="sm">
            Status: {summary.study.status.toUpperCase()}
          </Badge>
        }
      >
        <p className="text-xs text-slate-600 leading-relaxed mb-4">
          {summary.study.description}
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-slate-200/60 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Enrolled Participants</span>
            <span className="font-bold text-slate-800">{summary.total_participants}</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Completion Rate</span>
            <span className="font-bold text-teal-700">{summary.overall_completion_rate}%</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Experimental Conditions</span>
            <span className="font-bold text-slate-800">3 (Adaptive / Accuracy / Random)</span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Institution</span>
            <span className="font-bold text-slate-800">Medi-Caps University</span>
          </div>
        </div>
      </Card>

      {/* Simulation Banner */}
      {simulationMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center justify-between">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {simulationMsg}
          </span>
          <button
            onClick={() => setSimulationMsg(null)}
            className="text-xs text-emerald-700 hover:underline font-medium"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Comparative Bar Chart */}
      <Card
        title="Comparative Outcome Evaluation: Pre-Test vs Post-Test by Strategy"
        subtitle="Comparing learning gains across Adaptive, Accuracy-Only, and Random question selection conditions"
        headerAction={
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 hidden sm:inline">Simulate trial:</span>
            <button
              disabled={simulating}
              onClick={() => handleSimulate('adaptive')}
              className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 rounded-md text-[11px] font-semibold transition flex items-center gap-1"
            >
              <Play className="w-3 h-3" /> + Adaptive
            </button>
            <button
              disabled={simulating}
              onClick={() => handleSimulate('accuracy_only')}
              className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 rounded-md text-[11px] font-semibold transition flex items-center gap-1"
            >
              <Play className="w-3 h-3" /> + Accuracy
            </button>
            <button
              disabled={simulating}
              onClick={() => handleSimulate('random')}
              className="px-2.5 py-1 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-md text-[11px] font-semibold transition flex items-center gap-1"
            >
              <Play className="w-3 h-3" /> + Random
            </button>
          </div>
        }
      >
        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={comparisonChartData}
              margin={{ top: 10, right: 20, left: -20, bottom: 15 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#334155', fontWeight: 500 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  borderRadius: '8px',
                  color: '#f8fafc',
                  fontSize: '12px',
                  border: 'none',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              <Bar dataKey="PreTest" fill="#94a3b8" name="Pre-Test Baseline" radius={[4, 4, 0, 0]} />
              <Bar dataKey="PostTest" fill="#167D74" name="Post-Test Outcome" radius={[4, 4, 0, 0]} />
              <Bar dataKey="ScoreGain" fill="#0f766e" name="Score Gain (Δ)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Comparative Statistics Table */}
      <Card
        title="Descriptive Summary Metrics by Strategy Condition"
        subtitle="Aggregate outcomes computed across completed participant trials"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="pb-3 font-medium">Experimental Condition</th>
                <th className="pb-3 font-medium">Sample Size (n)</th>
                <th className="pb-3 font-medium">Pre-Test Mean</th>
                <th className="pb-3 font-medium">Post-Test Mean</th>
                <th className="pb-3 font-medium">Score Gain (Δ)</th>
                <th className="pb-3 font-medium">Relative Improvement</th>
                <th className="pb-3 font-medium">Avg Solving Duration</th>
                <th className="pb-3 font-medium">Completion Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {summary.strategies.map((stat) => (
                <tr key={stat.strategy} className="hover:bg-slate-50/50">
                  <td className="py-3 font-semibold text-slate-800 capitalize">
                    {stat.strategy === 'adaptive' ? (
                      <span className="flex items-center gap-1.5 text-teal-800">
                        <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                        Multi-Factor Adaptive (Proposed)
                      </span>
                    ) : stat.strategy === 'accuracy_only' ? (
                      'Accuracy-Only Baseline'
                    ) : (
                      'Random Question Selection'
                    )}
                  </td>
                  <td className="py-3 font-mono text-slate-700">{stat.participant_count}</td>
                  <td className="py-3 text-slate-600">{stat.pre_test_mean}%</td>
                  <td className="py-3 text-slate-600">{stat.post_test_mean}%</td>
                  <td className="py-3 font-bold text-slate-900">
                    +{stat.absolute_change_mean} pts
                  </td>
                  <td className="py-3 font-medium text-emerald-700">
                    +{stat.percentage_improvement_mean}%
                  </td>
                  <td className="py-3 text-slate-500 font-mono">
                    {stat.avg_solving_time_seconds}s
                  </td>
                  <td className="py-3">
                    <Badge variant={stat.completion_rate >= 80 ? 'success' : 'neutral'} size="sm">
                      {stat.completion_rate}%
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Research Protocol, Assumptions, and Ethics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Data Dictionary */}
        <Card title="Pseudonymized Export Data Dictionary" subtitle="Standardized schema for researcher data reuse">
          <div className="space-y-2.5 text-xs">
            {Object.entries(summary.data_dictionary).map(([key, desc]) => (
              <div key={key} className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                <code className="text-teal-700 font-semibold">{key}</code>
                <p className="text-slate-600 text-[11px] mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Assumptions and Limitations */}
        <Card
          title="Methodological Notes & Limitations"
          subtitle="Honest academic disclosure of evaluation constraints"
        >
          <div className="space-y-2.5 text-xs text-slate-600">
            {summary.assumptions_and_limitations.map((note, idx) => (
              <div key={idx} className="flex items-start gap-2.5 p-2.5 bg-amber-50/50 border border-amber-100 rounded-lg">
                <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{note}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};


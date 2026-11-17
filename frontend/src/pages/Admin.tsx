import React, { useEffect, useState } from 'react';
import {
  ShieldCheck,
  Plus,
  CheckCircle2,
  XCircle,
  Eye,
  ToggleLeft,
  ToggleRight,
  BookOpen,
  Filter,
  Users,
  Target,
  BarChart2,
  AlertCircle,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import { Question } from '../types';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Admin: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [topics, setTopics] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);

  // New question form state
  const [newTitle, setNewTitle] = useState('');
  const [newStatement, setNewStatement] = useState('');
  const [newTopic, setNewTopic] = useState('Arrays');
  const [newSubtopic, setNewSubtopic] = useState('');
  const [newDifficulty, setNewDifficulty] = useState('Easy');
  const [newStatus, setNewStatus] = useState('published');
  const [newConceptTags, setNewConceptTags] = useState('');
  const [newOptions, setNewOptions] = useState<string[]>(['', '', '', '']);
  const [newCorrectAnswer, setNewCorrectAnswer] = useState('');
  const [newExplanation, setNewExplanation] = useState('');
  const [newDuration, setNewDuration] = useState<number>(90);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, qsData, topicsList] = await Promise.all([
        api.admin.getStats(),
        api.questions.list(selectedTopic || undefined, selectedDifficulty || undefined),
        api.questions.getTopics(),
      ]);
      setStats(statsData);
      setQuestions(qsData);
      setTopics(topicsList);
      if (topicsList.length > 0 && !newTopic) {
        setNewTopic(topicsList[0]);
      }
    } catch (err: any) {
      console.error('Failed to load admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedTopic, selectedDifficulty]);

  const handleToggleActive = async (qId: number) => {
    try {
      const updated = await api.admin.toggleActive(qId);
      setQuestions((prev) =>
        prev.map((q) => (q.id === qId ? { ...q, is_active: updated.is_active } : q))
      );
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const handleStatusChange = async (qId: number, status: string) => {
    try {
      const updated = await api.admin.updateStatus(qId, status);
      setQuestions((prev) =>
        prev.map((q) => (q.id === qId ? { ...q, status: updated.status, is_active: updated.is_active } : q))
      );
    } catch (err: any) {
      alert(`Failed to transition question lifecycle: ${err.message}`);
    }
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const filteredOptions = newOptions.map((o) => o.trim()).filter(Boolean);
    if (filteredOptions.length < 2) {
      setFormError('Please provide at least 2 distinct options.');
      return;
    }

    if (!newCorrectAnswer || !filteredOptions.includes(newCorrectAnswer.trim())) {
      setFormError('The correct answer must exactly match one of the options.');
      return;
    }

    try {
      setFormSubmitting(true);
      const tagsArray = newConceptTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);

      await api.admin.createQuestion({
        title: newTitle.trim(),
        statement: newStatement.trim(),
        topic: newTopic,
        subtopic: newSubtopic.trim() || undefined,
        difficulty: newDifficulty,
        status: newStatus,
        concept_tags: tagsArray.length > 0 ? tagsArray : undefined,
        options: filteredOptions,
        correct_answer: newCorrectAnswer.trim(),
        explanation: newExplanation.trim(),
        expected_duration_seconds: newDuration,
      });

      setShowAddModal(false);
      // Reset form
      setNewTitle('');
      setNewStatement('');
      setNewSubtopic('');
      setNewConceptTags('');
      setNewStatus('published');
      setNewOptions(['', '', '', '']);
      setNewCorrectAnswer('');
      setNewExplanation('');
      await loadData();
    } catch (err: any) {
      setFormError(err.message || 'Failed to create question');
    } finally {
      setFormSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">Question Bank Administration</h1>
            <Badge variant="teal" size="sm">
              Staff Access
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Curate placement problem inventory, inspect solution models, and manage content activation.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold transition shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add New Question</span>
        </button>
      </div>

      {/* Admin Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <span className="text-xs font-medium text-slate-500">Total Placement Questions</span>
            <div className="mt-2 text-2xl font-bold text-slate-800">
              {stats.total_questions}{' '}
              <span className="text-xs font-normal text-emerald-600">({stats.active_questions} active)</span>
            </div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-medium text-slate-500">Registered Students</span>
            <div className="mt-2 text-2xl font-bold text-slate-800">{stats.student_count}</div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-medium text-slate-500">Platform Practice Attempts</span>
            <div className="mt-2 text-2xl font-bold text-slate-800">{stats.total_attempts}</div>
          </Card>
          <Card className="p-4">
            <span className="text-xs font-medium text-slate-500">Platform Accuracy</span>
            <div className="mt-2 text-2xl font-bold text-teal-700">{stats.platform_accuracy}%</div>
          </Card>
        </div>
      )}

      {/* Filter controls */}
      <Card>
        <div className="flex flex-wrap items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-medium text-slate-600">Topic:</span>
            <select
              value={selectedTopic}
              onChange={(e) => setSelectedTopic(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-700 rounded-md px-2.5 py-1 focus:outline-none"
            >
              <option value="">All Topics</option>
              {topics.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="font-medium text-slate-600">Difficulty:</span>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="bg-slate-50 border border-slate-200 text-slate-700 rounded-md px-2.5 py-1 focus:outline-none"
            >
              <option value="">All Difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </div>

          <span className="text-slate-400 ml-auto">{questions.length} questions listed</span>
        </div>
      </Card>

      {/* Questions Table */}
      {loading ? (
        <LoadingSpinner message="Loading question bank inventory..." />
      ) : (
        <Card title="Question Bank Inventory">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="pb-3 font-medium">ID</th>
                  <th className="pb-3 font-medium">Question Title</th>
                  <th className="pb-3 font-medium">Topic / Subtopic</th>
                  <th className="pb-3 font-medium">Difficulty</th>
                  <th className="pb-3 font-medium">Correct Key</th>
                  <th className="pb-3 font-medium">Lifecycle</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {questions.map((q) => {
                  const status = q.status || (q.is_active ? 'published' : 'archived');
                  return (
                    <tr key={q.id} className="hover:bg-slate-50/50">
                      <td className="py-3 font-mono text-slate-400">
                        <div className="flex items-center gap-1">
                          <span>#{q.id}</span>
                          <span className="text-[9px] bg-slate-100 text-slate-500 font-mono px-1 rounded">
                            v{q.version || 1}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 font-medium text-slate-800 pr-3 max-w-[220px]">
                        <div className="truncate" title={q.title}>
                          {q.title}
                        </div>
                        {q.concept_tags && q.concept_tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {q.concept_tags.slice(0, 2).map((tag, i) => (
                              <span
                                key={i}
                                className="inline-block px-1.5 py-0.2 text-[9px] bg-slate-100 text-slate-600 rounded"
                              >
                                #{tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="py-3 text-slate-600 pr-3">
                        <div className="font-medium">{q.topic}</div>
                        {q.subtopic && <div className="text-[10px] text-slate-400">{q.subtopic}</div>}
                      </td>
                      <td className="py-3 pr-3">
                        <Badge
                          variant={
                            q.difficulty === 'Easy'
                              ? 'easy'
                              : q.difficulty === 'Medium'
                              ? 'medium'
                              : 'hard'
                          }
                          size="sm"
                        >
                          {q.difficulty}
                        </Badge>
                      </td>
                      <td
                        className="py-3 text-emerald-800 font-semibold pr-3 max-w-[160px] truncate"
                        title={q.correct_answer}
                      >
                        {q.correct_answer}
                      </td>
                      <td className="py-3 pr-3">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            status === 'published'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : status === 'in_review'
                              ? 'bg-sky-50 text-sky-700 border border-sky-200'
                              : status === 'draft'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : 'bg-slate-100 text-slate-500 border border-slate-200'
                          }`}
                        >
                          {status}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <select
                            value={status}
                            onChange={(e) => handleStatusChange(q.id, e.target.value)}
                            className="bg-white border border-slate-200 text-slate-700 rounded px-2 py-1 text-[11px] focus:outline-none"
                            title="Transition lifecycle stage"
                          >
                            <option value="published">Published</option>
                            <option value="in_review">In Review</option>
                            <option value="draft">Draft</option>
                            <option value="archived">Archived</option>
                          </select>
                          <button
                            onClick={() => handleToggleActive(q.id)}
                            className={`text-[11px] font-semibold px-2 py-1 rounded transition ${
                              q.is_active
                                ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                                : 'bg-teal-50 hover:bg-teal-100 text-teal-700'
                            }`}
                          >
                            {q.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add Question Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="font-bold text-slate-800 text-base">Add Placement Question</h3>
              <button onClick={() => setShowAddModal(false)}>
                <X className="w-5 h-5 text-slate-400 hover:text-slate-600" />
              </button>
            </div>

            {formError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-xs">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateQuestion} className="space-y-4 text-xs">
              <div>
                <label className="font-medium text-slate-700 block mb-1">Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Kadane's Algorithm Revisit"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Topic</label>
                  <select
                    value={newTopic}
                    onChange={(e) => setNewTopic(e.target.value)}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  >
                    {topics.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Subtopic</label>
                  <input
                    type="text"
                    placeholder="e.g. Sliding Window"
                    value={newSubtopic}
                    onChange={(e) => setNewSubtopic(e.target.value)}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Difficulty</label>
                  <select
                    value={newDifficulty}
                    onChange={(e) => setNewDifficulty(e.target.value)}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Lifecycle Status</label>
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                    className="w-full px-2.5 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  >
                    <option value="published">Published</option>
                    <option value="draft">Draft</option>
                    <option value="in_review">In Review</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Concept Tags (comma separated)</label>
                  <input
                    type="text"
                    placeholder="e.g. array, two-pointers, kadane"
                    value={newConceptTags}
                    onChange={(e) => setNewConceptTags(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  />
                </div>
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Expected Seconds</label>
                  <input
                    type="number"
                    min="10"
                    max="600"
                    value={newDuration}
                    onChange={(e) => setNewDuration(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">Problem Statement</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Specify the placement problem statement clearly..."
                  value={newStatement}
                  onChange={(e) => setNewStatement(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                />
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">Multiple Choice Options</label>
                <div className="space-y-2">
                  {newOptions.map((opt, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="w-5 text-center font-bold text-slate-400">
                        {String.fromCharCode(65 + idx)}
                      </span>
                      <input
                        type="text"
                        required
                        placeholder={`Option ${String.fromCharCode(65 + idx)}`}
                        value={opt}
                        onChange={(e) => {
                          const updated = [...newOptions];
                          updated[idx] = e.target.value;
                          setNewOptions(updated);
                        }}
                        className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-xs focus:outline-none"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">
                  Correct Answer (Must match option exactly)
                </label>
                <input
                  type="text"
                  required
                  placeholder="Paste the exact string of the correct option"
                  value={newCorrectAnswer}
                  onChange={(e) => setNewCorrectAnswer(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">Solution Explanation</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Step-by-step reasoning or mathematical proof of the solution..."
                  value={newExplanation}
                  onChange={(e) => setNewExplanation(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-semibold transition"
                >
                  {formSubmitting ? 'Saving...' : 'Add to Question Bank'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};


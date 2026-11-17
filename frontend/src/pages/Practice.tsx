import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Sparkles,
  BookOpen,
  BrainCircuit,
  RotateCcw,
  AlertCircle,
  HelpCircle,
  Layers,
  Tag,
  Gauge,
} from 'lucide-react';
import { api } from '../services/api';
import { Question, AttemptFeedback } from '../types';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Practice: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTopic = searchParams.get('topic') || '';

  const [topics, setTopics] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<string>(initialTopic);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [recommendationReason, setRecommendationReason] = useState<string>('');
  const [selectedOption, setSelectedOption] = useState<string>('');
  const [feedback, setFeedback] = useState<AttemptFeedback | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Timing state
  const [secondsElapsed, setSecondsElapsed] = useState<number>(0);
  const [startedAtIso, setStartedAtIso] = useState<string>('');
  const timerRef = useRef<any>(null);

  // Fetch topics list
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const topicList = await api.questions.getTopics();
        setTopics(topicList);
      } catch (err: any) {
        console.error('Failed to load topics', err);
      }
    };
    fetchTopics();
  }, []);

  // Fetch next question when selectedTopic changes
  const loadNextQuestion = async (topicToFetch?: string) => {
    try {
      setLoading(true);
      setError(null);
      setFeedback(null);
      setSelectedOption('');
      setSecondsElapsed(0);
      const nowIso = new Date().toISOString();
      setStartedAtIso(nowIso);

      const target = topicToFetch !== undefined ? topicToFetch : selectedTopic;
      const res = await api.practice.getNextQuestion(target || undefined);

      setCurrentQuestion(res.question);
      setRecommendationReason(res.recommendation_reason);

      // Start timer
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = setInterval(() => {
        setSecondsElapsed((prev) => prev + 1);
      }, 1000);
    } catch (err: any) {
      setError(err.message || 'No questions available for this selection.');
      setCurrentQuestion(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNextQuestion(selectedTopic);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [selectedTopic]);

  const handleTopicChange = (newTopic: string) => {
    setSelectedTopic(newTopic);
    if (newTopic) {
      setSearchParams({ topic: newTopic });
    } else {
      setSearchParams({});
    }
  };

  const handleSubmit = async () => {
    if (!currentQuestion || !selectedOption) return;

    if (timerRef.current) clearInterval(timerRef.current);

    try {
      setSubmitting(true);
      const res = await api.practice.submitAttempt({
        question_id: currentQuestion.id,
        submitted_answer: selectedOption,
        time_taken_seconds: Math.max(3, secondsElapsed),
        started_at: startedAtIso,
      });
      setFeedback(res);
    } catch (err: any) {
      setError(err.message || 'Failed to submit attempt.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleContinue = () => {
    loadNextQuestion(selectedTopic);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header and Topic Filter Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">Adaptive Practice</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time difficulty adjustment tailored to your proficiency and solving speed.
          </p>
        </div>

        {/* Topic dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500 whitespace-nowrap">Topic Filter:</span>
          <select
            value={selectedTopic}
            onChange={(e) => handleTopicChange(e.target.value)}
            className="text-xs font-medium bg-white border border-slate-200 text-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600 transition"
          >
            <option value="">All Topics (Adaptive Auto-Select)</option>
            {topics.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Selecting personalized candidate question..." />
      ) : error ? (
        <Card className="text-center py-10">
          <AlertCircle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
          <h3 className="font-semibold text-slate-800 text-sm">Unable to load question</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-4">{error}</p>
          <button
            onClick={() => handleTopicChange('')}
            className="px-4 py-2 bg-teal-600 text-white rounded-lg text-xs font-medium hover:bg-teal-700 transition"
          >
            Switch to All Topics
          </button>
        </Card>
      ) : currentQuestion ? (
        <div className="space-y-6">
          {/* Question Card */}
          <Card className="border-slate-200/90 shadow-sm">
            {/* Top metadata row */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="teal" size="sm">
                  {currentQuestion.topic}
                </Badge>
                {currentQuestion.subtopic && (
                  <span className="text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                    {currentQuestion.subtopic}
                  </span>
                )}
                <Badge
                  variant={
                    currentQuestion.difficulty === 'Easy'
                      ? 'easy'
                      : currentQuestion.difficulty === 'Medium'
                      ? 'medium'
                      : 'hard'
                  }
                  size="sm"
                >
                  {currentQuestion.difficulty}
                </Badge>
                <span className="text-[10px] text-slate-400">v{currentQuestion.version || 1}</span>
              </div>

              {/* Live Timer */}
              <div className="flex items-center gap-1.5 font-mono text-slate-500 bg-slate-50 border border-slate-100 px-2.5 py-1 rounded-md">
                <Clock className="w-3.5 h-3.5 text-teal-600" />
                <span>
                  {Math.floor(secondsElapsed / 60)}:
                  {(secondsElapsed % 60).toString().padStart(2, '0')}
                </span>
                <span className="text-[10px] text-slate-400">
                  / {currentQuestion.expected_duration_seconds}s exp.
                </span>
              </div>
            </div>

            {/* Recommendation rationale banner */}
            {recommendationReason && !feedback && (
              <div className="my-3 p-3 bg-teal-50/70 border border-teal-100 rounded-lg text-xs text-teal-900 flex items-start gap-2">
                <BrainCircuit className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-teal-800">Adaptive Recommendation Rationale: </span>
                  {recommendationReason}
                </div>
              </div>
            )}

            {/* Question Statement */}
            <div className="py-4">
              <h2 className="text-sm md:text-base font-semibold text-slate-900 leading-snug mb-2">
                {currentQuestion.title}
              </h2>
              <p className="text-xs md:text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                {currentQuestion.statement}
              </p>

              {/* Concept tags */}
              {currentQuestion.concept_tags && currentQuestion.concept_tags.length > 0 && (
                <div className="flex items-center gap-1.5 mt-3 pt-2">
                  <Tag className="w-3 h-3 text-slate-400" />
                  {currentQuestion.concept_tags.map((tag, i) => (
                    <span key={i} className="text-[10px] font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Options List */}
            <div className="space-y-2.5 pt-2">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Select your answer:
              </span>
              {currentQuestion.options.map((opt, idx) => {
                const isSelected = selectedOption === opt;
                const isSubmitted = !!feedback;
                const isCorrectOption = feedback && opt === feedback.correct_answer;
                const isWrongSelection = feedback && isSelected && !feedback.is_correct;

                let optionStyles = 'border-slate-200 hover:border-teal-500/60 hover:bg-teal-50/30';
                if (isSelected && !isSubmitted) {
                  optionStyles = 'border-teal-600 bg-teal-50/50 ring-1 ring-teal-600 text-teal-950 font-medium';
                } else if (isCorrectOption) {
                  optionStyles = 'border-emerald-500 bg-emerald-50 text-emerald-950 font-medium ring-1 ring-emerald-500';
                } else if (isWrongSelection) {
                  optionStyles = 'border-rose-400 bg-rose-50 text-rose-950 line-through';
                }

                return (
                  <button
                    key={idx}
                    type="button"
                    disabled={isSubmitted || submitting}
                    onClick={() => setSelectedOption(opt)}
                    className={`w-full text-left p-3.5 rounded-xl border text-xs md:text-sm transition flex items-center justify-between ${optionStyles}`}
                  >
                    <div className="flex items-center gap-3">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${
                          isSelected
                            ? 'bg-teal-600 text-white'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {String.fromCharCode(65 + idx)}
                      </span>
                      <span className="leading-relaxed">{opt}</span>
                    </div>

                    {isCorrectOption && (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                    )}
                    {isWrongSelection && (
                      <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Submit Action */}
            {!feedback && (
              <div className="pt-6 border-t border-slate-100 mt-6 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  {selectedOption ? 'Ready to submit' : 'Please select an option to submit'}
                </span>
                <button
                  onClick={handleSubmit}
                  disabled={!selectedOption || submitting}
                  className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-lg text-xs md:text-sm font-semibold transition shadow-sm shadow-teal-600/20"
                >
                  {submitting ? 'Evaluating...' : 'Submit Answer'}
                </button>
              </div>
            )}
          </Card>

          {/* Feedback Screen */}
          {feedback && (
            <Card
              className={`border-2 animate-fadeIn ${
                feedback.is_correct ? 'border-emerald-300 bg-emerald-50/20' : 'border-rose-200 bg-rose-50/20'
              }`}
            >
              <div className="space-y-4">
                {/* Result Headline */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    {feedback.is_correct ? (
                      <div className="w-9 h-9 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                    ) : (
                      <div className="w-9 h-9 rounded-full bg-rose-100 flex items-center justify-center text-rose-700">
                        <XCircle className="w-5 h-5" />
                      </div>
                    )}
                    <div>
                      <h3 className="font-bold text-slate-800 text-sm md:text-base">
                        {feedback.is_correct ? 'Correct Solution!' : 'Incorrect Answer'}
                      </h3>
                      <p className="text-xs text-slate-500">
                        Completed in {feedback.time_taken_seconds} seconds
                      </p>
                    </div>
                  </div>

                  {/* Proficiency Delta Badge */}
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                      {feedback.topic} Proficiency
                    </span>
                    <span className="text-sm font-bold text-slate-800">
                      {feedback.updated_proficiency.toFixed(1)}/100{' '}
                      <span
                        className={`text-xs ${
                          feedback.proficiency_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}
                      >
                        ({feedback.proficiency_delta >= 0 ? `+${feedback.proficiency_delta}` : feedback.proficiency_delta})
                      </span>
                    </span>
                  </div>
                </div>

                {/* Explanation Box */}
                <div className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-xs space-y-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
                    <BookOpen className="w-4 h-4 text-teal-600" />
                    <span>Explanation & Verification</span>
                  </div>
                  <p className="text-xs md:text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                    {feedback.explanation}
                  </p>
                </div>

                {/* 4-Factor Multi-Factor Decomposition Preview */}
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs space-y-2">
                  <span className="font-semibold text-slate-700 flex items-center gap-1 text-[11px]">
                    <Gauge className="w-3.5 h-3.5 text-teal-600" /> Multi-Factor Model Calibration:
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                    <div className="p-2 bg-white rounded border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Historical Acc (A)</span>
                      <span className="font-semibold text-slate-800">45% weight</span>
                    </div>
                    <div className="p-2 bg-white rounded border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Recent Trend (R)</span>
                      <span className="font-semibold text-slate-800">25% weight (W=5)</span>
                    </div>
                    <div className="p-2 bg-white rounded border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Difficulty Tier (D)</span>
                      <span className="font-semibold text-slate-800">20% weight</span>
                    </div>
                    <div className="p-2 bg-white rounded border border-slate-100">
                      <span className="text-slate-400 block text-[10px]">Speed Efficiency (E)</span>
                      <span className="font-semibold text-slate-800">10% weight</span>
                    </div>
                  </div>
                </div>

                {/* Next Question Recommendation Explanation */}
                {feedback.next_recommendation_reason && (
                  <div className="p-3.5 bg-teal-50 border border-teal-200/80 rounded-xl text-xs text-teal-900 flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-teal-800">Adaptive Engine Update: </span>
                      {feedback.next_recommendation_reason}
                    </div>
                  </div>
                )}

                {/* Continue button */}
                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleContinue}
                    className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs md:text-sm font-semibold transition shadow-sm flex items-center gap-2"
                  >
                    <span>Proceed to Next Recommendation</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          )}
        </div>
      ) : null}
    </div>
  );
};

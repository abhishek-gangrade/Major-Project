import React, { useState } from 'react';
import {
  User as UserIcon,
  Building,
  Briefcase,
  FlaskConical,
  Shield,
  Save,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { api } from '../services/api';
import { Card } from '../components/Card';
import { Badge } from '../components/Badge';

export const Settings: React.FC = () => {
  const { user } = useAuth();

  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [college, setCollege] = useState(user?.college || 'Medi-Caps University');
  const [targetRole, setTargetRole] = useState(user?.target_role || 'Software Development Engineer (SDE)');
  const [researchConsent, setResearchConsent] = useState(user?.research_consent ?? true);

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const updatedUser = await api.auth.updateProfile({
        display_name: displayName,
        college,
        target_role: targetRole,
        research_consent: researchConsent,
      });

      localStorage.setItem('adaptiveprep_user', JSON.stringify(updatedUser));
      setSuccessMsg('Your profile and learning preferences have been updated successfully.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update profile settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">Account & Platform Settings</h1>
          <Badge variant="teal" size="sm">
            {user?.role === 'admin' ? 'Faculty / Staff' : 'Student'}
          </Badge>
        </div>
        <p className="text-xs text-slate-500 mt-0.5">
          Manage your personal placement target, institutional affiliation, and research consent.
        </p>
      </div>

      {successMsg && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Profile Form */}
        <div className="md:col-span-2 space-y-6">
          <Card
            title="Learner Profile Information"
            subtitle="Details associated with your placement preparation account"
          >
            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
              <div>
                <label className="font-medium text-slate-700 block mb-1">Full Name</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                  />
                </div>
              </div>

              <div>
                <label className="font-medium text-slate-700 block mb-1">Email Address</label>
                <input
                  type="email"
                  disabled
                  value={user?.email || ''}
                  className="w-full px-3 py-2 border border-slate-200 bg-slate-50 rounded-lg text-xs text-slate-500 cursor-not-allowed"
                />
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Email address serves as your primary identifier and cannot be modified.
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-medium text-slate-700 block mb-1">Institution / College</label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={college}
                      onChange={(e) => setCollege(e.target.value)}
                      placeholder="e.g. Medi-Caps University"
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-medium text-slate-700 block mb-1">Target Placement Role</label>
                  <div className="relative">
                    <Briefcase className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={targetRole}
                      onChange={(e) => setTargetRole(e.target.value)}
                      placeholder="e.g. SDE, Cloud Engineer"
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-600"
                    />
                  </div>
                </div>
              </div>

              {/* Research Consent Box */}
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2 mt-4">
                <div className="flex items-start gap-2.5">
                  <input
                    type="checkbox"
                    id="consentCheckbox"
                    checked={researchConsent}
                    onChange={(e) => setResearchConsent(e.target.checked)}
                    className="mt-0.5 rounded text-teal-600 focus:ring-teal-500"
                  />
                  <label htmlFor="consentCheckbox" className="text-xs text-slate-700 leading-snug cursor-pointer">
                    <span className="font-semibold block text-slate-900">
                      Research Evaluation Protocol Consent (MEDICAPS-AP-2026.1)
                    </span>
                    Allow pseudonymized practice scores to contribute to statistical comparisons between adaptive,
                    accuracy-based, and random recommendation algorithms. Personal identifiers are never exported.
                  </label>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold transition shadow-sm flex items-center gap-1.5"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{saving ? 'Updating...' : 'Save Settings'}</span>
                </button>
              </div>
            </form>
          </Card>
        </div>

        {/* Right Column: Algorithm & Transparency Card */}
        <div className="space-y-6">
          <Card
            title="Algorithm Transparency"
            subtitle="Deterministic heuristic parameters"
          >
            <div className="space-y-3 text-xs text-slate-600">
              <div className="p-3 bg-teal-50/60 border border-teal-100 rounded-lg">
                <span className="font-semibold text-teal-900 block text-[11px] uppercase tracking-wider mb-1">
                  Proficiency Formula (S-Score)
                </span>
                <code className="text-teal-800 font-mono text-[11px] block">
                  S = 100 × (0.45A + 0.25R + 0.20D + 0.10E)
                </code>
              </div>

              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span>Historical Accuracy (A):</span>
                  <span className="font-semibold text-slate-800">45% weight</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span>Recent Performance (R):</span>
                  <span className="font-semibold text-slate-800">25% weight (W=5)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span>Difficulty Tier (D):</span>
                  <span className="font-semibold text-slate-800">20% weight</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span>Solving Efficiency (E):</span>
                  <span className="font-semibold text-slate-800">10% weight</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Difficulty Thresholds:
                </span>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <Badge variant="easy" size="sm">&lt; 40 Easy</Badge>
                  <Badge variant="medium" size="sm">40-69 Medium</Badge>
                  <Badge variant="hard" size="sm">&ge; 70 Hard</Badge>
                </div>
              </div>
            </div>
          </Card>

          <Card title="Account Metadata">
            <div className="space-y-2 text-xs text-slate-500">
              <div className="flex justify-between">
                <span>Account ID:</span>
                <span className="font-mono font-semibold text-slate-700">#{user?.id}</span>
              </div>
              <div className="flex justify-between">
                <span>User Role:</span>
                <Badge variant={user?.role === 'admin' ? 'teal' : 'neutral'} size="sm">
                  {user?.role}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span>Account Created:</span>
                <span className="text-slate-700">
                  {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Algorithm Version:</span>
                <span className="font-mono text-teal-700 font-semibold">v1.0.0-multi-factor</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

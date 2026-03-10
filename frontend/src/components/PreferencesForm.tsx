import React, { useState, useEffect } from 'react';
import { Plus, X, Save, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { savePreferences } from '../api/client';
import type { JobPreferences, JobPreferencesCreate } from '../types';

interface PreferencesFormProps {
  onSaved: (prefs: JobPreferences) => void;
  initialPrefs?: JobPreferences | null;
}

const EXPERIENCE_LEVELS = ['Entry', 'Mid', 'Senior', 'Lead', 'Architect'];
const JOB_TYPE_OPTIONS = ['Full-time', 'Contract', 'Part-time', 'Remote'];
const JOB_BOARD_OPTIONS = ['Google Jobs', 'Indeed', 'LinkedIn', 'JobStreet', 'MyCareersFuture', 'Glassdoor'];

const MultiInput: React.FC<{
  label: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}> = ({ label, placeholder, values, onChange }) => {
  const [input, setInput] = useState('');

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
      setInput('');
    }
  };

  const remove = (val: string) => onChange(values.filter(v => v !== val));

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={input}
          placeholder={placeholder}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), add())}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={add}
          className="bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={16} />
        </button>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {values.map(val => (
          <span key={val} className="inline-flex items-center gap-1 bg-blue-50 text-blue-700 text-xs px-2 py-1 rounded-full">
            {val}
            <button onClick={() => remove(val)} className="hover:text-red-500">
              <X size={12} />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
};

const PreferencesForm: React.FC<PreferencesFormProps> = ({ onSaved, initialPrefs }) => {
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState<JobPreferencesCreate>({
    target_titles: [],
    locations: [],
    experience_level: 'Mid',
    job_types: ['Full-time'],
    min_salary: '',
    industries: [],
    job_boards: ['Google Jobs'],
    excluded_companies: [],
  });

  useEffect(() => {
    if (initialPrefs) {
      setForm({
        target_titles: initialPrefs.target_titles,
        locations: initialPrefs.locations,
        experience_level: initialPrefs.experience_level,
        job_types: initialPrefs.job_types,
        min_salary: initialPrefs.min_salary || '',
        industries: initialPrefs.industries,
        job_boards: initialPrefs.job_boards,
        excluded_companies: initialPrefs.excluded_companies,
      });
    }
  }, [initialPrefs]);

  const toggleCheckbox = (field: 'job_types' | 'job_boards', value: string) => {
    setForm(prev => {
      const current = prev[field];
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value];
      return { ...prev, [field]: updated };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.target_titles.length === 0) {
      toast.error('Please add at least one target job title');
      return;
    }
    setIsSaving(true);
    try {
      const prefs = await savePreferences(form);
      toast.success('Preferences saved!');
      onSaved(prefs);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Job Preferences</h2>
        <p className="text-gray-500 mt-1">Configure what jobs to search for.</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
        {/* Target Titles */}
        <MultiInput
          label="Target Job Titles *"
          placeholder="e.g. Senior Java Developer"
          values={form.target_titles}
          onChange={v => setForm(prev => ({ ...prev, target_titles: v }))}
        />

        {/* Locations */}
        <MultiInput
          label="Preferred Locations"
          placeholder="e.g. Singapore, Remote"
          values={form.locations}
          onChange={v => setForm(prev => ({ ...prev, locations: v }))}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Experience Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Experience Level</label>
            <select
              value={form.experience_level}
              onChange={e => setForm(prev => ({ ...prev, experience_level: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {EXPERIENCE_LEVELS.map(lvl => (
                <option key={lvl} value={lvl}>{lvl}</option>
              ))}
            </select>
          </div>

          {/* Min Salary */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Salary (optional)</label>
            <input
              type="text"
              placeholder="e.g. $80,000 or SGD 8000/month"
              value={form.min_salary || ''}
              onChange={e => setForm(prev => ({ ...prev, min_salary: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Job Types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Types</label>
          <div className="flex flex-wrap gap-3">
            {JOB_TYPE_OPTIONS.map(type => (
              <label key={type} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.job_types.includes(type)}
                  onChange={() => toggleCheckbox('job_types', type)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm text-gray-700">{type}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Industries */}
        <MultiInput
          label="Target Industries"
          placeholder="e.g. Fintech, Healthcare"
          values={form.industries}
          onChange={v => setForm(prev => ({ ...prev, industries: v }))}
        />

        {/* Job Boards */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Job Boards to Search</label>
          <div className="flex flex-wrap gap-3">
            {JOB_BOARD_OPTIONS.map(board => (
              <label key={board} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.job_boards.includes(board)}
                  onChange={() => toggleCheckbox('job_boards', board)}
                  className="w-4 h-4 text-blue-600 rounded"
                />
                <span className="text-sm text-gray-700">{board}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Excluded Companies */}
        <MultiInput
          label="Excluded Companies (optional)"
          placeholder="e.g. Company to skip"
          values={form.excluded_companies}
          onChange={v => setForm(prev => ({ ...prev, excluded_companies: v }))}
        />
      </div>

      <button
        type="submit"
        disabled={isSaving}
        className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
      >
        {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
        Save Preferences
      </button>
    </form>
  );
};

export default PreferencesForm;

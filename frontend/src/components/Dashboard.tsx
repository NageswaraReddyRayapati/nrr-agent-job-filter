import React from 'react';
import { CheckCircle, Circle, ArrowRight } from 'lucide-react';
import type { Resume, JobPreferences, AppSettings, SetupStep } from '../types';

interface DashboardProps {
  resume?: Resume | null;
  preferences?: JobPreferences | null;
  settings?: AppSettings | null;
  onNavigate: (step: SetupStep) => void;
}

interface SetupItemProps {
  title: string;
  description: string;
  isComplete: boolean;
  action: string;
  onClick: () => void;
}

const SetupItem: React.FC<SetupItemProps> = ({ title, description, isComplete, action, onClick }) => (
  <div className={`flex items-center gap-4 p-4 rounded-xl border transition-colors
    ${isComplete ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-white hover:border-blue-300 cursor-pointer'}`}
    onClick={!isComplete ? onClick : undefined}
  >
    <div className="flex-shrink-0">
      {isComplete
        ? <CheckCircle className="text-green-500" size={24} />
        : <Circle className="text-gray-300" size={24} />
      }
    </div>
    <div className="flex-1">
      <p className="font-medium text-gray-900">{title}</p>
      <p className="text-sm text-gray-500">{description}</p>
    </div>
    {!isComplete && (
      <button onClick={onClick} className="flex items-center gap-1 text-blue-600 text-sm font-medium hover:text-blue-700">
        {action} <ArrowRight size={14} />
      </button>
    )}
  </div>
);

const Dashboard: React.FC<DashboardProps> = ({ resume, preferences, settings, onNavigate }) => {
  const hasSettings = settings?.openai_api_key_set || settings?.serpapi_key_set;
  const hasResume = !!resume;
  const hasPreferences = !!preferences;
  const isReady = hasResume && hasPreferences;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold">AI Job Search Agent</h1>
        <p className="mt-1 text-blue-100">
          Upload your resume, set preferences, and let AI find & tailor jobs for you automatically.
        </p>
      </div>

      {/* Setup Checklist */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">Setup Checklist</h2>
        <div className="space-y-2">
          <SetupItem
            title="Configure API Keys"
            description="Add your OpenAI and/or SerpAPI keys for full functionality"
            isComplete={!!hasSettings}
            action="Configure"
            onClick={() => onNavigate('settings')}
          />
          <SetupItem
            title="Upload Your Resume"
            description={resume ? `${resume.filename} — ${resume.skills.length} skills detected` : 'Upload your PDF, DOCX, or TXT resume'}
            isComplete={hasResume}
            action="Upload"
            onClick={() => onNavigate('resume')}
          />
          <SetupItem
            title="Set Job Preferences"
            description={
              preferences
                ? `Searching for: ${preferences.target_titles.join(', ') || 'any title'}`
                : 'Configure target job titles, locations, and more'
            }
            isComplete={hasPreferences}
            action="Configure"
            onClick={() => onNavigate('preferences')}
          />
        </div>
      </div>

      {/* Feature Overview */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-3">How It Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[
            {
              step: '1',
              title: 'Smart Job Search',
              desc: 'Searches Google Jobs and other boards for positions matching your skills and preferences',
              bgClass: 'bg-blue-500',
            },
            {
              step: '2',
              title: 'AI Matching & Scoring',
              desc: 'Scores each job based on skill overlap, experience relevance, and location match',
              bgClass: 'bg-purple-500',
            },
            {
              step: '3',
              title: 'Resume Tailoring',
              desc: 'Generates a custom-tailored resume for each job to maximize ATS score',
              bgClass: 'bg-green-500',
            },
          ].map(feature => (
            <div key={feature.step} className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm mb-3 ${feature.bgClass}`}>
                {feature.step}
              </div>
              <p className="font-semibold text-gray-900">{feature.title}</p>
              <p className="text-sm text-gray-500 mt-1">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      {isReady && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="font-medium text-blue-900">Ready to search!</p>
            <p className="text-sm text-blue-600">Your resume and preferences are configured.</p>
          </div>
          <button
            onClick={() => onNavigate('dashboard')}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Go to Job List <ArrowRight size={14} />
          </button>
        </div>
      )}
    </div>
  );
};

export default Dashboard;

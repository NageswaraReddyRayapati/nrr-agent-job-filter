import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import ResumeUpload from './components/ResumeUpload';
import PreferencesForm from './components/PreferencesForm';
import SettingsPanel from './components/SettingsPanel';
import JobList from './components/JobList';
import { getCurrentResume, getPreferences, getSettings } from './api/client';
import type { Resume, JobPreferences, AppSettings, SetupStep } from './types';

function App() {
  const [currentStep, setCurrentStep] = useState<SetupStep>('settings');
  const [resume, setResume] = useState<Resume | null>(null);
  const [preferences, setPreferences] = useState<JobPreferences | null>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      try {
        const [resumeData, prefsData, settingsData] = await Promise.allSettled([
          getCurrentResume(),
          getPreferences(),
          getSettings(),
        ]);

        if (resumeData.status === 'fulfilled') setResume(resumeData.value);
        if (prefsData.status === 'fulfilled') setPreferences(prefsData.value);
        if (settingsData.status === 'fulfilled') setSettings(settingsData.value);

        // Auto-navigate to the most logical step
        const hasResume = resumeData.status === 'fulfilled';
        const hasPrefs = prefsData.status === 'fulfilled';

        if (hasResume && hasPrefs) {
          setCurrentStep('dashboard');
        } else if (hasResume) {
          setCurrentStep('preferences');
        } else {
          setCurrentStep('settings');
        }
      } catch {
        // Start fresh
      } finally {
        setIsLoading(false);
      }
    };
    init();
  }, []);

  const isSetupComplete = !!resume && !!preferences;

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="text-gray-500 mt-3">Loading...</p>
        </div>
      </div>
    );
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'settings':
        return (
          <SettingsPanel
            onSaved={(s) => {
              setSettings(s);
              if (!resume) setCurrentStep('resume');
            }}
            currentSettings={settings}
          />
        );
      case 'resume':
        return (
          <ResumeUpload
            onUploaded={(r) => {
              setResume(r);
              if (!preferences) setCurrentStep('preferences');
              else setCurrentStep('dashboard');
            }}
            currentResume={resume}
          />
        );
      case 'preferences':
        return (
          <PreferencesForm
            onSaved={(p) => {
              setPreferences(p);
              setCurrentStep('dashboard');
            }}
            initialPrefs={preferences}
          />
        );
      case 'dashboard':
        return isSetupComplete ? (
          <JobList onSearchComplete={() => {}} />
        ) : (
          <Dashboard
            resume={resume}
            preferences={preferences}
            settings={settings}
            onNavigate={setCurrentStep}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { borderRadius: '10px', background: '#333', color: '#fff' },
        }}
      />
      <Header
        currentStep={currentStep}
        onNavigate={setCurrentStep}
        isSetupComplete={isSetupComplete}
      />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderStep()}
      </main>
    </div>
  );
}

export default App;

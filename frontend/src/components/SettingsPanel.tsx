import React, { useState } from 'react';
import { Save, Eye, EyeOff, TestTube, Loader2, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { saveSettings, testOpenAI, testSerpAPI } from '../api/client';
import type { AppSettings } from '../types';

interface SettingsPanelProps {
  onSaved: (settings: AppSettings) => void;
  currentSettings?: AppSettings | null;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ onSaved, currentSettings }) => {
  const [openaiKey, setOpenaiKey] = useState('');
  const [serpapiKey, setSerpapiKey] = useState('');
  const [showOpenai, setShowOpenai] = useState(false);
  const [showSerpapi, setShowSerpapi] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testingOpenai, setTestingOpenai] = useState(false);
  const [testingSerpapi, setTestingSerpapi] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!openaiKey && !serpapiKey) {
      toast.error('Enter at least one API key');
      return;
    }
    setIsSaving(true);
    try {
      const settings = await saveSettings({
        openai_api_key: openaiKey || undefined,
        serpapi_key: serpapiKey || undefined,
      });
      toast.success('Settings saved!');
      setOpenaiKey('');
      setSerpapiKey('');
      onSaved(settings);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestOpenAI = async () => {
    setTestingOpenai(true);
    try {
      const result = await testOpenAI();
      toast.success(result.message);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'OpenAI test failed');
    } finally {
      setTestingOpenai(false);
    }
  };

  const handleTestSerpAPI = async () => {
    setTestingSerpapi(true);
    try {
      const result = await testSerpAPI();
      toast.success(result.message);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'SerpAPI test failed');
    } finally {
      setTestingSerpapi(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-gray-500 mt-1">Configure your API keys. Keys are stored encrypted.</p>
      </div>

      {/* Current Status */}
      {currentSettings && (
        <div className="bg-blue-50 rounded-xl border border-blue-200 p-4">
          <h3 className="font-medium text-blue-900 mb-3">Current API Key Status</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="flex items-center gap-2">
              {currentSettings.openai_api_key_set
                ? <CheckCircle size={16} className="text-green-500" />
                : <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
              }
              <div>
                <p className="text-sm font-medium text-gray-700">OpenAI API Key</p>
                <p className="text-xs text-gray-500">
                  {currentSettings.openai_api_key_set
                    ? currentSettings.openai_api_key_masked || 'Set'
                    : 'Not configured'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {currentSettings.serpapi_key_set
                ? <CheckCircle size={16} className="text-green-500" />
                : <div className="w-4 h-4 rounded-full border-2 border-gray-300" />
              }
              <div>
                <p className="text-sm font-medium text-gray-700">SerpAPI Key</p>
                <p className="text-xs text-gray-500">
                  {currentSettings.serpapi_key_set
                    ? currentSettings.serpapi_key_masked || 'Set'
                    : 'Not configured'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm space-y-6">
        {/* OpenAI */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            OpenAI API Key
            <a
              href="https://platform.openai.com/api-keys"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-blue-500 text-xs hover:underline"
            >
              Get key →
            </a>
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type={showOpenai ? 'text' : 'password'}
                value={openaiKey}
                onChange={e => setOpenaiKey(e.target.value)}
                placeholder={currentSettings?.openai_api_key_set ? '••••••••• (leave blank to keep current)' : 'sk-...'}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowOpenai(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showOpenai ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <button
              type="button"
              onClick={handleTestOpenAI}
              disabled={testingOpenai || !currentSettings?.openai_api_key_set}
              className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testingOpenai ? <Loader2 size={14} className="animate-spin" /> : <TestTube size={14} />}
              Test
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">Used for resume parsing, job matching, and tailoring</p>
        </div>

        {/* SerpAPI */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            SerpAPI Key
            <a
              href="https://serpapi.com/manage-api-key"
              target="_blank"
              rel="noopener noreferrer"
              className="ml-2 text-blue-500 text-xs hover:underline"
            >
              Get key →
            </a>
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type={showSerpapi ? 'text' : 'password'}
                value={serpapiKey}
                onChange={e => setSerpapiKey(e.target.value)}
                placeholder={currentSettings?.serpapi_key_set ? '••••••••• (leave blank to keep current)' : 'Enter SerpAPI key...'}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => setShowSerpapi(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showSerpapi ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <button
              type="button"
              onClick={handleTestSerpAPI}
              disabled={testingSerpapi || !currentSettings?.serpapi_key_set}
              className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {testingSerpapi ? <Loader2 size={14} className="animate-spin" /> : <TestTube size={14} />}
              Test
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-1">Used for Google Jobs search. Without this key, mock results are shown.</p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-xs text-yellow-800">
          <strong>Note:</strong> You can also set keys via the <code>.env</code> file
          (OPENAI_API_KEY, SERPAPI_KEY). Keys set via UI take precedence.
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
        >
          {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          Save API Keys
        </button>
      </form>
    </div>
  );
};

export default SettingsPanel;

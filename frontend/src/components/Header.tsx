import React from 'react';
import { BotMessageSquare, Settings, LayoutDashboard, Upload, ListFilter } from 'lucide-react';
import type { SetupStep } from '../types';

interface HeaderProps {
  currentStep: SetupStep;
  onNavigate: (step: SetupStep) => void;
  isSetupComplete: boolean;
}

const steps: { key: SetupStep; label: string; icon: React.ReactNode }[] = [
  { key: 'settings', label: 'Settings', icon: <Settings size={16} /> },
  { key: 'resume', label: 'Resume', icon: <Upload size={16} /> },
  { key: 'preferences', label: 'Preferences', icon: <ListFilter size={16} /> },
  { key: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard size={16} /> },
];

const Header: React.FC<HeaderProps> = ({ currentStep, onNavigate, isSetupComplete }) => {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <BotMessageSquare className="text-blue-600" size={28} />
            <span className="font-bold text-gray-900 text-lg">AI Job Agent</span>
          </div>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {steps.map((step, idx) => {
              const isActive = currentStep === step.key;
              const isEnabled = isSetupComplete || idx === 0 || step.key === 'dashboard' ? true : idx <= steps.findIndex(s => s.key === currentStep) + 1;
              return (
                <button
                  key={step.key}
                  onClick={() => isEnabled && onNavigate(step.key)}
                  disabled={!isEnabled}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                    ${isActive
                      ? 'bg-blue-600 text-white'
                      : isEnabled
                        ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                        : 'text-gray-300 cursor-not-allowed'
                    }`}
                >
                  {step.icon}
                  {step.label}
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;

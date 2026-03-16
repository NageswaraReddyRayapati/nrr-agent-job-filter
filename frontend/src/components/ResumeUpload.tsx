import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadResume } from '../api/client';
import type { Resume } from '../types';

interface ResumeUploadProps {
  onUploaded: (resume: Resume) => void;
  currentResume?: Resume | null;
}

const ResumeUpload: React.FC<ResumeUploadProps> = ({ onUploaded, currentResume }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFile = async (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext || '')) {
      toast.error('Please upload a PDF, DOCX, or TXT file');
      return;
    }

    setIsUploading(true);
    try {
      const resume = await uploadResume(file);
      toast.success('Resume uploaded and parsed successfully!');
      onUploaded(resume);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || 'Upload failed';
      toast.error(detail);
    } finally {
      setIsUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Upload Your Resume</h2>
        <p className="text-gray-500 mt-1">Upload a PDF, DOCX, or TXT file. We'll parse it automatically.</p>
      </div>

      {/* Upload Zone */}
      <label
        className={`block border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}
          ${isUploading ? 'pointer-events-none opacity-70' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
      >
        <input type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={onChange} disabled={isUploading} />
        {isUploading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="animate-spin text-blue-500" size={40} />
            <p className="text-blue-600 font-medium">Uploading and parsing...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="text-gray-400" size={40} />
            <p className="text-gray-700 font-medium">Drag & drop your resume here</p>
            <p className="text-gray-400 text-sm">or click to browse</p>
            <p className="text-gray-400 text-xs">Supported: PDF, DOCX, TXT (max 10 MB)</p>
          </div>
        )}
      </label>

      {/* Parsed Resume Display */}
      {currentResume && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="text-green-500" size={20} />
            <h3 className="font-semibold text-gray-900">Parsed Resume</h3>
            <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Active</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-500">File</p>
              <p className="font-medium flex items-center gap-1">
                <FileText size={14} className="text-blue-500" />
                {currentResume.filename}
              </p>
            </div>
            {currentResume.full_name && (
              <div>
                <p className="text-sm text-gray-500">Name</p>
                <p className="font-medium">{currentResume.full_name}</p>
              </div>
            )}
            {currentResume.email && (
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="font-medium">{currentResume.email}</p>
              </div>
            )}
            {currentResume.phone && (
              <div>
                <p className="text-sm text-gray-500">Phone</p>
                <p className="font-medium">{currentResume.phone}</p>
              </div>
            )}
          </div>

          {currentResume.skills.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-2">Detected Skills</p>
              <div className="flex flex-wrap gap-1.5">
                {currentResume.skills.map((skill) => (
                  <span key={skill} className="bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {currentResume.experience_summary && (
            <div className="mt-4">
              <p className="text-sm text-gray-500 mb-1">Experience Summary</p>
              <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3">
                {currentResume.experience_summary.slice(0, 400)}
                {currentResume.experience_summary.length > 400 ? '...' : ''}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ResumeUpload;

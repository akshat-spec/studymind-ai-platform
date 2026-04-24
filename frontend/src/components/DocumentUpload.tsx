import React, { useState, useRef } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  withCredentials: true,
});

export const DocumentUpload: React.FC<{ onUploadComplete: () => void }> = ({ onUploadComplete }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [docDetails, setDocDetails] = useState<{ id: string, pages: number, size: number } | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const token = useAuthStore(state => state.accessToken);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
      } else {
        setErrorMessage('Only PDF files are allowed');
      }
    }
  };

  const startUpload = async () => {
    if (!file) return;
    
    setStatus('uploading');
    setErrorMessage('');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await api.post('/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
          setProgress(percentCompleted);
        }
      });
      
      const docId = res.data.id;
      setStatus('processing');
      pollStatus(docId);
      
    } catch (err: any) {
      setStatus('error');
      setErrorMessage(err.response?.data?.detail || 'Upload failed');
    }
  };

  const pollStatus = async (docId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/documents/${docId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.data.status === 'ready') {
          clearInterval(interval);
          setStatus('ready');
          setDocDetails({
            id: res.data.id,
            pages: res.data.page_count,
            size: res.data.file_size
          });
          onUploadComplete();
        } else if (res.data.status === 'failed') {
          clearInterval(interval);
          setStatus('error');
          setErrorMessage('Processing failed');
        }
      } catch (e) {
        clearInterval(interval);
        setStatus('error');
        setErrorMessage('Failed to check status');
      }
    }, 3000);
  };

  return (
    <div className="w-full">
      <div 
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging ? 'border-emerald-500 bg-emerald-50' : 'border-slate-300 bg-white hover:border-emerald-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {!file && status === 'idle' && (
          <div className="flex flex-col items-center justify-center space-y-4 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
            <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center">
               <span className="text-3xl text-slate-400">📄</span>
            </div>
            <div>
              <p className="text-lg font-medium text-slate-700">Click to upload or drag and drop</p>
              <p className="text-sm text-slate-500 mt-1">PDF up to 50MB</p>
            </div>
            <input 
              type="file" 
              className="hidden" 
              ref={fileInputRef} 
              accept=".pdf" 
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setFile(e.target.files[0]);
                }
              }} 
            />
          </div>
        )}

        {file && status === 'idle' && (
          <div className="flex flex-col items-center space-y-4">
            <span className="text-4xl">📎</span>
            <p className="text-md font-medium text-slate-800">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            <div className="flex space-x-4">
              <button 
                onClick={() => setFile(null)} 
                className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={startUpload} 
                className="px-4 py-2 text-sm text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors"
              >
                Upload File
              </button>
            </div>
          </div>
        )}

        {(status === 'uploading' || status === 'processing') && (
          <div className="flex flex-col items-center space-y-4 w-full max-w-xs mx-auto">
             <span className="text-emerald-500 animate-pulse text-4xl">⚙️</span>
             <p className="text-sm font-medium text-slate-700">
               {status === 'uploading' ? `Uploading... ${progress}%` : 'Evaluating Document AI Patterns...'}
             </p>
             <div className="w-full bg-slate-200 rounded-full h-2.5">
               <div 
                 className={`bg-emerald-600 h-2.5 rounded-full transition-all duration-500 ${status==='processing' ? 'w-full animate-pulse' : ''}`} 
                 style={{ width: status === 'uploading' ? `${progress}%` : '100%' }}
               ></div>
             </div>
          </div>
        )}

        {status === 'ready' && docDetails && (
          <div className="flex flex-col items-center space-y-4 w-full">
            <div className="h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center">
               <span className="text-3xl">✅</span>
            </div>
            <div className="text-center">
              <h3 className="text-lg font-bold text-slate-800">Processing Complete!</h3>
              <p className="text-sm text-slate-600 mt-1">{file?.name}</p>
              <div className="flex justify-center space-x-4 mt-3">
                <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded">Pages: {docDetails.pages}</span>
                <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded">{(docDetails.size/1024/1024).toFixed(2)} MB</span>
              </div>
            </div>
            <button 
                onClick={() => { setFile(null); setStatus('idle'); }} 
                className="mt-4 px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Upload Another
            </button>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center space-y-4">
            <span className="text-4xl">❌</span>
            <p className="text-red-500 text-sm">{errorMessage}</p>
            <button 
                onClick={() => { setFile(null); setStatus('idle'); setErrorMessage(''); }} 
                className="px-4 py-2 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

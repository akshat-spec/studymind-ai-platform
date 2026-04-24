import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { DocumentUpload } from '../components/DocumentUpload';
import { UsageBanner } from '../components/UsageBanner';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  withCredentials: true,
});

interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: string;
  created_at: string;
}

export const DocumentsPage: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const token = useAuthStore(state => state.accessToken);

  const fetchDocuments = async () => {
    try {
      const res = await api.get('/documents/', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDocuments(res.data);
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [token]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document? All associated chats and flashcards will be removed.')) return;
    
    try {
      await api.delete(`/documents/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchDocuments();
    } catch (e) {
      console.error("Failed to delete document", e);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-end mb-8">
        <h1 className="text-3xl font-bold text-slate-900">My Documents</h1>
      </div>
      
      <div className="mb-8">
         <UsageBanner />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-8">
        <DocumentUpload onUploadComplete={fetchDocuments} />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full py-12 text-center text-slate-500">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="col-span-full py-12 text-center text-slate-500 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200">
            No documents uploaded yet. Add your first PDF above!
          </div>
        ) : (
          documents.map(doc => (
            <div 
              key={doc.id} 
              className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-300 transition-all cursor-pointer flex flex-col relative group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="h-10 w-10 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600">
                   📄
                </div>
                <div className="flex flex-col items-end">
                   <button 
                     onClick={(e) => handleDelete(doc.id, e)} 
                     className="text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity mb-2"
                   >
                     <span className="text-lg">🗑️</span>
                   </button>
                   <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                     doc.status === 'ready' ? 'bg-emerald-100 text-emerald-700' :
                     doc.status === 'processing' ? 'bg-amber-100 text-amber-700 animate-pulse' :
                     'bg-red-100 text-red-700'
                   }`}>
                     {doc.status.charAt(0).toUpperCase() + doc.status.slice(1)}
                   </span>
                </div>
              </div>
              
              <h3 className="text-lg font-semibold text-slate-800 line-clamp-2" title={doc.title}>
                {doc.title}
              </h3>
              
              <div className="mt-auto pt-4 flex items-center justify-between text-sm text-slate-500">
                <div className="flex flex-col">
                  <span>{(doc.file_size / 1024 / 1024).toFixed(2)} MB</span>
                  <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                </div>
                {doc.status === 'ready' && (
                  <span className="bg-slate-100 px-2 py-1 rounded text-xs font-medium text-slate-600">
                    {doc.page_count} Pages
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

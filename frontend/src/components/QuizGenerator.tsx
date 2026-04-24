import React, { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
});

interface Props {
  documentId: string;
  onClose?: () => void;
}

export const QuizGenerator: React.FC<Props> = ({ documentId, onClose }) => {
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState('medium');
  const [topic, setTopic] = useState('');
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const token = useAuthStore(state => state.accessToken);
  const navigate = useNavigate();

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    try {
      const res = await api.post(
        '/quiz/generate',
        {
          document_id: documentId,
          num_questions: numQuestions,
          difficulty,
          topic_focus: topic || null
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const quizId = res.data.quiz_id;
      navigate(`/quiz/${quizId}`);
      if (onClose) onClose();
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate quiz. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-lg border border-slate-200">
      <h3 className="text-xl font-bold text-slate-800 mb-2">Generate Assessment</h3>
      <p className="text-slate-500 text-sm mb-6">Customize the parameters to test your knowledge exactly how you want.</p>
      
      <form onSubmit={handleGenerate} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Number of Questions</label>
          <div className="flex bg-slate-100 p-1 rounded-lg">
            {[5, 10, 20].map(num => (
              <button
                key={num}
                type="button"
                onClick={() => setNumQuestions(num)}
                className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  numQuestions === num ? 'bg-white shadow-sm text-emerald-600' : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Difficulty Level</label>
          <select 
            value={difficulty} 
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full rounded-lg border-slate-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 px-3 py-2 text-sm"
          >
            <option value="easy">Easy (Definitions & Facts)</option>
            <option value="medium">Medium (Comprehension & Concepts)</option>
            <option value="hard">Hard (Analysis & Application)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Specific Topic Focus (Optional)</label>
          <input 
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Mitochondria, Supply Chain..."
            className="w-full rounded-lg border-slate-300 shadow-sm focus:border-emerald-500 focus:ring-emerald-500 bg-slate-50 px-3 py-2 text-sm"
          />
        </div>

        {error && <div className="text-red-500 text-sm">{error}</div>}

        <div className="pt-2">
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-medium py-2.5 rounded-lg transition-colors flex justify-center items-center"
            >
              {isLoading ? (
                 <>
                    <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin mr-2"></span>
                    Generating AI Quiz...
                 </>
              ) : (
                 'Create Quiz'
              )}
            </button>
        </div>
      </form>
    </div>
  );
};

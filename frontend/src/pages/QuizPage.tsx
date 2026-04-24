import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
});



export const QuizPage: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>();
  const navigate = useNavigate();
  const token = useAuthStore(state => state.accessToken);
  
  const [quizData, setQuizData] = useState<any>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);

  useEffect(() => {
    const loadQuiz = async () => {
      try {
        const res = await api.get(`/quiz/${quizId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setQuizData(res.data);
      } catch (err) {
        console.error('Failed to load quiz', err);
      }
    };
    if (quizId) loadQuiz();
  }, [quizId, token]);

  const handleSelect = (questionId: number, option: string) => {
      setAnswers(prev => ({ ...prev, [questionId]: option }));
  };

  const handleNext = () => {
      if (currentIndex < quizData.questions.length - 1) {
          setCurrentIndex(prev => prev + 1);
      }
  };

  const handlePrev = () => {
      if (currentIndex > 0) {
          setCurrentIndex(prev => prev - 1);
      }
  };

  const handleSubmit = async () => {
      setIsSubmitting(true);
      const payload = Object.entries(answers).map(([qid, sel]) => ({
          question_id: parseInt(qid),
          selected: sel
      }));

      try {
          const res = await api.post(`/quiz/${quizId}/submit`, { answers: payload }, {
              headers: { Authorization: `Bearer ${token}` }
          });
          setResults(res.data);
      } catch (err) {
          console.error('Failed to submit', err);
      } finally {
          setIsSubmitting(false);
      }
  };

  if (!quizData) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="animate-pulse text-slate-500">Loading quiz...</div></div>;

  // View: Results
  if (results) {
      return (
          <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
              <div className="max-w-3xl mx-auto">
                  <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-8">
                      <div className="bg-slate-900 p-8 text-center">
                          <h2 className="text-3xl font-bold text-white mb-2">Quiz Results</h2>
                          <div className="inline-flex items-center justify-center w-32 h-32 rounded-full border-4 border-emerald-500/30 mb-4 mt-6">
                              <span className="text-4xl font-bold text-emerald-400">{results.score} / {results.total}</span>
                          </div>
                      </div>
                      
                      <div className="p-8 space-y-8">
                          {results.feedback.map((f: any, idx: number) => {
                              const q = quizData.questions.find((q: any) => q.id === f.id);
                              return (
                                  <div key={f.id} className={`p-6 rounded-xl border ${f.is_correct ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'}`}>
                                      <div className="flex gap-3 items-start mb-4">
                                          <span className="text-2xl">{f.is_correct ? '✅' : '❌'}</span>
                                          <div>
                                              <p className="font-medium text-slate-800 text-lg mb-1">{idx + 1}. {q?.question}</p>
                                              <p className="text-sm text-slate-500">Your answer: <span className="font-semibold text-slate-700">{f.selected_option || 'Skipped'}</span></p>
                                              {!f.is_correct && (
                                                  <p className="text-sm text-slate-500">Correct answer: <span className="font-semibold text-emerald-600">{f.correct_option}</span></p>
                                              )}
                                          </div>
                                      </div>
                                      <div className="bg-white/60 p-4 rounded-lg text-sm text-slate-600 border border-white">
                                          <span className="font-semibold text-slate-700">Explanation:</span> {f.explanation}
                                          {f.page_ref && <span className="ml-2 inline-block px-2 py-0.5 bg-slate-200 rounded text-xs">Page {f.page_ref}</span>}
                                      </div>
                                  </div>
                              );
                          })}
                      </div>
                      <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-center">
                          <button onClick={() => navigate('/')} className="px-6 py-2.5 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition">Return to Dashboard</button>
                      </div>
                  </div>
              </div>
          </div>
      );
  }

  // View: Questions
  const currentQ = quizData.questions[currentIndex];
  const answeredCount = Object.keys(answers).length;
  const progress = (answeredCount / quizData.questions.length) * 100;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl w-full mx-auto flex-1 flex flex-col">
            
            {/* Header / Progress */}
            <div className="mb-8 pl-1">
                <button onClick={() => navigate('/')} className="text-sm text-slate-500 hover:text-slate-700 mb-4 transition font-medium">← Back</button>
                <h1 className="text-2xl font-bold text-slate-800 mb-4">{quizData.title}</h1>
                <div className="flex items-center justify-between text-sm font-medium text-slate-500 mb-2">
                    <span>Question {currentIndex + 1} of {quizData.questions.length}</span>
                    <span className="text-emerald-600">{Math.round(progress)}% Completed</span>
                </div>
                <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 transition-all duration-300" style={{ width: `${progress}%` }}></div>
                </div>
            </div>

            {/* Question Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow p-8 flex-1">
                <h2 className="text-xl text-slate-800 font-medium leading-relaxed mb-8">{currentQ.question}</h2>
                <div className="space-y-3">
                    {currentQ.options.map((opt: string, i: number) => {
                        const isSelected = answers[currentQ.id] === opt;
                        const letters = ['A', 'B', 'C', 'D', 'E'];
                        return (
                            <div 
                                key={i}
                                onClick={() => handleSelect(currentQ.id, opt)}
                                className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex items-center group ${
                                    isSelected 
                                    ? 'border-emerald-500 bg-emerald-50' 
                                    : 'border-slate-100 hover:border-emerald-200 hover:bg-slate-50'
                                }`}
                            >
                                <span className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center mr-4 font-bold text-sm transition-colors ${
                                    isSelected ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-emerald-100'
                                }`}>
                                    {letters[i]}
                                </span>
                                <span className={`${isSelected ? 'text-emerald-900 font-medium' : 'text-slate-700'}`}>{opt}</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Controls */}
            <div className="mt-8 flex justify-between items-center text-sm font-medium">
                <button 
                  onClick={handlePrev}
                  disabled={currentIndex === 0}
                  className="px-6 py-2.5 rounded-lg border border-slate-200 text-slate-600 disabled:opacity-50 hover:bg-white transition"
                >
                    Previous
                </button>
                
                {currentIndex === quizData.questions.length - 1 ? (
                    <button 
                      onClick={handleSubmit}
                      disabled={isSubmitting || answeredCount < quizData.questions.length}
                      className="px-8 py-2.5 rounded-lg bg-emerald-600 text-white disabled:opacity-50 hover:bg-emerald-700 transition shadow-sm hover:shadow"
                    >
                        {isSubmitting ? 'Submitting...' : 'Submit Answers'}
                    </button>
                ) : (
                    <button 
                      onClick={handleNext}
                      className="px-8 py-2.5 rounded-lg bg-slate-800 text-white hover:bg-slate-900 transition shadow-sm hover:shadow"
                    >
                        Next
                    </button>
                )}
            </div>
            
        </div>
    </div>
  );
};

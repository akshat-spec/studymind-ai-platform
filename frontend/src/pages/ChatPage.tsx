import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';
import { MessageBubble } from '../components/MessageBubble';
import { QuizGenerator } from '../components/QuizGenerator';
import { useChat } from '../hooks/useChat';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  withCredentials: true,
});

export const ChatPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const token = useAuthStore(state => state.accessToken);
  const { messages, isLoading, sendMessage, fetchHistory, stopGeneration } = useChat(sessionId || '');
  
  const [sessions, setSessions] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [docPanelOpen, setDocPanelOpen] = useState(true);
  const [activeGenerator, setActiveGenerator] = useState<'none'|'quiz'|'flashcards'>('none');
  const [isGeneratingCards, setIsGeneratingCards] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load History
  useEffect(() => {
    if (sessionId) fetchHistory();
  }, [sessionId, fetchHistory]);
  
  // Load sidebar sessions
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await api.get('/chat/sessions', { headers: { Authorization: `Bearer ${token}` }});
        setSessions(res.data);
      } catch (e) {
        console.error("Failed fetching sessions");
      }
    };
    fetchSessions();
  }, [token, messages.length]); // Refresh on new messages incase title changed

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const currentSession = sessions.find(s => s.id === sessionId);

  const handleGenerateFlashcards = async () => {
    if (!currentSession?.document_id) return;
    setIsGeneratingCards(true);
    try {
      await api.post('/flashcards/generate', 
        { document_id: currentSession.document_id, num_cards: 20 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      navigate('/flashcards');
    } catch (e) {
      console.error("Failed to generate flashcards", e);
      alert("Failed to generate flashcards");
    } finally {
      setIsGeneratingCards(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar: Sessions */}
      <div className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0">
        <div className="p-4 border-b border-slate-800">
          <button 
            onClick={() => navigate('/')}
            className="text-white font-bold text-xl hover:text-emerald-400 transition-colors"
          >
            ← StudyMind AI
          </button>
        </div>
        <div className="overflow-y-auto flex-1 p-3 space-y-2">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-2">Your Chats</div>
          {sessions.map(s => (
            <div 
              key={s.id} 
              onClick={() => navigate(`/chat/${s.id}`)}
              className={`px-3 py-2.5 rounded-lg text-sm cursor-pointer truncate transition-colors ${
                s.id === sessionId ? 'bg-emerald-600 text-white' : 'hover:bg-slate-800'
              }`}
            >
              💬 {s.title || 'New Chat'}
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Panel */}
      <div className="flex-1 flex flex-col relative transition-all duration-300">
        <div className="absolute top-0 left-0 right-0 h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 z-10 flex items-center px-6 justify-between">
            <h2 className="text-lg font-semibold text-slate-800">
               {sessions.find(s => s.id === sessionId)?.title || 'AI Study Session'}
            </h2>
            <button 
              onClick={() => setDocPanelOpen(!docPanelOpen)}
              className="text-slate-500 hover:text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            >
              {docPanelOpen ? 'Hide Context' : 'Show Context'}
            </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 pt-24 pb-32">
          {messages.length === 0 ? (
             <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                 <div className="h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center text-3xl">🤖</div>
                 <h3 className="text-xl font-medium text-slate-700">How can I help you study?</h3>
                 <p className="text-sm max-w-sm text-center">Ask me questions about your document, or request practice quizzes and flashcards!</p>
             </div>
          ) : (
            <div className="max-w-4xl mx-auto flex flex-col space-y-4">
              {messages.map(msg => (
                <MessageBubble 
                  key={msg.id} 
                  role={msg.role} 
                  content={msg.content} 
                  isStreaming={isLoading && msg.id === messages[messages.length-1].id && msg.role === 'assistant'} 
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto relative">
                <form onSubmit={handleSubmit} className="relative flex items-end shadow-lg rounded-xl bg-white border border-slate-200 overflow-hidden">
                    <textarea 
                      ref={inputRef}
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask a question about the document... (Shift+Enter for newline)"
                      className="w-full max-h-48 min-h-[60px] py-4 pl-4 pr-14 resize-none focus:outline-none focus:ring-0 text-slate-700 bg-transparent"
                      rows={1}
                    />
                    {isLoading ? (
                        <button 
                            type="button"
                            onClick={stopGeneration}
                            className="absolute right-3 bottom-3 h-9 w-9 bg-red-100 hover:bg-red-200 text-red-600 rounded-lg flex items-center justify-center transition-colors"
                        >
                            ⏹
                        </button>
                    ) : (
                        <button 
                            type="submit"
                            disabled={!input.trim()}
                            className="absolute right-3 bottom-3 h-9 w-9 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg flex items-center justify-center transition-colors"
                        >
                            ↑
                        </button>
                    )}
                </form>
                <div className="text-center mt-2 text-xs text-slate-400">
                    AI can make mistakes. Check your document for critical facts.
                </div>
            </div>
        </div>
      </div>

      {/* Document Panel (Right) */}
      <div className={`bg-white border-l border-slate-200 transition-all duration-300 ease-in-out ${docPanelOpen ? 'w-80 opacity-100 block' : 'w-0 opacity-0 hidden'} flex-shrink-0 flex flex-col`}>
          <div className="h-16 border-b border-slate-200 flex items-center px-4 shrink-0">
             <h3 className="font-semibold text-slate-700 flex items-center space-x-2">
                 <span>📄</span>
                 <span>Document Context</span>
             </h3>
          </div>
          <div className="flex-1 p-4 overflow-y-auto">
             <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-sm text-slate-600 italic">
                 The document preview panel will display the relevant PDF pages here if a viewer is integrated, or contextual meta-data regarding the current active reference.
             </div>
             
             <div className="mt-6 space-y-4">
                 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Features</h4>
                 
                 {activeGenerator === 'none' && (
                   <>
                     <button 
                        onClick={() => setActiveGenerator('quiz')}
                        className="w-full text-left px-3 py-2 text-sm text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors flex items-center"
                     >
                        <span className="mr-2">📝</span> Generate Quiz
                     </button>
                     <button 
                        onClick={handleGenerateFlashcards}
                        disabled={isGeneratingCards}
                        className="w-full text-left px-3 py-2 text-sm text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors flex items-center disabled:opacity-50"
                     >
                        <span className="mr-2">🗂️</span> {isGeneratingCards ? 'Generating...' : 'Create Flashcards'}
                     </button>
                   </>
                 )}

                 {activeGenerator === 'quiz' && currentSession?.document_id && (
                    <div className="pt-2">
                       <button onClick={() => setActiveGenerator('none')} className="text-xs text-slate-500 hover:text-slate-700 mb-2 font-medium">← Back to features</button>
                       <QuizGenerator documentId={currentSession.document_id} onClose={() => setActiveGenerator('none')} />
                    </div>
                 )}
             </div>
          </div>
      </div>
    </div>
  );
};

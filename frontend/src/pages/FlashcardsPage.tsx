import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
});

// A pure CSS 3D transform animation for card flipping
export const FlashcardsPage: React.FC = () => {
    const navigate = useNavigate();
    const token = useAuthStore(state => state.accessToken);
    
    const [cards, setCards] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [cardsRes, statsRes] = await Promise.all([
                    api.get('/flashcards/due', { headers: { Authorization: `Bearer ${token}` } }),
                    api.get('/flashcards/stats', { headers: { Authorization: `Bearer ${token}` } })
                ]);
                setCards(cardsRes.data);
                setStats(statsRes.data);
            } catch (err) {
                console.error('Failed to load flashcards', err);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [token]);

    const handleRating = async (rating: number) => {
        const cardId = cards[currentIndex].id;
        // Optimistic UI advance
        setIsFlipped(false);
        setTimeout(() => setCurrentIndex(prev => prev + 1), 150); // slight delay for flip reset
        
        try {
            await api.post(`/flashcards/${cardId}/review`, { rating }, {
                headers: { Authorization: `Bearer ${token}` }
            });
        } catch (e) {
            console.error("Failed recording rating", e);
        }
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="animate-pulse">Loading deck...</div></div>;

    if (currentIndex >= cards.length || cards.length === 0) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-6">
                <div className="bg-white p-10 rounded-3xl shadow-xl border border-slate-100 max-w-md w-full text-center">
                    <div className="text-6xl mb-6 text-emerald-500">🎉</div>
                    <h2 className="text-2xl font-bold text-slate-800 mb-2">You're all caught up!</h2>
                    <p className="text-slate-500 mb-8 leading-relaxed">You've completed all your due reviews for today. Great job keeping your memory sharp.</p>
                    
                    <div className="bg-slate-50 p-4 rounded-xl mb-8 flex justify-around text-center">
                        <div>
                            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Mastered</div>
                            <div className="text-xl font-bold text-slate-700">{stats?.mastered || 0}</div>
                        </div>
                        <div className="w-px bg-slate-200"></div>
                        <div>
                            <div className="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1">Total Cards</div>
                            <div className="text-xl font-bold text-slate-700">{stats?.total || 0}</div>
                        </div>
                    </div>

                    <button 
                        onClick={() => navigate('/')} 
                        className="w-full py-3 px-4 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-xl transition"
                    >
                        Return to Dashboard
                    </button>
                </div>
            </div>
        );
    }

    const currentCard = cards[currentIndex];
    
    return (
        <div className="min-h-screen bg-slate-50 flex flex-col py-8 px-4 sm:px-6 lg:px-8">
            <div className="max-w-xl w-full mx-auto flex-1 flex flex-col">
                <div className="flex justify-between items-center mb-8">
                    <button onClick={() => navigate('/')} className="text-slate-500 hover:text-slate-800 font-medium transition text-sm">← Exit Review</button>
                    <div className="text-sm font-bold text-slate-400 bg-white border border-slate-200 px-3 py-1 rounded-full">{currentIndex + 1} / {cards.length} Due</div>
                </div>

                <div 
                    onClick={() => setIsFlipped(!isFlipped)}
                    className="flex-1 relative cursor-pointer group perspective-1000 mb-8 min-h-[400px]"
                >
                    <div className={`w-full h-full absolute transition-all duration-500 transform-style-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
                        
                        {/* Front of card */}
                        <div className="absolute w-full h-full backface-hidden bg-white rounded-3xl shadow-lg border border-slate-200 p-8 sm:p-12 flex items-center justify-center text-center">
                            <div>
                                <span className="text-xs font-bold text-blue-500 uppercase tracking-widest mb-4 block">Question</span>
                                <h3 className="text-2xl sm:text-3xl font-medium text-slate-800 leading-tight">{currentCard.front}</h3>
                                <p className="text-sm text-slate-400 mt-12 animate-pulse font-medium">Click card to reveal answer</p>
                            </div>
                        </div>
                        
                        {/* Back of card */}
                        <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-white rounded-3xl shadow-lg border-2 border-emerald-100 p-8 sm:p-12 flex items-center justify-center text-center">
                             <div>
                                <span className="text-xs font-bold text-emerald-500 uppercase tracking-widest mb-4 block">Answer</span>
                                <p className="text-xl sm:text-2xl text-slate-700 leading-relaxed">{currentCard.back}</p>
                            </div>
                        </div>

                    </div>
                </div>

                {/* Rating Controls - Only visible when flipped */}
                <div className={`transition-all duration-300 ${isFlipped ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}>
                   <p className="text-center text-sm font-medium text-slate-500 mb-4">How well did you know this?</p>
                   <div className="grid grid-cols-4 gap-3 text-sm font-medium">
                       <button onClick={(e) => { e.stopPropagation(); handleRating(1); }} className="py-3 rounded-xl bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition">
                           Again<br/><span className="text-xs font-normal opacity-70">1m</span>
                       </button>
                       <button onClick={(e) => { e.stopPropagation(); handleRating(3); }} className="py-3 rounded-xl bg-orange-50 text-orange-700 border border-orange-200 hover:bg-orange-100 transition">
                           Hard<br/><span className="text-xs font-normal opacity-70">1d</span>
                       </button>
                       <button onClick={(e) => { e.stopPropagation(); handleRating(4); }} className="py-3 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition shrink-0">
                           Good<br/><span className="text-xs font-normal opacity-70">3d</span>
                       </button>
                       <button onClick={(e) => { e.stopPropagation(); handleRating(5); }} className="py-3 rounded-xl bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition shrink-0">
                           Easy<br/><span className="text-xs font-normal opacity-70">5d</span>
                       </button>
                   </div>
                </div>

            </div>
        </div>
    );
};

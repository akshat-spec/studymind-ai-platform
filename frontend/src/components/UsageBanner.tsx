import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export const UsageBanner: React.FC = () => {
    const user = useAuthStore(state => state.user);
    const navigate = useNavigate();
    
    if (!user || user.plan === 'pro') return null;
    if (!user.usage) return null; // Hydrating
    
    // We display limits across specific tracking vectors
    // To not clutter the interface we can choose to explicitly highlight the closest one to running out
    
    const usageValues = Object.entries(user.usage).map(([action, detail]: [string, any]) => {
        if (detail.is_unlimited) return { action, percent: 0, used: 0, limit: '∞' };
        return {
            action,
            percent: (detail.used / detail.limit) * 100,
            used: detail.used,
            limit: detail.limit
        };
    });
    
    // Find the max utilized stat tracking percentage
    const maxUsage = usageValues.reduce((max, current) => current.percent > max.percent ? current : max, usageValues[0]);
    if (!maxUsage || maxUsage.limit === '∞') return null;
    
    const actionMap: Record<string, string> = {
        'document_uploaded': 'Documents',
        'chat_message': 'Chat Messages',
        'quiz_generated': 'Quizzes',
        'flashcard_review': 'Daily Flashcards'
    };
    
    let stateColor = "bg-slate-100 border-slate-200 text-slate-700";
    let highlightColor = "bg-slate-300";
    
    if (maxUsage.percent >= 95) {
        stateColor = "bg-red-50 border-red-200 text-red-800";
        highlightColor = "bg-red-500";
    } else if (maxUsage.percent >= 80) {
        stateColor = "bg-amber-50 border-amber-200 text-amber-800";
        highlightColor = "bg-amber-500";
    }
    
    return (
        <div className={`border rounded-lg p-3 ${stateColor} flex flex-col md:flex-row md:items-center justify-between text-sm shadow-sm`}>
            <div>
                 <span className="font-semibold block mb-1">
                     {maxUsage.used} / {maxUsage.limit} {actionMap[maxUsage.action]} Used
                 </span>
                 <div className="w-48 md:w-64 h-2 bg-white rounded-full overflow-hidden border border-slate-900/10 mb-2 md:mb-0">
                     <div className={`h-full transition-all ${highlightColor}`} style={{ width: `${Math.min(maxUsage.percent, 100)}%` }} />
                 </div>
            </div>
            
            <button 
                onClick={() => navigate('/pricing')}
                className="mt-2 md:mt-0 font-medium px-4 py-1.5 bg-slate-900 text-white rounded-md hover:bg-slate-800 transition"
            >
                Upgrade Plan
            </button>
        </div>
    );
};

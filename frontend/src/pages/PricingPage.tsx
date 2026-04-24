import React, { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
});

export const PricingPage: React.FC = () => {
    const { user, accessToken, checkAuth } = useAuthStore();
    const [isProcessing, setIsProcessing] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleUpgrade = async () => {
        setIsProcessing(true);
        try {
            await api.post(
                '/billing/upgrade', 
                {}, 
                { headers: { Authorization: `Bearer ${accessToken}` } }
            );
            // Refresh local auth context to sync usage state explicitly mapping the plan to "pro"
            await checkAuth();
            setSuccess(true);
        } catch (error) {
            console.error("Upgrade failed:", error);
            alert("Upgrade mockup failed. Please ensure backend is mapped.");
        } finally {
            setIsProcessing(false);
        }
    };

    if (success || user?.plan === 'pro') {
        return (
            <div className="min-h-[80vh] flex items-center justify-center p-6">
                <div className="bg-emerald-50 p-10 rounded-3xl border border-emerald-100 max-w-lg text-center shadow-lg">
                    <span className="text-6xl mb-6 block">🚀</span>
                    <h2 className="text-3xl font-bold text-slate-800 mb-4">You are on PRO!</h2>
                    <p className="text-slate-600 mb-8 leading-relaxed">You have unlocked unlimited access to Documents, AI Chat, Assessment Quizzes, and infinite Flashcard evaluations. Accelerate your learning exponentially.</p>
                    <a href="/" className="inline-block px-8 py-3 bg-slate-900 text-white rounded-xl font-medium hover:bg-slate-800 transition">Return to Dashboard</a>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
                <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-4">Unlock Your Full Potential</h1>
                <p className="text-xl text-slate-500 max-w-2xl mx-auto">Upgrade to bypass limits and gain unrestricted access to our powerful educational LLM models and spaced repetition integrations.</p>
            </div>

            <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                {/* Free Tier */}
                <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 flex flex-col relative overflow-hidden text-center opacity-80">
                    <h3 className="text-xl font-bold text-slate-800 mb-2">Free Plan</h3>
                    <div className="text-4xl font-black text-slate-900 mb-8">$0<span className="text-lg text-slate-500 font-medium tracking-normal">/mo</span></div>
                    
                    <ul className="space-y-4 mb-8 text-slate-600 text-left w-max mx-auto">
                        <li className="flex items-center"><span className="text-emerald-500 mr-3">✓</span> 3 Documents max</li>
                        <li className="flex items-center"><span className="text-emerald-500 mr-3">✓</span> 50 AI Messages / month</li>
                        <li className="flex items-center"><span className="text-emerald-500 mr-3">✓</span> 5 Quiz Generations / month</li>
                        <li className="flex items-center"><span className="text-emerald-500 mr-3">✓</span> 20 Flashcard Reviews / day</li>
                    </ul>
                    
                    <div className="mt-auto pt-6 border-t border-slate-100">
                        <span className="text-slate-400 font-medium">Your Current Plan</span>
                    </div>
                </div>

                {/* Pro Tier */}
                <div className="bg-slate-900 rounded-3xl border-2 border-emerald-500 shadow-2xl p-8 flex flex-col relative transform md:-translate-y-4 text-center">
                    <div className="absolute top-0 right-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wider">
                        Recommended
                    </div>
                    
                    <h3 className="text-xl font-bold text-white mb-2">Pro Plan</h3>
                    <div className="text-4xl font-black text-white mb-8">$9<span className="text-lg text-slate-400 font-medium tracking-normal">/mo</span></div>
                    
                    <ul className="space-y-4 mb-10 text-slate-300 text-left w-max mx-auto">
                        <li className="flex items-center"><span className="text-emerald-400 mr-3">✦</span> Unlimited Documents</li>
                        <li className="flex items-center"><span className="text-emerald-400 mr-3">✦</span> Unlimited AI Chat Context</li>
                        <li className="flex items-center"><span className="text-emerald-400 mr-3">✦</span> Unlimited Assessment Generation</li>
                        <li className="flex items-center"><span className="text-emerald-400 mr-3">✦</span> Unlimited SM-2 Spaced Repetitions</li>
                        <li className="flex items-center"><span className="text-emerald-400 mr-3">✦</span> Priority processing & memory speed</li>
                    </ul>
                    
                    <button 
                        onClick={handleUpgrade}
                        disabled={isProcessing}
                        className="mt-auto w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-white rounded-xl font-bold transition flex justify-center items-center gap-2"
                    >
                        {isProcessing ? 'Processing upgrade...' : 'Upgrade Now'}
                    </button>
                    <p className="text-xs text-slate-500 mt-4 italic">*Mock billing: Does not require real credit card for demonstration</p>
                </div>
            </div>
        </div>
    );
};

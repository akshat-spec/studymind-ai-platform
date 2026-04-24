import { useState, useRef, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import axios from 'axios';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export const useChat = (sessionId: string) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const token = useAuthStore(state => state.accessToken);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/chat/sessions/${sessionId}/messages?size=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(res.data);
    } catch (e: any) {
      console.error(e);
      setError("Failed to fetch chat history");
    }
  }, [sessionId, token]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Optimistic UI update
    const tempId = Date.now().toString();
    const userMsg: Message = {
      id: tempId,
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    // Prepare assistant msg structure for streaming
    const assistantTempId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, {
      id: assistantTempId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString()
    }]);

    try {
      // Create new abort controller for this request
      abortControllerRef.current = new AbortController();
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ content }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) throw new Error("Network response was not ok");
      if (!response.body) throw new Error("ReadableStream not yet supported in this browser.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const text = decoder.decode(value, { stream: true });
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') {
              setIsLoading(false);
              return;
            }
            if (!dataStr) continue;
            
            try {
              const data = JSON.parse(dataStr);
              if (data.chunk) {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantTempId ? { ...msg, content: msg.content + data.chunk } : msg
                ));
              }
            } catch (e) {
              console.error("Failed to parse SSE JSON", e);
            }
          }
        }
      }
    } catch (e: any) {
      if (e.name === 'AbortError') {
         console.log('Stream aborted');
      } else {
         console.error('Streaming error:', e);
         setError("Failed to send message");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    fetchHistory,
    stopGeneration
  };
};

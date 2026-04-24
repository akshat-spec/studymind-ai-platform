import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ role, content, isStreaming }) => {
  const isUser = role === 'user';
  
  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex max-w-[85%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center shadow-sm ${
          isUser ? 'bg-blue-600 ml-3' : 'bg-emerald-600 mr-3'
        }`}>
          <span className="text-white text-sm">{isUser ? '👤' : '🤖'}</span>
        </div>
        
        {/* Bubble */}
        <div className={`relative px-5 py-3.5 rounded-2xl shadow-sm text-[15px] leading-relaxed ${
          isUser 
            ? 'bg-blue-600 text-white rounded-tr-none' 
            : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none'
        }`}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{content}</div>
          ) : (
            <div className="prose prose-sm max-w-none prose-emerald prose-p:leading-relaxed">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  code({node, inline, className, children, ...props}: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={vscDarkPlus as any}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-lg shadow-sm"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="bg-slate-100 text-emerald-600 px-1.5 py-0.5 rounded-md text-sm" {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {content || (isStreaming ? '...' : '')}
              </ReactMarkdown>
              
              {/* Type indicator */}
              {isStreaming && (
                <span className="inline-block w-1.5 h-4 ml-1 bg-emerald-500 animate-pulse rounded-sm align-middle"></span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

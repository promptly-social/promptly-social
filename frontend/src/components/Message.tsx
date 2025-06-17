
import React from 'react';
import { Bot, User } from 'lucide-react';

interface MessageProps {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export const Message: React.FC<MessageProps> = ({ role, content, timestamp }) => {
  return (
    <div
      className={`flex gap-3 ${
        role === 'user' ? 'justify-end' : 'justify-start'
      }`}
    >
      <div
        className={`flex gap-2 max-w-[80%] ${
          role === 'user' ? 'flex-row-reverse' : 'flex-row'
        }`}
      >
        <div className="flex-shrink-0">
          {role === 'user' ? (
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
          ) : (
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
          )}
        </div>
        <div
          className={`px-3 py-2 rounded-lg ${
            role === 'user'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{content}</p>
          <span className="text-xs opacity-70 mt-1 block">
            {timestamp.toLocaleTimeString()}
          </span>
        </div>
      </div>
    </div>
  );
};

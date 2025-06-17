
import React, { useRef, useEffect } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Message } from './Message';
import { Bot, Loader2 } from 'lucide-react';

interface MessageData {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MessageListProps {
  messages: MessageData[];
  isLoading: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isLoading }) => {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <ScrollArea className="h-full p-6" ref={scrollAreaRef}>
      <div className="space-y-6 max-w-4xl mx-auto">
        {messages.map((message) => (
          <Message
            key={message.id}
            id={message.id}
            role={message.role}
            content={message.content}
            timestamp={message.timestamp}
          />
        ))}
        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="px-4 py-3 rounded-lg bg-gray-100">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
};
